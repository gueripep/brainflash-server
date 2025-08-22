"""
BrainFlash TTS Server
A text-to-speech server using Google Cloud TTS and Gemini AI
"""
from typing import Dict, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.config import create_app
from app.routes.tts import router as tts_router
from app.routes.gemini import router as gemini_router
from app.routes.auth import router as auth_router
from app.routes.decks import router as decks_router
from app.routes.flashcards.flashcards import router as flashcards_router
from app.routes.flashcards.flaschards_final_card import router as final_card_router
from app.routes.flashcards.flashcards_fsrs import router as fsrs_router
from app.database import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


# Create the FastAPI application with lifespan
app = create_app(lifespan=lifespan)

# Include routers
app.include_router(auth_router)
app.include_router(tts_router)
app.include_router(gemini_router)
app.include_router(flashcards_router)
app.include_router(decks_router)
app.include_router(fsrs_router)
app.include_router(final_card_router)