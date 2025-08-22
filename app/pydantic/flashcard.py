

# Nested objects
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from app.database import FlashcardFSRS, FlashcardFinalCard
from app.pydantic.audio import AudioFileReadSchema, AudioFileUpdateSchema, create_audio_file_orm_from_dto


class FlashcardDiscussionSchema(BaseModel):
    ssml_text: str
    text: str
    audio: "AudioFileReadSchema"
    class Config:
        from_attributes = True


class FlashcardFinalCardUpdateSchema(BaseModel):
    front: str
    back: str
    question_audio: "AudioFileReadSchema"
    answer_audio: "AudioFileReadSchema"
    class Config:
        from_attributes = True


class FlashcardFSRSSchema(BaseModel):
    flashcard_id: UUID
    due: datetime
    stability: int
    difficulty: int
    elapsed_days: int
    scheduled_days: int
    reps: int
    lapses: int
    state: int
    learning_steps: int
    
    class Config:
        from_attributes = True


class FlashcardBase(BaseModel):
    deck_id: UUID = None
    stage: int


class FlashcardCreate(FlashcardBase):
    discussion: FlashcardDiscussionSchema
    final_card: FlashcardFinalCardUpdateSchema
    fsrs: FlashcardFSRSSchema

class FlashcardUpdate(BaseModel):
    deck_id: Optional[UUID] = None
    stage: Optional[int] = None
    discussion: Optional[FlashcardDiscussionSchema] = None
    final_card: Optional[FlashcardFinalCardUpdateSchema] = None
    fsrs: Optional[FlashcardFSRSSchema] = None

class FinalCardReadSchema(BaseModel):
    front: str
    back: str
    question_audio: "AudioFileReadSchema"
    answer_audio: "AudioFileReadSchema"
    class Config:
        from_attributes = True

class FlashcardRead(FlashcardBase):
    id: UUID
    created_at: datetime
    discussion: FlashcardDiscussionSchema
    final_card: FinalCardReadSchema
    fsrs: FlashcardFSRSSchema

    class Config:
        from_attributes = True



    
class FlashcardFinalCardUpdateSchema(BaseModel):
    front: str
    back: str
    question_audio: "AudioFileUpdateSchema"
    answer_audio: "AudioFileUpdateSchema"
    class Config:
        from_attributes = True
        
        
# mappers
def create_flashcard_fsrs_orm_from_dto(dto: FlashcardFSRSSchema) -> FlashcardFSRS:
    return FlashcardFSRS(
        flashcard_id=dto.flashcard_id,
        due=dto.due,
        interval=dto.interval,
        repetitions=dto.repetitions,
        ef=dto.ef,
        last_reviewed=dto.last_reviewed,
    )

def create_flashcard_final_card_orm_from_dto(dto: FlashcardFinalCardUpdateSchema) -> FlashcardFinalCard:
    return FlashcardFinalCard(
        front=dto.front,
        back=dto.back,
        question_audio=create_audio_file_orm_from_dto(dto.question_audio),
        answer_audio=create_audio_file_orm_from_dto(dto.answer_audio),
    )
