"""
Authentication configuration using fastapi-users
"""
import os
import uuid
from typing import Optional, Any

from fastapi import Depends, Header, HTTPException, Request
from fastapi_users import BaseUserManager, FastAPIUsers
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase

from app.database import User, get_user_db, get_db, AsyncSessionLocal
from dotenv import load_dotenv
from datetime import datetime, timedelta
import hashlib
import secrets
from sqlalchemy import select
from app.database import RefreshToken
from fastapi import Response

load_dotenv()

# Configuration
SECRET = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
API_KEY = os.getenv("API_KEY")

# Access token lifetime (short)
ACCESS_TOKEN_LIFETIME = int(os.getenv("ACCESS_TOKEN_LIFETIME_SECONDS", 900))  # default 15 minutes
# Refresh token lifetime (long)
REFRESH_TOKEN_LIFETIME_DAYS = int(os.getenv("REFRESH_TOKEN_LIFETIME_DAYS", 30))


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=ACCESS_TOKEN_LIFETIME)


class UserManager(BaseUserManager[User, uuid.UUID]):
    """User manager for handling user operations"""
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")

    async def on_after_login(self, user: User, request: Optional[Request] = None, response: Optional[Response] = None):
        """Called after successful login via fastapi-users; create a refresh token and set cookie."""
        # Create a refresh token, store its hash in DB tied to user
        raw = secrets.token_urlsafe(64)
        token_hash = hashlib.sha256(raw.encode()).hexdigest()
        now = datetime.now()
        expires_at = now + timedelta(days=REFRESH_TOKEN_LIFETIME_DAYS)

        # store in DB using session maker
        async with AsyncSessionLocal() as session:
            rt = RefreshToken(user_id=user.id, token_hash=token_hash, issued_at=now, expires_at=expires_at, revoked=False)
            session.add(rt)
            await session.commit()

        # If response provided, set secure HTTPOnly cookie (works when called from auth router)
        if response is not None:
            response.set_cookie(
                key="refresh_token",
                value=raw,
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=REFRESH_TOKEN_LIFETIME_DAYS * 24 * 3600,
            )

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"Verification requested for user {user.id}. Verification token: {token}")

    def parse_id(self, value: Any) -> uuid.UUID:
        """Parse ID from string to UUID"""
        try:
            return uuid.UUID(value)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid UUID: {value}")


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


# Authentication backend
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# FastAPI Users instance
fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

# Dependencies for protected routes
current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)


def verify_api_key(x_api_key: str = Header(...)):
    """Verify API key from request headers (for backward compatibility)"""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
