"""
Pydantic models for request validation
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TTSRequest(BaseModel):
    text: str
    language_code: str = "en-US"
    voice_name: str = "en-US-Wavenet-D"
    audio_encoding: str = "MP3"
    enable_time_pointing: bool = True  # Enable word-level timing
    is_ssml: bool = False  # Whether the input text is SSML


class TTSResponse(BaseModel):
    id: int
    audio_file_name: str
    audio_file_url: Optional[str] = None
    timing_file_name: Optional[str] = None
    timing_file_url: Optional[str] = None
    processing_time_ms: Optional[int] = None
    created_at: datetime


class GeminiRequest(BaseModel):
    prompt: str


class GeminiResponse(BaseModel):
    id: int
    prompt: str
    response: str
    processing_time_ms: Optional[int] = None
    model_used: Optional[str] = None
    created_at: datetime
