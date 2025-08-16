"""
Application configuration and factory
"""
import os
from fastapi import FastAPI, Depends
from dotenv import load_dotenv

from app.auth import verify_api_key
from app.middleware.rate_limiter import RateLimitMiddleware

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
            description="A text-to-speech server using Google Cloud TTS and Gemini AI with Authentication",
            version="1.0.0",
            docs_url=None,
            openapi_url=None,
            redoc_url=None,
            lifespan=lifespan
        )
    elif env == "dev":
        # Development configuration - enable docs
        app = FastAPI(
            title="BrainFlash TTS Server",
            description="A text-to-speech server using Google Cloud TTS and Gemini AI with Authentication",
            version="1.0.0",
            lifespan=lifespan
        )
    else:
        raise ValueError("Invalid ENV value")

    # Configure rate limiting from environment variables (defaults provided)
    try:
        max_requests = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "60"))
        window_seconds = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
    except ValueError:
        max_requests = 60
        window_seconds = 60

    # Paths to exempt from rate limiting (comma-separated)
    exempt = os.getenv("RATE_LIMIT_EXEMPT_PATHS", "/docs,/openapi.json").split(",")

    # Attach the middleware
    app.add_middleware(
        RateLimitMiddleware,
        max_requests=max_requests,
        window_seconds=window_seconds,
        exempt_paths=exempt,
    )

    return app
