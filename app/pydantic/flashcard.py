

# Nested objects
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from app.database import Flashcard, FlashcardDiscussion, FlashcardFSRS, FlashcardFinalCard
from app.pydantic.audio import AudioFileCreateSchema, AudioFileReadSchema, AudioFileUpdateSchema, create_audio_file_orm_from_dto


class FlashcardDiscussionCreateSchema(BaseModel):
    ssml_text: str
    text: str
    audio: "AudioFileReadSchema"
    class Config:
        from_attributes = True

class FlashcardDiscussionUpdateSchema(BaseModel):
    ssml_text: Optional[str] = None
    text: Optional[str] = None
    audio: Optional["AudioFileUpdateSchema"] = None
    class Config:
        from_attributes = True


class FlashcardFinalCardUpdateSchema(BaseModel):
    front: str
    back: str
    question_audio: "AudioFileReadSchema"
    answer_audio: "AudioFileReadSchema"
    class Config:
        from_attributes = True

class FlashcardFSRSCreateSchema(BaseModel):
    due: datetime
    stability: int
    difficulty: int
    elapsed_days: int
    scheduled_days: int
    reps: int
    lapses: int
    state: int
    learning_steps: int
    
class FlashcardFSRSUpdateSchema(BaseModel):
    due: Optional[datetime] = None
    stability: Optional[int] = None
    difficulty: Optional[int] = None
    elapsed_days: Optional[int] = None
    scheduled_days: Optional[int] = None
    reps: Optional[int] = None
    lapses: Optional[int] = None
    state: Optional[int] = None
    learning_steps: Optional[int] = None
    
    
class FlashcardFSRSReadSchema(BaseModel):
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

class FlashcardFinalCardCreateSchema(BaseModel):
    front: str
    back: str
    question_audio: "AudioFileCreateSchema"
    answer_audio: "AudioFileCreateSchema"
    class Config:
        from_attributes = True
        
class FlashcardCreateSchema(BaseModel):
    deck_id: UUID
    stage: int
    discussion: FlashcardDiscussionCreateSchema
    final_card: FlashcardFinalCardCreateSchema
    fsrs: FlashcardFSRSCreateSchema

class FlashcardUpdateSchema(BaseModel):
    stage: Optional[int] = None
    discussion: Optional[FlashcardDiscussionUpdateSchema] = None
    final_card: Optional[FlashcardFinalCardUpdateSchema] = None
    fsrs: Optional[FlashcardFSRSUpdateSchema] = None

class FinalCardReadSchema(BaseModel):
    front: str
    back: str
    question_audio: "AudioFileReadSchema"
    answer_audio: "AudioFileReadSchema"
    class Config:
        from_attributes = True
        
class FlashcardDiscussionReadSchema(BaseModel):
    ssml_text: Optional[str] = None
    text: str
    audio: AudioFileReadSchema
    class Config:
        from_attributes = True

class FlashcardReadSchema(BaseModel):
    id: UUID
    created_at: datetime
    deck_id: UUID
    stage: int
    discussion: FlashcardDiscussionReadSchema
    final_card: FinalCardReadSchema
    fsrs: FlashcardFSRSReadSchema

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
def create_flashcard_discussion_orm_from_dto(dto: FlashcardDiscussionCreateSchema) -> FlashcardDiscussion:
    return FlashcardDiscussion(
        ssml_text=dto.ssml_text,
        text=dto.text,
        audio=create_audio_file_orm_from_dto(dto.audio),
    )


def create_flashcard_fsrs_orm_from_dto(dto: FlashcardFSRSReadSchema) -> FlashcardFSRS:
    return FlashcardFSRS(
        flashcard_id=dto.flashcard_id,
        due=dto.due,
        interval=dto.interval,
        repetitions=dto.repetitions,
        ef=dto.ef,
        last_reviewed=dto.last_reviewed,
    )
def update_flashcard_fsrs_orm_from_dto(orm: FlashcardFSRS, dto: FlashcardFSRSUpdateSchema) -> FlashcardFSRS:
    orm.due = dto.due.replace(tzinfo=None)
    orm.stability = dto.stability
    orm.difficulty = dto.difficulty
    orm.elapsed_days = dto.elapsed_days
    orm.scheduled_days = dto.scheduled_days
    orm.reps = dto.reps
    orm.lapses = dto.lapses
    orm.state = dto.state
    orm.learning_steps = dto.learning_steps
    return orm

def create_flashcard_final_card_orm_from_dto(dto: FlashcardFinalCardUpdateSchema) -> FlashcardFinalCard:
    return FlashcardFinalCard(
        front=dto.front,
        back=dto.back,
        question_audio=create_audio_file_orm_from_dto(dto.question_audio),
        answer_audio=create_audio_file_orm_from_dto(dto.answer_audio),
    )

def create_flashcard_orm_from_dto(dto: FlashcardCreateSchema) -> Flashcard:
	return Flashcard(
		deck_id=dto.deck_id,
		stage=dto.stage,
		discussion=create_flashcard_discussion_orm_from_dto(dto.discussion),
		final_card=create_flashcard_final_card_orm_from_dto(dto.final_card),
		fsrs=create_flashcard_fsrs_orm_from_dto(dto.fsrs),
	)

def update_flashcard_orm_from_dto(orm: Flashcard, dto: FlashcardUpdateSchema) -> Flashcard:
	orm.stage = dto.stage
	orm.discussion = create_flashcard_discussion_orm_from_dto(dto.discussion)
	orm.final_card = create_flashcard_final_card_orm_from_dto(dto.final_card)
	orm.fsrs = update_flashcard_fsrs_orm_from_dto(orm.fsrs, dto.fsrs)
	return orm