"""
Database configuration and connection setup
"""
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime, Text, Boolean, Integer
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTable, SQLAlchemyUserDatabase
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column
from fastapi import Depends


# Load environment variables
load_dotenv()
CET = timezone(timedelta(hours=1))  # Central European Time
now_cet = datetime.now(CET)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://brainflash:brainflash_password@db:5432/brainflash"
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("ENV") == "dev",  # Enable SQL logging in development
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Create async session maker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


class User(SQLAlchemyBaseUserTable[uuid.UUID], Base):
    """User model for authentication"""
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class TTSRecord(Base):
    """Model for storing TTS requests and results"""
    __tablename__ = "tts_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), default="en-US")
    voice_name: Mapped[str] = mapped_column(String(50), default="en-US-Wavenet-D")
    audio_encoding: Mapped[str] = mapped_column(String(10), default="MP3")
    enable_time_pointing: Mapped[bool] = mapped_column(Boolean, default=True)
    is_ssml: Mapped[bool] = mapped_column(Boolean, default=False)
    audio_file_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    timing_file_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class GeminiRecord(Base):
    """Model for storing Gemini AI requests and responses"""
    __tablename__ = "gemini_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    model_used: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    



async def get_db():
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connection"""
    await engine.dispose()


async def get_user_db(session: AsyncSession = Depends(get_db)):
    """Get user database adapter"""
    yield SQLAlchemyUserDatabase(session, User)
