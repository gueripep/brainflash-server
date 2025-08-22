from typing import List, Optional
import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from app.routes.flashcards.flashcards_fsrs import create_flashcard_fsrs_orm_from_dto

from app.database import (
	Flashcard,
	FlashcardDiscussion,
	FlashcardFinalCard,
	FlashcardFSRS,
	FlashcardDeck,
	AudioFile,
	get_db,
)
from app.pydantic.flashcard import (
	FlashcardCreate,
	FlashcardRead,
)
from app.pydantic.audio import AudioFileReadSchema
from app.gcp_config import gcp_config


router = APIRouter(prefix="/flashcards", tags=["flashcards"])


def _generate_signed_url_for_blob(storage_client, bucket_name: str, blob_name: str, expiration_hours: int = 1) -> str:
	"""
	Try to generate a V4 signed URL for the given blob. Fall back to public_url then to the canonical GCS URL.
	Returns None only if the bucket or client operations failed entirely.
	"""
	bucket = storage_client.bucket(bucket_name)
	blob = bucket.blob(blob_name)
	return blob.generate_signed_url(
		expiration=datetime.timedelta(hours=expiration_hours),
		version="v4",
		method="GET",
	)



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
	
	# Generate signed URLs for audio files
	storage_client = gcp_config.get_storage_client()
	bucket_name = "ttsinfo"
	
	# Convert to dict format and populate signed URLs
	flashcards_with_urls = []
	for item in items:
		print(f"Processing flashcard {item.__dict__}")
		dto = FlashcardRead.model_validate(item)
		dto.final_card.question_audio.signed_url_files = AudioFileReadSchema(
			audio_file=_generate_signed_url_for_blob(
				storage_client, bucket_name, item.final_card.question_audio.filename, expiration_hours=1
			),
			timing_file=_generate_signed_url_for_blob(
				storage_client, bucket_name, item.final_card.question_audio.timing_filename, expiration_hours=1
			)
		)
		dto.final_card.answer_audio.signed_url_files = AudioFileReadSchema(
			audio_file=_generate_signed_url_for_blob(
				storage_client, bucket_name, item.final_card.answer_audio.filename, expiration_hours=1
			),
			timing_file=_generate_signed_url_for_blob(
				storage_client, bucket_name, item.final_card.answer_audio.timing_filename, expiration_hours=1
			)
		)
		dto.discussion.audio.signed_url_files = AudioFileReadSchema(
			audio_file=_generate_signed_url_for_blob(
				storage_client, bucket_name, item.discussion.audio.filename, expiration_hours=1
			),
			timing_file=_generate_signed_url_for_blob(
				storage_client, bucket_name, item.discussion.audio.timing_filename, expiration_hours=1
			)
		)
		flashcards_with_urls.append(dto)

	return flashcards_with_urls


@router.get("/signed-urls/{flashcard_id}")
async def get_flashcard_signed_urls(flashcard_id: str, bucket: str = "ttsinfo", expiration_hours: int = 1, session: AsyncSession = Depends(get_db)):
	"""
	Return fresh signed URLs for all audio files associated with a flashcard.
	Useful when previously issued signed URLs have expired.
	"""
	q = select(Flashcard).where(Flashcard.id == flashcard_id).options(
		joinedload(Flashcard.discussion).joinedload(FlashcardDiscussion.audio),
		joinedload(Flashcard.final_card).joinedload(FlashcardFinalCard.question_audio),
		joinedload(Flashcard.final_card).joinedload(FlashcardFinalCard.answer_audio),
	)
	res = await session.execute(q)
	item = res.scalars().first()
	if not item:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flashcard not found")
	
	try:
		storage_client = gcp_config.get_storage_client()
		
		signed_urls = {
			"flashcard_id": flashcard_id,
			"bucket": bucket,
			"expiration_hours": expiration_hours,
			"urls": {}
		}
		
		# Discussion audio
		if item.discussion and item.discussion.audio:
			audio = item.discussion.audio
			discussion_urls = {}
			if audio.filename:
				discussion_urls["audio_url"] = _generate_signed_url_for_blob(storage_client, bucket, audio.filename, expiration_hours)
			if audio.timing_filename:
				discussion_urls["timing_url"] = _generate_signed_url_for_blob(storage_client, bucket, audio.timing_filename, expiration_hours)
			signed_urls["urls"]["discussion"] = discussion_urls
		
		# Final card audio
		if item.final_card:
			final_card_urls = {}
			
			if item.final_card.question_audio:
				question_audio = item.final_card.question_audio
				question_urls = {}
				if question_audio.filename:
					question_urls["audio_url"] = _generate_signed_url_for_blob(storage_client, bucket, question_audio.filename, expiration_hours)
				if question_audio.timing_filename:
					question_urls["timing_url"] = _generate_signed_url_for_blob(storage_client, bucket, question_audio.timing_filename, expiration_hours)
				final_card_urls["question"] = question_urls
			
			if item.final_card.answer_audio:
				answer_audio = item.final_card.answer_audio
				answer_urls = {}
				if answer_audio.filename:
					answer_urls["audio_url"] = _generate_signed_url_for_blob(storage_client, bucket, answer_audio.filename, expiration_hours)
				if answer_audio.timing_filename:
					answer_urls["timing_url"] = _generate_signed_url_for_blob(storage_client, bucket, answer_audio.timing_filename, expiration_hours)
				final_card_urls["answer"] = answer_urls
			
			if final_card_urls:
				signed_urls["urls"]["final_card"] = final_card_urls
		
		return signed_urls
	
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to generate signed URLs: {e}")

@router.put("/{flashcard_id}", response_model=FlashcardRead)
async def update_flashcard(flashcard_id: str, payload: FlashcardRead, session: AsyncSession = Depends(get_db)):
	# Ensure flashcard exists
	flashcard = await session.get(Flashcard, flashcard_id)
	if not flashcard:
		raise HTTPException(status_code=404, detail="Flashcard not found")

	# Update fields
	for field, value in payload.dict(exclude_unset=True).items():
		setattr(flashcard, field, value)

	await session.commit()
	await session.refresh(flashcard)
	return flashcard


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


@router.delete("/{flashcard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_flashcard(flashcard_id: str, session: AsyncSession = Depends(get_db)):
	item = await session.get(Flashcard, flashcard_id)
	if not item:
		raise HTTPException(status_code=404, detail="Flashcard not found")
	await session.delete(item)
	await session.commit()
	return None

def create_flashcard_orm_from_dto(dto: FlashcardCreate) -> Flashcard:
	return Flashcard(
		deck_id=dto.deck_id,
		stage=dto.stage,
		discussion=create_flashcard_discussion_orm_from_dto(dto.discussion),
		final_card=create_flashcard_final_card_orm_from_dto(dto.final_card),
		fsrs=create_flashcard_fsrs_orm_from_dto(dto.fsrs),
	)
