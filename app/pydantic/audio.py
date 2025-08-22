from typing import Optional
from pydantic import BaseModel

from app.database import AudioFile


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
def create_audio_file_orm_from_dto(dto: AudioFileCreateSchema) -> "AudioFile":
    return AudioFile(
        filename=dto.filename,
        timing_filename=dto.timing_filename,
    )
    
def update_audio_file_orm_from_dto(orm: AudioFile, dto: AudioFileUpdateSchema) -> AudioFile:
    if dto.filename is not None:
        orm.filename = dto.filename
    if dto.timing_filename is not None:
        orm.timing_filename = dto.timing_filename
    return orm