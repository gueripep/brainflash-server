from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from uuid import UUID


# Nested objects
class DiscussionSchema(BaseModel):
    ssml_text: str
    text: str
    audio: "AudioSchema"
    class Config:
        from_attributes = True


class FinalCardSchema(BaseModel):
    front: str
    back: str
    question_audio: "AudioSchema"
    answer_audio: "AudioSchema"
    class Config:
        from_attributes = True


class FSRSSchema(BaseModel):
    due: datetime
    stability: Optional[int] = None
    difficulty: Optional[int] = None
    elapsed_days: Optional[int] = None
    scheduled_days: Optional[int] = None
    reps: Optional[int] = None
    lapses: Optional[int] = None
    state: Optional[int] = None
    learning_steps: Optional[int] = None
    audio_id: Optional[int] = None
    
    class Config:
        from_attributes = True


class FlashcardBase(BaseModel):
    deck_id: Optional[UUID] = None
    stage: int


class FlashcardCreate(FlashcardBase):
    discussion: DiscussionSchema
    final_card: FinalCardSchema
    fsrs: FSRSSchema

class FlashcardUpdate(BaseModel):
    deck_id: Optional[UUID] = None
    stage: Optional[int] = None
    discussion: Optional[DiscussionSchema] = None
    final_card: Optional[FinalCardSchema] = None
    fsrs: Optional[FSRSSchema] = None


class FlashcardRead(FlashcardBase):
    id: UUID
    created_at: datetime
    discussion: DiscussionSchema
    final_card: FinalCardSchema
    fsrs: FSRSSchema

    class Config:
        from_attributes = True


class TimedAudioFileSchema(BaseModel):
    audio_file: str
    timing_file: str
    
class AudioSchema(BaseModel):
    filename: str
    timing_filename: str
    signed_url_files: Optional[TimedAudioFileSchema] = None
    class Config:
        from_attributes = True



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
