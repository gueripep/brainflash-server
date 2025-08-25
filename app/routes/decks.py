from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import FlashcardDeck, Flashcard, get_db, User
from app.auth import current_active_user
from app.pydantic.deck import DeckCreate, DeckRead, DeckUpdate

router = APIRouter(prefix="/decks", tags=["decks"])


def _deck_to_dto(deck: FlashcardDeck, card_count: int) -> DeckRead:
    """Build a DeckRead DTO from a SQLAlchemy `FlashcardDeck` plus a card count.

    Keeps DTO construction in one place so both endpoints behave the same.
    """
    return DeckRead.model_validate({
        **deck.__dict__,
        "card_count": card_count,
    })


@router.get("/", response_model=List[DeckRead])
async def list_decks(skip: int = 0, limit: int = 100, session: AsyncSession = Depends(get_db), current_user: User = Depends(current_active_user)):
    q = select(FlashcardDeck, func.count(FlashcardDeck.cards)).where(FlashcardDeck.owner_id == current_user.id).offset(skip).limit(limit).join(FlashcardDeck.cards, isouter=True).group_by(FlashcardDeck.id)
    res = await session.execute(q)
    items = res.all()
    items_dtos = [_deck_to_dto(deck, card_count) for deck, card_count in items]
    return items_dtos


@router.get("/{deck_id}", response_model=DeckRead)
async def get_deck(deck_id: str, session: AsyncSession = Depends(get_db)):
    q = select(FlashcardDeck, func.count(FlashcardDeck.cards)).where(FlashcardDeck.id == deck_id).join(FlashcardDeck.cards, isouter=True).group_by(FlashcardDeck.id)
    res = await session.execute(q)

    if not res:
        raise HTTPException(status_code=404, detail="Deck not found")

    deck, card_count = res.one()
    return _deck_to_dto(deck, card_count)


@router.post("/", response_model=DeckRead, status_code=status.HTTP_201_CREATED)
async def create_deck(
    payload: DeckCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(current_active_user),
):
    deck = FlashcardDeck(name=payload.name, owner_id=current_user.id)
    session.add(deck)
    await session.commit()
    await session.refresh(deck)
    return _deck_to_dto(deck, 0)


@router.put("/{deck_id}", response_model=DeckRead)
async def update_deck(deck_id: str, payload: DeckUpdate, session: AsyncSession = Depends(get_db)):
    deck = await session.get(FlashcardDeck, deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    if payload.name is not None:
        deck.name = payload.name
    await session.commit()
    await session.refresh(deck)
    return deck


@router.delete("/{deck_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deck(deck_id: str, session: AsyncSession = Depends(get_db), current_user: User = Depends(current_active_user),):
    deck = await session.get(FlashcardDeck, deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    await session.delete(deck)
    await session.commit()
    return None
