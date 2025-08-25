from pydantic import BaseModel, Field, model_validator
from typing import Optional
from datetime import datetime, date
from uuid import UUID

from app.database import FlashcardDeck


class DeckCreate(BaseModel):
    name: str

class DeckUpdate(BaseModel):
    name: Optional[str] = None


class DeckRead(BaseModel):
    id: UUID
    name: str
    card_count: int
    created_at: datetime

    class Config:
        from_attributes = True