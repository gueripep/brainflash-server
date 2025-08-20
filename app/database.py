"""
Database configuration and connection setup
"""
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Text, Boolean, Integer, JSON, ForeignKey, Date
from datetime import datetime
from typing import Optional, List
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
    # One user can own many flashcard decks
    decks: Mapped[List["FlashcardDeck"]] = relationship("FlashcardDeck", back_populates="owner", cascade="all, delete-orphan")


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
    


class DailyProgress(Base):
    """Store daily progress like: {"date":"Sun Aug 17 2025","newCardsStudied":0}"""
    __tablename__ = "daily_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    date: Mapped[Date] = mapped_column(Date, nullable=False)
    new_cards_studied: Mapped[int] = mapped_column(Integer, default=0)


class FlashcardDeck(Base):
    """Store flashcard deck metadata"""
    __tablename__ = "flashcard_decks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    # Optional owner reference to users table
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    owner: Mapped["User"] = relationship("User", back_populates="decks")
    # Relationship to Flashcard: one deck -> many flashcards
    cards: Mapped[List["Flashcard"]] = relationship(
        "Flashcard",
        back_populates="deck",
        cascade="all, delete-orphan",
    )


class Flashcard(Base):
    """Store individual flashcards; nested fields (discussion, final_card, fsrs) are stored as JSON."""
    __tablename__ = "flashcards"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    created_at: Mapped[Optional[DateTime]] = mapped_column(DateTime, default=datetime.now, nullable=True)
    # A flashcard must belong to a deck; require deck_id on creation
    deck_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("flashcard_decks.id"), nullable=False)
    # Relationship back to the deck that contains this card
    deck: Mapped["FlashcardDeck"] = relationship("FlashcardDeck", back_populates="cards")
    # One-to-one related objects
    discussion: Mapped["FlashcardDiscussion"] = relationship(
        "FlashcardDiscussion", back_populates="flashcard", uselist=False, cascade="all, delete-orphan"
    )
    final_card: Mapped["FlashcardFinalCard"] = relationship(
        "FlashcardFinalCard", back_populates="flashcard", uselist=False, cascade="all, delete-orphan"
    )
    fsrs: Mapped["FlashcardFSRS"] = relationship(
        "FlashcardFSRS", back_populates="flashcard", uselist=False, cascade="all, delete-orphan"
    )
    stage: Mapped[int] = mapped_column(Integer, default=0)



class FlashcardDiscussion(Base):
    """Separate table for the 'discussion' object attached to a flashcard.

    Example structure:
    {
      "ssmlText": "...",
      "text": "...",
      "audio": { "filename": "...", "timingFilename": "..." }
    }
    """
    __tablename__ = "flashcard_discussions"

    flashcard_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("flashcards.id", ondelete="CASCADE"), primary_key=True)
    ssml_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Link to shared audio file instead of storing JSON with filename/timing
    audio_id: Mapped[int] = mapped_column(Integer, ForeignKey("audio_files.id"), nullable=True)
    audio: Mapped["AudioFile"] = relationship("AudioFile", foreign_keys=[audio_id], cascade="all, delete-orphan", single_parent=True, passive_deletes=True)

    flashcard: Mapped["Flashcard"] = relationship("Flashcard", back_populates="discussion")


class FlashcardFinalCard(Base):
    """Separate table for the 'finalCard' object attached to a flashcard."""
    __tablename__ = "flashcard_final_cards"

    flashcard_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("flashcards.id", ondelete="CASCADE"), primary_key=True)
    front: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    back: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Replace JSON audio blobs with FKs to shared AudioFile table
    question_audio_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("audio_files.id"), nullable=True)
    answer_audio_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("audio_files.id"), nullable=True)

    question_audio: Mapped[Optional["AudioFile"]] = relationship("AudioFile", foreign_keys=[question_audio_id], cascade="all, delete-orphan", single_parent=True, passive_deletes=True)
    answer_audio: Mapped[Optional["AudioFile"]] = relationship("AudioFile", foreign_keys=[answer_audio_id], cascade="all, delete-orphan", single_parent=True, passive_deletes=True)

    flashcard: Mapped["Flashcard"] = relationship("Flashcard", back_populates="final_card")


class FlashcardFSRS(Base):
    """Separate table for FSRS (spaced repetition) metadata attached to a flashcard."""
    __tablename__ = "flashcard_fsrs"

    flashcard_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("flashcards.id", ondelete="CASCADE"), primary_key=True)
    due: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    stability: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    difficulty: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    elapsed_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    scheduled_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    lapses: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    state: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    learning_steps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationship back to Flashcard (one-to-one) to match Flashcard.fsrs back_populates
    flashcard: Mapped["Flashcard"] = relationship("Flashcard", back_populates="fsrs")


class StudySession(Base):
    """Store study sessions keyed by id; reviews stored as JSON list/object."""
    __tablename__ = "study_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, index=True)
    deck_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("flashcard_decks.id"), nullable=True)
    start_time: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)
    cards_studied: Mapped[int] = mapped_column(Integer, default=0)
    question_audio_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("audio_files.id"), nullable=True)
    answer_audio_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("audio_files.id"), nullable=True)


    question_audio: Mapped[Optional["AudioFile"]] = relationship("AudioFile", foreign_keys=[question_audio_id])
    answer_audio: Mapped[Optional["AudioFile"]] = relationship("AudioFile", foreign_keys=[answer_audio_id])

class AudioFile(Base):
    """Table to store audio filenames and their timing file names. Shared by multiple models."""
    __tablename__ = "audio_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    timing_filename: Mapped[str] = mapped_column(String(255), nullable=True)


class RefreshToken(Base):
    """Store refresh tokens per user (store only a hash of the token)."""
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)


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
