from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.database import Flashcard, FlashcardFSRS, get_db
from app.schemas_db import FSRSSchema
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


router = APIRouter(prefix="/flashcards", tags=["flashcards"])

@router.get("/fsrs/", response_model=list[FSRSSchema])
async def read_fsrs(offset: int = 0, limit: int = Query(default=100, le=100), session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(FlashcardFSRS).offset(offset).limit(limit))
    fsrs = result.scalars().all()
    pydantic_fsrs = [FSRSSchema.model_validate(fsr) for fsr in fsrs]
    return pydantic_fsrs

@router.get("{flashcard_id}/fsrs/", response_model=FSRSSchema)
async def read_fsrs(flashcard_id: str, session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(FlashcardFSRS).where(FlashcardFSRS.flashcard_id == flashcard_id))
    db_fsrs = result.scalars().first()
    if not db_fsrs:
        raise HTTPException(status_code=404, detail="FSRS record not found for this flashcard")
    return FSRSSchema.model_validate(db_fsrs)


@router.put("/{flashcard_id}/fsrs", response_model=FSRSSchema)
async def update_fsrs(flashcard_id: str, payload: FSRSSchema, session: AsyncSession = Depends(get_db)):
    """
    Create or update the FSRS record for a flashcard. If an FSRS row exists it will be updated,
    otherwise a new row will be created and linked to the flashcard.
    """
    result = await session.execute(select(FlashcardFSRS).where(FlashcardFSRS.flashcard_id == flashcard_id))
    db_fsrs = result.scalars().first()
    
    if not db_fsrs:
        raise HTTPException(status_code=404, detail="FSRS record not found for this flashcard")
    
    pydantic_fsrs = FSRSSchema.model_validate(payload)
    
    new_db_fsrs = create_fsrs_orm_from_dto(pydantic_fsrs)
    session.add(new_db_fsrs)
    await session.commit()
    await session.refresh(new_db_fsrs)
    return new_db_fsrs





def create_fsrs_orm_from_dto(dto: FSRSSchema) -> FlashcardFSRS:
    return FlashcardFSRS(
        flashcard_id=dto.flashcard_id,
        due=dto.due,
        interval=dto.interval,
        repetitions=dto.repetitions,
        ef=dto.ef,
        last_reviewed=dto.last_reviewed,
    )
