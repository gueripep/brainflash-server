

from sqlalchemy.future import select

from fastapi import APIRouter, Depends, HTTPException

from app.database import get_db
from app.pydantic.flashcard import FinalCardReadSchema, FlashcardFinalCardUpdateSchema, create_flashcard_final_card_orm_from_dto
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(prefix="/flashcards", tags=["flashcards"])


@router.put("/{flashcard_id}/final_card", response_model=FinalCardReadSchema)
async def update_final_card(flashcard_id: str, payload: FlashcardFinalCardUpdateSchema, session: AsyncSession = Depends(get_db)):
    """
    Create or update the FinalCard record for a flashcard. If a FinalCard row exists it will be updated,
    """
    result = await session.execute(select(FlashcardFinalCardUpdateSchema).where(FlashcardFinalCardUpdateSchema.flashcard_id == flashcard_id))
    db_final_card = result.scalars().first()

    if not db_final_card:
        raise HTTPException(status_code=404, detail="FinalCard record not found for this flashcard")

    pydantic_final_card = FlashcardFinalCardUpdateSchema.model_validate(payload)

    new_db_final_card = create_flashcard_final_card_orm_from_dto(pydantic_final_card)
    session.add(new_db_final_card)
    await session.commit()
    await session.refresh(new_db_final_card)
    return new_db_final_card