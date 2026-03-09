"""
Authentication API routes.

Endpoints:
  POST /api/auth/register          — create account with email + password
  POST /api/auth/login             — login, get access token + httpOnly refresh cookie
  POST /api/auth/logout            — clear refresh cookie
  POST /api/auth/refresh           — use refresh cookie to issue a new access token
  GET  /api/auth/me                — return current user profile (requires access token)
  GET  /api/auth/google            — redirect to Google's OAuth consent page
  GET  /api/auth/google/callback   — Google redirects here; issues tokens and redirects to frontend

Security notes:
- Refresh tokens live in httpOnly, Secure, SameSite=Lax cookies (inaccessible to JS).
- Access tokens are returned in the JSON body and kept in memory by the frontend.
- Rate limiting on sensitive endpoints is handled by slowapi (configured in main.py).
"""
import logging
import re
from typing import Optional
from urllib.parse import urlencode

import httpx
from better_profanity import profanity as _profanity
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import models
from app.auth_service import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    create_or_update_google_user,
    create_user_with_password,
    get_current_user,
    get_current_user_from_refresh_cookie,
    validate_password_strength,
)
from app.config import settings
from app.database import get_db
from app.limiter import limiter

# ---------------------------------------------------------------------------
# Profanity filter — initialised once at import time.
# Load the default word list and extend it with common leet-speak / short
# offensive terms that the stock list sometimes misses.
# ---------------------------------------------------------------------------
_EXTRA_BANNED = [
    "slut", "whore", "cunt", "fag", "nigga", "nigger", "chink", "spic",
    "kike", "tranny", "retard", "rapist", "pedo", "paedo", "molest",
    "adolf", "hitler", "nazi", "kkk", "rape", "kill yourself", "kys",
    "fcker", "fucker", "fck",
]

# Words to block even when embedded inside a longer string
# (e.g. "Hitler2024", "n_zi", "iLoveAss"). Checked against the
# separator-stripped, lower-cased nickname via a simple `in` test.
_SUBSTRING_BANNED = [
    "hitler", "adolf", "nazi", "nzi", "nigger", "nigga", "chink", "spic",
    "kike", "rapist", "paedo", "paedoph", "pedoph", "slut", "whore",
    "cunt", "fck", "fucker",
]

_profanity.load_censor_words(whitelist_words=[])
_profanity.add_censor_words(_EXTRA_BANNED)


def _spaced_camel(s: str) -> str:
    """Insert spaces before uppercase letters so 'iLoveAss' → 'i Love Ass'."""
    return re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', s)

logger = logging.getLogger(__name__)

auth_router = APIRouter(prefix="/api/auth", tags=["auth"])

# ---------------------------------------------------------------------------
# Cookie helpers
# ---------------------------------------------------------------------------
_COOKIE_NAME = "refresh_token"
_COOKIE_MAX_AGE = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600  # seconds


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=_COOKIE_NAME,
        value=token,
        httponly=True,           # Not readable by JavaScript
        secure=not settings.DEBUG,   # False in dev (HTTP), True in prod (HTTPS)
        samesite="lax",          # Protects against CSRF while allowing top-level redirects
        max_age=_COOKIE_MAX_AGE,
        path="/api/auth",        # Scope cookie to auth endpoints only
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=_COOKIE_NAME, path="/api/auth")


# ---------------------------------------------------------------------------
# Email + Password endpoints
# ---------------------------------------------------------------------------

@auth_router.post("/register", response_model=models.TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(request: Request, body: models.UserRegister, response: Response, db: Session = Depends(get_db)):
    """
    Create a new account with email and password.
    Returns an access token and sets the refresh cookie.
    Rate limited to 5 registrations per minute per IP.
    """
    validate_password_strength(body.password)
    user = create_user_with_password(db, body.email, body.password)
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    _set_refresh_cookie(response, refresh_token)
    return models.TokenResponse(access_token=access_token, user=user)


@auth_router.post("/login", response_model=models.TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, body: models.UserLogin, response: Response, db: Session = Depends(get_db)):
    """
    Login with email and password.
    Returns an access token and sets the refresh cookie.
    Rate limited to 10 attempts per minute per IP.
    """
    user = authenticate_user(db, body.email, body.password)
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    _set_refresh_cookie(response, refresh_token)
    return models.TokenResponse(access_token=access_token, user=user)


@auth_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    """Clear the refresh cookie to log the user out."""
    _clear_refresh_cookie(response)


@auth_router.post("/refresh", response_model=models.TokenResponse)
@limiter.limit("30/minute")
def refresh(request: Request, response: Response, user: models.User = Depends(get_current_user_from_refresh_cookie), db: Session = Depends(get_db)):
    """
    Issue a new access token using the httpOnly refresh cookie.
    Also rotates the refresh token (refresh token rotation).
    Rate limited to 30 per minute per IP.
    """
    new_access_token = create_access_token(user.id)
    new_refresh_token = create_refresh_token(user.id)
    _set_refresh_cookie(response, new_refresh_token)
    return models.TokenResponse(access_token=new_access_token, user=user)


@auth_router.get("/me", response_model=models.UserSchema)
def get_me(current_user: models.User = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return current_user


class UpdateProfileRequest(BaseModel):
    username: Optional[str] = None          # None = don't change; "" = clear nickname


@auth_router.patch("/me", response_model=models.UserSchema)
def update_me(
    body: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Update the current user's profile (nickname). Requires authentication."""
    if body.username is not None:
        nickname = body.username.strip()

        if nickname == "":
            # Allow clearing the nickname
            current_user.username = None
        else:
            if len(nickname) < 2:
                raise HTTPException(status_code=422, detail="Nickname must be at least 2 characters.")
            if len(nickname) > 30:
                raise HTTPException(status_code=422, detail="Nickname must be 30 characters or fewer.")
            if not re.match(r'^[\w\-. ]+$', nickname):
                raise HTTPException(
                    status_code=422,
                    detail="Nickname may only contain letters, numbers, spaces, hyphens, underscores and dots.",
                )
            # Reject nicknames that contain profanity / hate speech.
            # Strategy (three passes):
            # 1. better-profanity on the raw nickname (handles leet-speak like "sh!t", "@ss").
            # 2. better-profanity on the camelCase-expanded version ("iLoveAss" → "i Love Ass").
            # 3. Substring match on the separator-stripped, lower-cased version to catch
            #    hate terms embedded in longer strings ("Hitler2024", "h.i.t.l.e.r", "n_zi").
            _camel_spaced = _spaced_camel(nickname)
            _normalised = re.sub(r'[\-_.]', '', nickname).lower()
            _is_profane = (
                _profanity.contains_profanity(nickname)
                or _profanity.contains_profanity(_camel_spaced)
                or any(w in _normalised for w in _SUBSTRING_BANNED)
            )
            if _is_profane:
                raise HTTPException(
                    status_code=422,
                    detail="Nickname contains inappropriate language.",
                )
            # Check uniqueness (case-insensitive)
            existing = db.query(models.User).filter(
                models.User.username.ilike(nickname),
                models.User.id != current_user.id,
            ).first()
            if existing:
                raise HTTPException(status_code=409, detail="That nickname is already taken.")
            current_user.username = nickname

        db.commit()
        db.refresh(current_user)

    return current_user


# ---------------------------------------------------------------------------
# Google OAuth 2.0 (Authorization Code Flow — server-side)
# ---------------------------------------------------------------------------

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


@auth_router.get("/google")
def google_login():
    """
    Redirect the user to Google's OAuth consent page.
    The client_secret never leaves the backend.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google login is not configured on this server.",
        )
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
    }
    return RedirectResponse(url=f"{_GOOGLE_AUTH_URL}?{urlencode(params)}")


@auth_router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """
    Google redirects here with an authorization code.
    We exchange the code for tokens, fetch user info, upsert the user,
    and redirect to the frontend with the access token in the URL fragment
    (so it lands in JS memory, never in history or server logs).
    The refresh token is set as an httpOnly cookie on the redirect response.
    """
    code = request.query_params.get("code")
    error = request.query_params.get("error")

    frontend_origin = settings.FRONTEND_URL

    if error or not code:
        logger.warning(f"Google OAuth error: {error}")
        return RedirectResponse(url=f"{frontend_origin}/login?error=google_denied")

    try:
        async with httpx.AsyncClient() as client:
            # Exchange code → tokens
            token_resp = await client.post(
                _GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )
            token_resp.raise_for_status()
            google_tokens = token_resp.json()

            # Fetch user info
            userinfo_resp = await client.get(
                _GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {google_tokens['access_token']}"},
            )
            userinfo_resp.raise_for_status()
            userinfo = userinfo_resp.json()

        google_id = userinfo.get("sub")
        email = userinfo.get("email")
        name = userinfo.get("name")

        if not google_id or not email:
            return RedirectResponse(url=f"{frontend_origin}/login?error=google_no_email")

        user = create_or_update_google_user(db, google_id, email, name)
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        # Redirect to frontend — access token in fragment (#) so it's never sent to server
        redirect = RedirectResponse(
            url=f"{frontend_origin}/auth/callback#access_token={access_token}",
            status_code=status.HTTP_302_FOUND,
        )
        _set_refresh_cookie(redirect, refresh_token)
        return redirect

    except httpx.HTTPStatusError as e:
        logger.error(f"Google token exchange failed: {e}")
        return RedirectResponse(url=f"{frontend_origin}/login?error=google_failed")
    except Exception as e:
        logger.error(f"Unexpected error in Google callback: {e}", exc_info=True)
        return RedirectResponse(url=f"{frontend_origin}/login?error=server_error")
