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
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
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
        secure=True,             # Only sent over HTTPS (set to False in dev if needed)
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
def register(body: models.UserRegister, response: Response, db: Session = Depends(get_db)):
    """
    Create a new account with email and password.
    Returns an access token and sets the refresh cookie.
    """
    validate_password_strength(body.password)
    user = create_user_with_password(db, body.email, body.password)
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    _set_refresh_cookie(response, refresh_token)
    return models.TokenResponse(access_token=access_token, user=user)


@auth_router.post("/login", response_model=models.TokenResponse)
def login(body: models.UserLogin, response: Response, db: Session = Depends(get_db)):
    """
    Login with email and password.
    Returns an access token and sets the refresh cookie.
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
def refresh(response: Response, user: models.User = Depends(get_current_user_from_refresh_cookie), db: Session = Depends(get_db)):
    """
    Issue a new access token using the httpOnly refresh cookie.
    Also rotates the refresh token (refresh token rotation).
    """
    new_access_token = create_access_token(user.id)
    new_refresh_token = create_refresh_token(user.id)
    _set_refresh_cookie(response, new_refresh_token)
    return models.TokenResponse(access_token=new_access_token, user=user)


@auth_router.get("/me", response_model=models.UserSchema)
def get_me(current_user: models.User = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
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

    frontend_origin = settings.ALLOWED_ORIGINS[0]  # e.g. http://localhost:5173

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
