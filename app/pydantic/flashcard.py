

# Nested objects
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from app.database import Flashcard, FlashcardDiscussion, FlashcardFSRS, FlashcardFinalCard
from app.pydantic.audio import AudioFileCreateSchema, AudioFileReadSchema, AudioFileUpdateSchema, create_audio_file_orm_from_dto, update_audio_file_orm_from_dto


class FlashcardDiscussionCreateSchema(BaseModel):
    ssml_text: str
    text: str
    audio: "AudioFileCreateSchema"
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
    question_audio: "AudioFileUpdateSchema"
    answer_audio: "AudioFileUpdateSchema"
    class Config:
        from_attributes = True

class FlashcardFSRSCreateSchema(BaseModel):
    due: datetime
    stability: float
    difficulty: float
    elapsed_days: int
    scheduled_days: int
    reps: int
    lapses: int
    state: int
    learning_steps: int
    
class FlashcardFSRSUpdateSchema(BaseModel):
    due: Optional[datetime] = None
    stability: Optional[float] = None
    difficulty: Optional[float] = None
    elapsed_days: Optional[int] = None
    scheduled_days: Optional[int] = None
    reps: Optional[int] = None
    lapses: Optional[int] = None
    state: Optional[int] = None
    learning_steps: Optional[int] = None
    
    
class FlashcardFSRSReadSchema(BaseModel):
    flashcard_id: UUID
    due: datetime
    stability: float
    difficulty: float
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



        



# mappers
def create_flashcard_discussion_orm_from_dto(dto: FlashcardDiscussionCreateSchema) -> FlashcardDiscussion:
    return FlashcardDiscussion(
        ssml_text=dto.ssml_text,
        text=dto.text,
        audio=create_audio_file_orm_from_dto(dto.audio),
    )

def update_flashcard_discussion_orm_from_dto(orm: FlashcardDiscussion, dto: FlashcardDiscussionUpdateSchema) -> FlashcardDiscussion:
    orm.ssml_text = dto.ssml_text if dto.ssml_text is not None else orm.ssml_text
    orm.text = dto.text if dto.text is not None else orm.text
    orm.audio = update_audio_file_orm_from_dto(orm.audio, dto.audio) if dto.audio is not None else orm.audio
    return orm

def create_flashcard_fsrs_orm_from_dto(dto: FlashcardFSRSCreateSchema) -> FlashcardFSRS:
    return FlashcardFSRS(
        due=dto.due,
        stability=dto.stability,
        difficulty=dto.difficulty,
        elapsed_days=dto.elapsed_days,
        scheduled_days=dto.scheduled_days,
        reps=dto.reps,
        lapses=dto.lapses,
        state=dto.state,
        learning_steps=dto.learning_steps,
    )
def update_flashcard_fsrs_orm_from_dto(orm: FlashcardFSRS, dto: FlashcardFSRSUpdateSchema) -> FlashcardFSRS:
    orm.due = dto.due.replace(tzinfo=None) if dto.due is not None else orm.due
    orm.stability = dto.stability if dto.stability is not None else orm.stability
    orm.difficulty = dto.difficulty if dto.difficulty is not None else orm.difficulty
    orm.elapsed_days = dto.elapsed_days if dto.elapsed_days is not None else orm.elapsed_days
    orm.scheduled_days = dto.scheduled_days if dto.scheduled_days is not None else orm.scheduled_days
    orm.reps = dto.reps if dto.reps is not None else orm.reps
    orm.lapses = dto.lapses if dto.lapses is not None else orm.lapses
    orm.state = dto.state if dto.state is not None else orm.state
    orm.learning_steps = dto.learning_steps if dto.learning_steps is not None else orm.learning_steps
    return orm

def create_flashcard_final_card_orm_from_dto(dto: FlashcardFinalCardCreateSchema) -> FlashcardFinalCard:
    return FlashcardFinalCard(
        front=dto.front,
        back=dto.back,
        question_audio=create_audio_file_orm_from_dto(dto.question_audio),
        answer_audio=create_audio_file_orm_from_dto(dto.answer_audio),
    )

def update_flashcard_final_card_orm_from_dto(orm: FlashcardFinalCard, dto: FlashcardFinalCardUpdateSchema) -> FlashcardFinalCard:
    orm.front = dto.front if dto.front is not None else orm.front
    orm.back = dto.back if dto.back is not None else orm.back
    orm.question_audio = update_audio_file_orm_from_dto(orm.question_audio, dto.question_audio) if dto.question_audio is not None else orm.question_audio
    orm.answer_audio = update_audio_file_orm_from_dto(orm.answer_audio, dto.answer_audio) if dto.answer_audio is not None else orm.answer_audio
    return orm

def create_flashcard_orm_from_dto(dto: FlashcardCreateSchema) -> Flashcard:
	return Flashcard(
		deck_id=dto.deck_id,
		stage=dto.stage,
		discussion=create_flashcard_discussion_orm_from_dto(dto.discussion),
		final_card=create_flashcard_final_card_orm_from_dto(dto.final_card),
		fsrs=create_flashcard_fsrs_orm_from_dto(dto.fsrs),
	)

def update_flashcard_orm_from_dto(orm: Flashcard, dto: FlashcardUpdateSchema) -> Flashcard:
	orm.stage = dto.stage if dto.stage is not None else orm.stage
	orm.discussion = update_flashcard_discussion_orm_from_dto(orm.discussion, dto.discussion) if dto.discussion is not None else orm.discussion
	orm.final_card = update_flashcard_final_card_orm_from_dto(orm.final_card, dto.final_card) if dto.final_card is not None else orm.final_card
	orm.fsrs = update_flashcard_fsrs_orm_from_dto(orm.fsrs, dto.fsrs) if dto.fsrs is not None else orm.fsrs
	return orm