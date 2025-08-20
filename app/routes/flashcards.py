from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import (
	Flashcard,
	FlashcardDiscussion,
	FlashcardFinalCard,
	FlashcardFSRS,
	FlashcardDeck,
	AudioFile,
	get_db,
)
from app.schemas_db import (
	FlashcardCreate,
	FlashcardRead,
	FlashcardUpdate,
)

router = APIRouter(prefix="/flashcards", tags=["flashcards"])


@router.get("/", response_model=List[FlashcardRead])
async def list_flashcards(skip: int = 0, limit: int = 100, session: AsyncSession = Depends(get_db)):
	q = select(Flashcard).options(
		joinedload(Flashcard.discussion).joinedload(FlashcardDiscussion.audio),
		joinedload(Flashcard.final_card).joinedload(FlashcardFinalCard.question_audio),
		joinedload(Flashcard.final_card).joinedload(FlashcardFinalCard.answer_audio),
		joinedload(Flashcard.fsrs),
	).offset(skip).limit(limit)
	res = await session.execute(q)
	items = res.scalars().all()
	return items


@router.get("/{flashcard_id}", response_model=FlashcardRead)
async def get_flashcard(flashcard_id: str, session: AsyncSession = Depends(get_db)):
	q = select(Flashcard).where(Flashcard.id == flashcard_id).options(
		joinedload(Flashcard.discussion),
		joinedload(Flashcard.final_card),
		joinedload(Flashcard.fsrs),
	)
	res = await session.execute(q)
	item = res.scalars().first()
	if not item:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flashcard not found")
	return item


@router.post("/", response_model=FlashcardRead, status_code=status.HTTP_201_CREATED)
async def create_flashcard(payload: FlashcardCreate, session: AsyncSession = Depends(get_db)):
	# Ensure deck exists (deck_id required in schema)
	deck = await session.get(FlashcardDeck, payload.deck_id)
	if not deck:
		raise HTTPException(status_code=404, detail="Deck not found")

	flashcard = Flashcard(deck_id=payload.deck_id, stage=payload.stage)
	session.add(flashcard)
	await session.flush()

	# nested discussion
	if payload.discussion:
		a = AudioFile(filename=payload.discussion.audio.filename, timing_filename=payload.discussion.audio.timing_filename)
		session.add(a)
		await session.flush()
		audio_id = a.id

		disc = FlashcardDiscussion(
			flashcard_id=flashcard.id,
			ssml_text=payload.discussion.ssml_text,
			text=payload.discussion.text,
			audio_id=audio_id,
		)
		session.add(disc)

	if payload.final_card:

		qa = AudioFile(filename=payload.final_card.question_audio.filename, timing_filename=payload.final_card.question_audio.timing_filename)
		session.add(qa)
		await session.flush()
		q_audio_id = qa.id

		aa = AudioFile(filename=payload.final_card.answer_audio.filename, timing_filename=payload.final_card.answer_audio.timing_filename)
		session.add(aa)
		await session.flush()
		a_audio_id = aa.id
		fc = FlashcardFinalCard(
			flashcard_id=flashcard.id,
			front=payload.final_card.front,
			back=payload.final_card.back,
			question_audio_id=q_audio_id,
			answer_audio_id=a_audio_id,
		)
		session.add(fc)

	if payload.fsrs:
		fs = FlashcardFSRS(flashcard_id=flashcard.id, due=payload.fsrs.due.replace(tzinfo=None), stability=payload.fsrs.stability, difficulty=payload.fsrs.difficulty, elapsed_days=payload.fsrs.elapsed_days, scheduled_days=payload.fsrs.scheduled_days, reps=payload.fsrs.reps, lapses=payload.fsrs.lapses, state=payload.fsrs.state, learning_steps=payload.fsrs.learning_steps)
		session.add(fs)

	await session.commit()
	await session.refresh(flashcard)

	# reload with relationships
	q = select(Flashcard).where(Flashcard.id == flashcard.id).options(
		joinedload(Flashcard.discussion).joinedload(FlashcardDiscussion.audio),
		joinedload(Flashcard.final_card).joinedload(FlashcardFinalCard.question_audio),
		joinedload(Flashcard.final_card).joinedload(FlashcardFinalCard.answer_audio),
		joinedload(Flashcard.fsrs),
	)
	res = await session.execute(q)
	created = res.scalars().first()
	return created


@router.put("/{flashcard_id}", response_model=FlashcardRead)
async def update_flashcard(flashcard_id: str, payload: FlashcardUpdate, session: AsyncSession = Depends(get_db)):
	item = await session.get(Flashcard, flashcard_id)
	if not item:
		raise HTTPException(status_code=404, detail="Flashcard not found")
	if payload.deck_id is not None:
		# validate new deck exists
		new_deck = await session.get(FlashcardDeck, payload.deck_id)
		if not new_deck:
			raise HTTPException(status_code=404, detail="Deck not found")
		item.deck_id = payload.deck_id
	if payload.stage is not None:
		item.stage = payload.stage

	# handle nested updates for discussion/final_card/fsrs (upsert semantics)
	if payload.discussion is not None:
		disc = await session.get(FlashcardDiscussion, flashcard_id)
		if disc:
			disc.ssml_text = payload.discussion.ssml_text
			disc.text = payload.discussion.text
			# convert AudioSchema -> dict for JSON column
			disc.audio = payload.discussion.audio.dict() if payload.discussion.audio is not None else None
		else:
			audio = payload.discussion.audio.dict() if payload.discussion.audio is not None else None
			session.add(FlashcardDiscussion(flashcard_id=flashcard_id, ssml_text=payload.discussion.ssml_text, text=payload.discussion.text, audio=audio))

	if payload.final_card is not None:
		fc = await session.get(FlashcardFinalCard, flashcard_id)
		if fc:
			fc.front = payload.final_card.front
			fc.back = payload.final_card.back
			fc.question_audio = payload.final_card.question_audio.dict() if payload.final_card.question_audio is not None else None
			fc.answer_audio = payload.final_card.answer_audio.dict() if payload.final_card.answer_audio is not None else None
		else:
			q_audio = payload.final_card.question_audio.dict() if payload.final_card.question_audio is not None else None
			a_audio = payload.final_card.answer_audio.dict() if payload.final_card.answer_audio is not None else None
			session.add(FlashcardFinalCard(flashcard_id=flashcard_id, front=payload.final_card.front, back=payload.final_card.back, question_audio=q_audio, answer_audio=a_audio))

	if payload.fsrs is not None:
		fs = await session.get(FlashcardFSRS, flashcard_id)
		if fs:
			fs.due = payload.fsrs.due.replace(tzinfo=None)
			fs.stability = payload.fsrs.stability
			fs.difficulty = payload.fsrs.difficulty
			fs.elapsed_days = payload.fsrs.elapsed_days
			fs.scheduled_days = payload.fsrs.scheduled_days
			fs.reps = payload.fsrs.reps
			fs.lapses = payload.fsrs.lapses
			fs.state = payload.fsrs.state
			fs.learning_steps = payload.fsrs.learning_steps
		else:
			session.add(FlashcardFSRS(flashcard_id=flashcard_id, due=payload.fsrs.due, stability=payload.fsrs.stability, difficulty=payload.fsrs.difficulty, elapsed_days=payload.fsrs.elapsed_days, scheduled_days=payload.fsrs.scheduled_days, reps=payload.fsrs.reps, lapses=payload.fsrs.lapses, state=payload.fsrs.state, learning_steps=payload.fsrs.learning_steps, audio_id=payload.fsrs.audio_id))

	await session.commit()

	# return refreshed with relationships
	q = select(Flashcard).where(Flashcard.id == flashcard_id).options(
		joinedload(Flashcard.discussion),
		joinedload(Flashcard.final_card),
		joinedload(Flashcard.fsrs),
	)
	res = await session.execute(q)
	updated = res.scalars().first()
	return updated


@router.delete("/{flashcard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_flashcard(flashcard_id: str, session: AsyncSession = Depends(get_db)):
	item = await session.get(Flashcard, flashcard_id)
	if not item:
		raise HTTPException(status_code=404, detail="Flashcard not found")
	await session.delete(item)
	await session.commit()
	return None
