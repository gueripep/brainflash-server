from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import FlashcardDeck, get_db, User
from app.auth import current_active_user
from app.pydantic.deck import DeckCreate, DeckRead, DeckUpdate

router = APIRouter(prefix="/decks", tags=["decks"])


@router.get("/", response_model=List[DeckRead])
async def list_decks(skip: int = 0, limit: int = 100, session: AsyncSession = Depends(get_db)):
    q = select(FlashcardDeck).offset(skip).limit(limit)
    res = await session.execute(q)
    items = res.scalars().all()
    return items


@router.get("/{deck_id}", response_model=DeckRead)
async def get_deck(deck_id: str, session: AsyncSession = Depends(get_db)):
    deck = await session.get(FlashcardDeck, deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    return deck


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
    return deck


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
