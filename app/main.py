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
from app.routes.flashcards import router as flashcards_router
from app.routes.decks import router as decks_router
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


@app.get("/")
def get_root() -> Dict[str, Any]:
    """
    Root endpoint - returns basic information about the API
    """
    return {
        "message": "Welcome to BrainFlash TTS Server",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "auth": {
                "register": "/auth/register",
                "login": "/auth/jwt/login",
                "logout": "/auth/jwt/logout",
                "users": "/users/me",
                "reset_password": "/auth/forgot-password"
            },
            "tts": {
                "gcp_test": "/gcp/test",
                "synthesize": "/tts/synthesize",
                "speak": "/tts/speak/{text}",
                "download": "/tts/download/{filename}",
                "timing": "/tts/timing/{filename}",
                "list_files": "/tts/list",
                "history": "/tts/history"
            },
            "gemini": {
                "chat": "/gemini/chat",
                "history": "/gemini/history"
            }
        }
    }