"""
Gemini AI route handlers
"""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException

from models import GeminiRequest
from gemini_config import GeminiConfig

router = APIRouter(prefix="/gemini", tags=["Gemini AI"])


@router.post("/generate/")
def generate_content(request: GeminiRequest) -> Dict[str, Any]:
    """
    Generate content using the Gemini model
    """
    try:
        gemini_config = GeminiConfig()
        response = gemini_config.generate_content(request.prompt)
        return {"status": "success", "content": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content generation failed: {str(e)}")
