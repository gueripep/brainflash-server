"""
Pydantic models for request validation
"""
from pydantic import BaseModel


class TTSRequest(BaseModel):
    text: str
    language_code: str = "en-US"
    voice_name: str = "en-US-Wavenet-D"
    audio_encoding: str = "MP3"
    enable_time_pointing: bool = True  # Enable word-level timing
    is_ssml: bool = False  # Whether the input text is SSML


class GeminiRequest(BaseModel):
    prompt: str
