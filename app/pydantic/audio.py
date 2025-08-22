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
    filename: str
    timing_filename: str

# mapper
def create_audio_file_orm_from_dto(dto: AudioFileUpdateSchema) -> "AudioFile":
    return AudioFileInsertSchema(
        audio_file=dto.filename,
        timing_file=dto.timing_filename,
    )