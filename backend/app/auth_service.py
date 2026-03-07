"""
Authentication service: password hashing, JWT creation/validation, user lookup.

Security design:
- Passwords are hashed with bcrypt (cost factor 12), pre-hashed with SHA-256
  so that passwords longer than 72 bytes are handled correctly (bcrypt's limit).
- Access tokens are short-lived JWTs (default 15 min) sent in the Authorization header.
- Refresh tokens are long-lived JWTs (default 7 days) stored in httpOnly, Secure, SameSite=Lax
  cookies so JavaScript cannot read them (mitigates XSS).
- Tokens include a 'type' claim to prevent refresh tokens being used as access tokens.
"""
import hashlib
import hmac
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt as pyjwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app import models

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------
# We pre-hash the password with SHA-256 (hex digest = 64 ASCII bytes) before
# passing it to bcrypt. This means:
#   1. Passwords of any length work — bcrypt only ever sees 64 bytes.
#   2. We avoid the silent 72-byte truncation that raw bcrypt performs.
# Cost factor 12 is the OWASP-recommended minimum for bcrypt (2025).

_BCRYPT_ROUNDS = 12


def _prehash(plain: str) -> bytes:
    """SHA-256 hex-encode the password so bcrypt always receives ≤64 bytes."""
    return hashlib.sha256(plain.encode("utf-8")).hexdigest().encode("ascii")


def hash_password(plain: str) -> str:
    hashed = bcrypt.hashpw(_prehash(plain), bcrypt.gensalt(rounds=_BCRYPT_ROUNDS))
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(_prehash(plain), hashed.encode("utf-8"))

# ---------------------------------------------------------------------------
# Password strength validation
# ---------------------------------------------------------------------------
import re

_PASSWORD_RULES = [
    (lambda p: len(p) >= 12,              "at least 12 characters"),
    (lambda p: re.search(r"[A-Z]", p),   "at least one uppercase letter"),
    (lambda p: re.search(r"[a-z]", p),   "at least one lowercase letter"),
    (lambda p: re.search(r"\d", p),      "at least one number"),
    (lambda p: re.search(r"[^A-Za-z0-9]", p), "at least one special character"),
]

def validate_password_strength(password: str) -> None:
    """
    Raise HTTPException 422 if the password does not satisfy all strength rules.
    Called during registration before hashing.
    """
    failed = [msg for check, msg in _PASSWORD_RULES if not check(password)]
    if failed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Password must contain: {', '.join(failed)}.",
        )
# ---------------------------------------------------------------------------
_bearer_scheme = HTTPBearer(auto_error=False)

def _create_token(data: dict, expires_delta: timedelta, token_type: str) -> str:
    payload = data.copy()
    now = datetime.now(timezone.utc)
    payload.update({
        "iat": now,
        "exp": now + expires_delta,
        "type": token_type,
    })
    return pyjwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def create_access_token(user_id: int) -> str:
    return _create_token(
        {"sub": str(user_id)},
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "access",
    )

def create_refresh_token(user_id: int) -> str:
    return _create_token(
        {"sub": str(user_id)},
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        "refresh",
    )

def _decode_token(token: str, expected_type: str) -> int:
    """Decode and validate a JWT. Returns the user_id (sub claim)."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = pyjwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != expected_type:
            raise credentials_exception
        sub: str = payload.get("sub")
        if sub is None:
            raise credentials_exception
        return int(sub)
    except pyjwt.PyJWTError:
        raise credentials_exception

# ---------------------------------------------------------------------------
# FastAPI dependencies
# ---------------------------------------------------------------------------

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    """
    Dependency: extracts the Bearer token from the Authorization header,
    validates it, and returns the User ORM object.
    Raises 401 if the token is missing or invalid.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = _decode_token(credentials.credentials, "access")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user

def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> Optional[models.User]:
    """
    Like get_current_user but returns None instead of raising 401
    when no token is present. Used for optional-auth endpoints (e.g. game/words).
    """
    if credentials is None:
        return None
    try:
        user_id = _decode_token(credentials.credentials, "access")
    except HTTPException:
        return None
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None or not user.is_active:
        return None
    return user

def get_admin_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """
    Dependency: like get_current_user but also requires is_admin=True.
    Raises 403 Forbidden for non-admin authenticated users.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return current_user

def get_current_user_from_refresh_cookie(request: Request, db: Session = Depends(get_db)) -> models.User:
    """
    Dependency: reads the refresh token from the httpOnly cookie,
    validates it, and returns the User.
    """
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token",
        )
    user_id = _decode_token(token, "refresh")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user

# ---------------------------------------------------------------------------
# User CRUD helpers
# ---------------------------------------------------------------------------

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email.lower()).first()

def get_user_by_google_id(db: Session, google_id: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.google_id == google_id).first()

def create_user_with_password(db: Session, email: str, password: str) -> models.User:
    """Create a new local (email+password) user."""
    if get_user_by_email(db, email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )
    user = models.User(
        email=email.lower(),
        hashed_password=hash_password(password),
        is_active=True,
        is_verified=False,  # Set True once email verification is added
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_or_update_google_user(db: Session, google_id: str, email: str, name: Optional[str] = None) -> models.User:
    """
    Upsert a user coming from Google OAuth.
    If the email already exists (local account), link the google_id to it.
    """
    # Check by google_id first
    user = get_user_by_google_id(db, google_id)
    if user:
        return user

    # Check if a local account with the same email exists — link them
    user = get_user_by_email(db, email)
    if user:
        user.google_id = google_id
        user.is_verified = True  # Google verifies the email
        db.commit()
        db.refresh(user)
        return user

    # Brand new user via Google
    user = models.User(
        email=email.lower(),
        google_id=google_id,
        username=name,
        is_active=True,
        is_verified=True,  # Google has already verified the email
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def authenticate_user(db: Session, email: str, password: str) -> models.User:
    """
    Verify email + password. Raises 401 on any failure.
    Uses a constant-time comparison via passlib to resist timing attacks.
    """
    user = get_user_by_email(db, email)
    # Always run verify_password even if user is None to prevent timing attacks.
    # This dummy hash is a real bcrypt digest so the full bcrypt work is done
    # before we discard the result, giving a consistent response time.
    _DUMMY_HASH = "$2b$12$eImiTXuWVxfM37uY4JANjQ.PD2UFGHdOdUcv1SZjZZyq/P9TkaBVy"
    password_ok = verify_password(password, user.hashed_password if user and user.hashed_password else _DUMMY_HASH)

    if not user or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled.")
    return user
