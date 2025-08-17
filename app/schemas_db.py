from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from uuid import UUID


# Nested objects
class DiscussionSchema(BaseModel):
    ssml_text: Optional[str] = None
    text: Optional[str] = None
    audio: Optional["AudioSchema"] = None


class FinalCardSchema(BaseModel):
    front: Optional[str] = None
    back: Optional[str] = None
    question_audio: Optional["AudioSchema"] = None
    answer_audio: Optional["AudioSchema"] = None


class FSRSSchema(BaseModel):
    due: Optional[datetime] = None
    stability: Optional[int] = None
    difficulty: Optional[int] = None
    elapsed_days: Optional[int] = None
    scheduled_days: Optional[int] = None
    reps: Optional[int] = None
    lapses: Optional[int] = None
    state: Optional[int] = None
    learning_steps: Optional[int] = None
    audio_id: Optional[int] = None


class FlashcardBase(BaseModel):
    id: str
    deck_id: Optional[str] = None
    stage: Optional[int] = 0


class FlashcardCreate(FlashcardBase):
    discussion: Optional[DiscussionSchema] = None
    final_card: Optional[FinalCardSchema] = None
    fsrs: Optional[FSRSSchema] = None

class FlashcardUpdate(BaseModel):
    deck_id: Optional[UUID] = None
    stage: Optional[int] = None
    discussion: Optional[DiscussionSchema] = None
    final_card: Optional[FinalCardSchema] = None
    fsrs: Optional[FSRSSchema] = None


class FlashcardRead(FlashcardBase):
    created_at: Optional[datetime] = None
    discussion: Optional[DiscussionSchema] = None
    final_card: Optional[FinalCardSchema] = None
    fsrs: Optional[FSRSSchema] = None

    class Config:
        orm_mode = True



class AudioSchema(BaseModel):
    filename: str
    timingFilename: Optional[str] = None

    class Config:
        orm_mode = True


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
        orm_mode = True
