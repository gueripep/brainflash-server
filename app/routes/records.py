"""
CRUD endpoints for record-like models: TTSRecord, GeminiRecord, DailyProgress
"""
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db, TTSRecord, GeminiRecord, DailyProgress
from app.auth import current_active_user

router = APIRouter(prefix="/records", tags=["Records"])


def _row_to_tts(r: TTSRecord) -> Dict[str, Any]:
    return {
        "id": r.id,
        "text": r.text,
        "language_code": r.language_code,
        "voice_name": r.voice_name,
        "audio_encoding": r.audio_encoding,
        "enable_time_pointing": r.enable_time_pointing,
        "is_ssml": r.is_ssml,
        "audio_file_path": r.audio_file_path,
        "timing_file_path": r.timing_file_path,
        "processing_time_ms": r.processing_time_ms,
        "created_at": r.created_at,
    }


@router.get("/tts", response_model=List[Dict[str, Any]])
async def list_tts(limit: int = 20, offset: int = 0, db: AsyncSession = Depends(get_db)):
    stmt = select(TTSRecord).order_by(TTSRecord.created_at.desc()).offset(offset).limit(limit)
    res = await db.execute(stmt)
    rows = res.scalars().all()
    return [_row_to_tts(r) for r in rows]


@router.get("/tts/{id}")
async def get_tts(id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(TTSRecord).where(TTSRecord.id == id)
    res = await db.execute(stmt)
    r = res.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="TTS record not found")
    return _row_to_tts(r)


@router.post("/tts", dependencies=[Depends(current_active_user)])
async def create_tts(payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    r = TTSRecord(
        text=payload.get("text", ""),
        language_code=payload.get("language_code", "en-US"),
        voice_name=payload.get("voice_name", "en-US-Wavenet-D"),
        audio_encoding=payload.get("audio_encoding", "MP3"),
        enable_time_pointing=payload.get("enable_time_pointing", True),
        is_ssml=payload.get("is_ssml", False),
        audio_file_path=payload.get("audio_file_path"),
        timing_file_path=payload.get("timing_file_path"),
        processing_time_ms=payload.get("processing_time_ms"),
    )
    db.add(r)
    await db.commit()
    await db.refresh(r)
    return {"id": r.id}


@router.put("/tts/{id}", dependencies=[Depends(current_active_user)])
async def update_tts(id: int, payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    stmt = select(TTSRecord).where(TTSRecord.id == id)
    res = await db.execute(stmt)
    r = res.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="TTS record not found")
    for k, v in payload.items():
        if hasattr(r, k):
            setattr(r, k, v)
    db.add(r)
    await db.commit()
    await db.refresh(r)
    return {"id": r.id}


@router.delete("/tts/{id}", dependencies=[Depends(current_active_user)])
async def delete_tts(id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(TTSRecord).where(TTSRecord.id == id)
    res = await db.execute(stmt)
    r = res.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="TTS record not found")
    await db.delete(r)
    await db.commit()
    return {"deleted": True}


# Gemini records
def _row_to_gemini(r: GeminiRecord) -> Dict[str, Any]:
    return {
        "id": r.id,
        "prompt": r.prompt,
        "response": r.response,
        "processing_time_ms": r.processing_time_ms,
        "model_used": r.model_used,
        "created_at": r.created_at,
    }


@router.get("/gemini", response_model=List[Dict[str, Any]])
async def list_gemini(limit: int = 20, offset: int = 0, db: AsyncSession = Depends(get_db)):
    stmt = select(GeminiRecord).order_by(GeminiRecord.created_at.desc()).offset(offset).limit(limit)
    res = await db.execute(stmt)
    rows = res.scalars().all()
    return [_row_to_gemini(r) for r in rows]


@router.get("/gemini/{id}")
async def get_gemini(id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(GeminiRecord).where(GeminiRecord.id == id)
    res = await db.execute(stmt)
    r = res.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Gemini record not found")
    return _row_to_gemini(r)


@router.post("/gemini", dependencies=[Depends(current_active_user)])
async def create_gemini(payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    r = GeminiRecord(prompt=payload.get("prompt", ""), response=payload.get("response"))
    db.add(r)
    await db.commit()
    await db.refresh(r)
    return {"id": r.id}


@router.put("/gemini/{id}", dependencies=[Depends(current_active_user)])
async def update_gemini(id: int, payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    stmt = select(GeminiRecord).where(GeminiRecord.id == id)
    res = await db.execute(stmt)
    r = res.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Gemini record not found")
    for k, v in payload.items():
        if hasattr(r, k):
            setattr(r, k, v)
    db.add(r)
    await db.commit()
    await db.refresh(r)
    return {"id": r.id}


@router.delete("/gemini/{id}", dependencies=[Depends(current_active_user)])
async def delete_gemini(id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(GeminiRecord).where(GeminiRecord.id == id)
    res = await db.execute(stmt)
    r = res.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Gemini record not found")
    await db.delete(r)
    await db.commit()
    return {"deleted": True}


# Daily progress
@router.get("/daily", response_model=List[Dict[str, Any]])
async def list_daily(limit: int = 50, offset: int = 0, db: AsyncSession = Depends(get_db)):
    stmt = select(DailyProgress).order_by(DailyProgress.date.desc()).offset(offset).limit(limit)
    res = await db.execute(stmt)
    rows = res.scalars().all()
    return [{"id": r.id, "date": r.date, "new_cards_studied": r.new_cards_studied} for r in rows]


@router.post("/daily", dependencies=[Depends(current_active_user)])
async def create_daily(payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    r = DailyProgress(date=payload.get("date"), new_cards_studied=payload.get("new_cards_studied", 0))
    db.add(r)
    await db.commit()
    await db.refresh(r)
    return {"id": r.id}
