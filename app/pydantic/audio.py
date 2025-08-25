from typing import Optional
from pydantic import BaseModel

from app.database import DiscussionAudio, FinalCardQuestionAudio
from app.database import DiscussionAudio, FinalCardQuestionAudio, FinalCardAnswerAudio  


class AudioFileInsertSchema(BaseModel):
    audio_file: str
    timing_file: str
    
# this class is never used in the db, only for read
class TimedAudioFile(BaseModel):
    audio_file: str
    timing_file: str
    
class AudioFileReadSchema(BaseModel):
    filename: str
    timing_filename: str
    signed_url_files: Optional[TimedAudioFile] = None
    class Config:
        from_attributes = True
        
class AudioFileUpdateSchema(BaseModel):
    filename: Optional[str] = None
    timing_filename: Optional[str] = None

class AudioFileCreateSchema(BaseModel):
    filename: str
    timing_filename: str

# mapper
def create_discussion_audio_orm_from_dto(dto: AudioFileCreateSchema) -> "DiscussionAudio":
    return DiscussionAudio(
        filename=dto.filename,
        timing_filename=dto.timing_filename,
    )

def create_final_card_question_audio_orm_from_dto(dto: AudioFileCreateSchema) -> "FinalCardQuestionAudio":
    return FinalCardQuestionAudio(
        filename=dto.filename,
        timing_filename=dto.timing_filename,
    )

def create_final_card_answer_audio_orm_from_dto(dto: AudioFileCreateSchema) -> "FinalCardQuestionAudio":
    return FinalCardQuestionAudio(
        filename=dto.filename,
        timing_filename=dto.timing_filename,
    )

def update_discussion_audio_orm_from_dto(orm: DiscussionAudio, dto: AudioFileUpdateSchema) -> DiscussionAudio:
    if dto.filename is not None:
        orm.filename = dto.filename
    if dto.timing_filename is not None:
        orm.timing_filename = dto.timing_filename
    return orm

def update_final_card_question_audio_orm_from_dto(orm: FinalCardQuestionAudio, dto: AudioFileUpdateSchema) -> FinalCardQuestionAudio:
    if dto.filename is not None:
        orm.filename = dto.filename
    if dto.timing_filename is not None:
        orm.timing_filename = dto.timing_filename
    return orm

def update_final_card_answer_audio_orm_from_dto(orm: FinalCardAnswerAudio, dto: AudioFileUpdateSchema) -> FinalCardAnswerAudio:
    if dto.filename is not None:
        orm.filename = dto.filename
    if dto.timing_filename is not None:
        orm.timing_filename = dto.timing_filename
    return orm
