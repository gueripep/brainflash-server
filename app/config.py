"""
Application configuration and factory
"""
import os
from fastapi import FastAPI, Depends
from dotenv import load_dotenv

from auth import verify_api_key

# Load environment variables
load_dotenv()
env = os.getenv("ENV")

if not env:
    raise RuntimeError("ENV not set!")


def create_app(lifespan=None) -> FastAPI:
    """
    Application factory function
    """
    if env == "prod":
        # Production configuration - disable docs for security
        app = FastAPI(
            title="BrainFlash TTS Server",
            description="A text-to-speech server using Google Cloud TTS",
            version="1.0.0",
            dependencies=[Depends(verify_api_key)],
            docs_url=None,
            openapi_url=None,
            redoc_url=None,
            lifespan=lifespan
        )
    elif env == "dev":
        # Development configuration - enable docs
        app = FastAPI(
            title="BrainFlash TTS Server",
            description="A text-to-speech server using Google Cloud TTS",
            version="1.0.0",
            dependencies=[Depends(verify_api_key)],
            lifespan=lifespan
        )
    else:
        raise ValueError("Invalid ENV value")

    return app
