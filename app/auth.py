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

from app.database import User, get_user_db, get_db
from dotenv import load_dotenv

load_dotenv()

# Configuration
SECRET = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
API_KEY = os.getenv("API_KEY")


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)


class UserManager(BaseUserManager[User, uuid.UUID]):
    """User manager for handling user operations"""
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")

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
