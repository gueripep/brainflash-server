"""
Authentication routes
"""
from fastapi import APIRouter
from fastapi_users import FastAPIUsers

from app.auth import auth_backend, fastapi_users
from app.schemas import UserRead, UserCreate, UserUpdate

router = APIRouter()

# Include authentication routes
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt", 
    tags=["auth"]
)

# Include registration routes
router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

# Include user management routes
router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

# Include password reset routes
router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)

# Include email verification routes
router.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)
