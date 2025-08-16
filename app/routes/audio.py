"""
CRUD endpoints for AudioFile and StudySession
"""
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db, AudioFile, StudySession
from app.auth import current_active_user

router = APIRouter(prefix="/audio", tags=["Audio"])


@router.get("/files", response_model=List[Dict[str, Any]])
async def list_audio(limit: int = 50, offset: int = 0, db: AsyncSession = Depends(get_db)):
    stmt = select(AudioFile).order_by(AudioFile.id.desc()).offset(offset).limit(limit)
    res = await db.execute(stmt)
    rows = res.scalars().all()
    return [{"id": r.id, "filename": r.filename, "timing_filename": r.timing_filename} for r in rows]


@router.post("/files", dependencies=[Depends(current_active_user)])
async def create_audio(payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    filename = payload.get("filename")
    if not filename:
        raise HTTPException(status_code=400, detail="`filename` is required and cannot be empty")
    timing = payload.get("timing_filename")
    r = AudioFile(filename=filename, timing_filename=timing)
    db.add(r)
    await db.commit()
    await db.refresh(r)
    return {"id": r.id}


@router.put("/files/{id}", dependencies=[Depends(current_active_user)])
async def update_audio(id: int, payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    stmt = select(AudioFile).where(AudioFile.id == id)
    res = await db.execute(stmt)
    r = res.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Audio file not found")
    if "filename" in payload:
        filename = payload.get("filename")
        if filename is None:
            raise HTTPException(status_code=400, detail="`filename` cannot be null")
        r.filename = filename
    if "timing_filename" in payload:
        r.timing_filename = payload.get("timing_filename")
    db.add(r)
    await db.commit()
    await db.refresh(r)
    return {"id": r.id}


@router.delete("/files/{id}", dependencies=[Depends(current_active_user)])
async def delete_audio(id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(AudioFile).where(AudioFile.id == id)
    res = await db.execute(stmt)
    r = res.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Audio file not found")
    await db.delete(r)
    await db.commit()
    return {"deleted": True}


# Study sessions
@router.get("/sessions", response_model=List[Dict[str, Any]])
async def list_sessions(limit: int = 50, offset: int = 0, db: AsyncSession = Depends(get_db)):
    stmt = select(StudySession).order_by(StudySession.id.desc()).offset(offset).limit(limit)
    res = await db.execute(stmt)
    rows = res.scalars().all()
    out = []
    for s in rows:
        out.append({
            "id": s.id,
            "deck_id": s.deck_id,
            "start_time": s.start_time,
            "cards_studied": s.cards_studied,
            "question_audio_id": s.question_audio_id,
            "answer_audio_id": s.answer_audio_id,
        })
    return out


@router.post("/sessions", dependencies=[Depends(current_active_user)])
async def create_session(payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    r = StudySession(
        id=payload.get("id"),
        deck_id=payload.get("deck_id"),
        start_time=payload.get("start_time"),
        cards_studied=payload.get("cards_studied", 0),
    question_audio_id=payload.get("question_audio_id"),
    answer_audio_id=payload.get("answer_audio_id"),
    )
    db.add(r)
    await db.commit()
    await db.refresh(r)
    return {"id": r.id}


@router.put("/sessions/{id}", dependencies=[Depends(current_active_user)])
async def update_session(id: str, payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    stmt = select(StudySession).where(StudySession.id == id)
    res = await db.execute(stmt)
    r = res.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Study session not found")
    for k, v in payload.items():
        if hasattr(r, k):
            setattr(r, k, v)
    db.add(r)
    await db.commit()
    await db.refresh(r)
    return {"id": r.id}


@router.delete("/sessions/{id}", dependencies=[Depends(current_active_user)])
async def delete_session(id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(StudySession).where(StudySession.id == id)
    res = await db.execute(stmt)
    r = res.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Study session not found")
    await db.delete(r)
    await db.commit()
    return {"deleted": True}
