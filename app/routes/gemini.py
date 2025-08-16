"""
Gemini AI route handlers
"""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends

from app.models import GeminiRequest
from app.gemini_config import GeminiConfig
from app.auth import current_active_user

router = APIRouter(prefix="/gemini", tags=["Gemini AI"])


@router.post("/generate/")
def generate_content(
    request: GeminiRequest,
    user=Depends(current_active_user)
) -> Dict[str, Any]:
    """
    Generate content using the Gemini model
    """
    try:
        gemini_config = GeminiConfig()
        response = gemini_config.generate_content(request.prompt)
        return {"status": "success", "content": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content generation failed: {str(e)}")
