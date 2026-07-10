"""Controller for the /auth endpoints.

Thin layer — delegates to services/auth.py and returns Pydantic models.
"""

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from models.api_models import LoginRequest, RegisterRequest, TokenResponse
from models.db_models import User
from services.auth import (
    TOKEN_EXPIRE_DAYS,
    create_access_token,
    hash_password,
    verify_password,
)
from services.db_session import get_db


def register(request: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Create a new user account and return a JWT access token.

    Returns 409 if the username is already taken.
    """
    existing = db.query(User).filter(User.username == request.username).first()
    if existing is not None:
        raise HTTPException(status_code=409, detail="Username already taken.")

    user = User(username=request.username, password_hash=hash_password(request.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.username)
    expires_in = TOKEN_EXPIRE_DAYS * 24 * 3600
    return TokenResponse(access_token=token, expires_in=expires_in)


def login(request: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Validate credentials and return a JWT access token valid for 30 days."""
    user = db.query(User).filter(User.username == request.username).first()
    if user is None:
        # Hash a dummy value to avoid timing differences.
        verify_password(request.password, hash_password("dummy"))
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    if not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    token = create_access_token(user.username)
    expires_in = TOKEN_EXPIRE_DAYS * 24 * 3600

    return TokenResponse(access_token=token, expires_in=expires_in)
