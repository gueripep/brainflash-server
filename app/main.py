"""
BrainFlash TTS Server
A text-to-speech server using Google Cloud TTS and Gemini AI
"""
from typing import Dict, Any

from config import create_app
from routes.tts import router as tts_router
from routes.gemini import router as gemini_router

# Create the FastAPI application
app = create_app()

# Include routers
app.include_router(tts_router)
app.include_router(gemini_router)


@app.get("/")
def read_root() -> Dict[str, Any]:
    """
    Root endpoint - returns basic information about the API
    """
    return {
        "message": "Welcome to BrainFlash TTS Server",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "gcp_test": "/gcp/test",
            "synthesize": "/tts/synthesize",
            "speak": "/tts/speak/{text}",
            "download": "/tts/download/{filename}",
            "timing": "/tts/timing/{filename}",
            "list_files": "/tts/list"
        }
    }