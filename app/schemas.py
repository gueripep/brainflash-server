"""
Pydantic schemas for API requests and responses
"""
import uuid
from typing import Optional
from fastapi_users import schemas


class UserRead(schemas.BaseUser[uuid.UUID]):
    """Schema for reading user data"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserCreate(schemas.BaseUserCreate):
    """Schema for creating a new user"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserUpdate(schemas.BaseUserUpdate):
    """Schema for updating user data"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
