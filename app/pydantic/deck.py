from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from uuid import UUID

# Deck schemas
class DeckBase(BaseModel):
    name: str


class DeckCreate(DeckBase):
    pass


class DeckUpdate(BaseModel):
    name: Optional[str] = None


class DeckRead(DeckBase):
    id: UUID
    card_count: Optional[int] = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
