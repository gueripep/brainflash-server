from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class GeminiRequest(BaseModel):
    prompt: str


class GeminiResponse(BaseModel):
    id: int
    prompt: str
    response: str
    processing_time_ms: Optional[int] = None
    model_used: Optional[str] = None
    created_at: datetime