#!/usr/bin/env python3
"""
Generate signed URLs for all flashcards
"""
import asyncio
import sys
import os
import json
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.gcp_config import gcp_config
from app.database import AsyncSessionLocal, Flashcard
from app.routes.flashcards import _generate_signed_url_for_blob
from sqlalchemy import select
from sqlalchemy.orm import joinedload


async def generate_all_flashcard_signed_urls():
    """Generate signed URLs for all flashcards and save to JSON file"""
    
    async with AsyncSessionLocal() as session:
        # Get all flashcards with audio
        q = select(Flashcard).options(
            joinedload(Flashcard.discussion).joinedload(Flashcard.discussion.audio),
            joinedload(Flashcard.final_card).joinedload(Flashcard.final_card.question_audio),
            joinedload(Flashcard.final_card).joinedload(Flashcard.final_card.answer_audio),
        )
        
        result = await session.execute(q)
        flashcards = result.scalars().all()
        
        if not flashcards:
            print("No flashcards found in database")
            return
            
        print(f"Generating signed URLs for {len(flashcards)} flashcards...")
        
        try:
            storage_client = gcp_config.get_storage_client()
            bucket_name = "ttsinfo"
            expiration_hours = 24  # URLs valid for 24 hours
            
            all_urls = {
                "generated_at": datetime.now().isoformat(),
                "bucket": bucket_name,
                "expiration_hours": expiration_hours,
                "flashcards": []
            }
            
            for flashcard in flashcards:
                flashcard_urls = {
                    "id": str(flashcard.id),
                    "deck_id": str(flashcard.deck_id) if flashcard.deck_id else None,
                    "stage": flashcard.stage,
                    "urls": {}
                }
                
                # Discussion audio URLs
                if flashcard.discussion and flashcard.discussion.audio:
                    audio = flashcard.discussion.audio
                    discussion_urls = {}
                    
                    if audio.filename:
                        discussion_urls["audio_url"] = _generate_signed_url_for_blob(
                            storage_client, bucket_name, audio.filename, expiration_hours=expiration_hours
                        )
                    if audio.timing_filename:
                        discussion_urls["timing_url"] = _generate_signed_url_for_blob(
                            storage_client, bucket_name, audio.timing_filename, expiration_hours=expiration_hours
                        )
                    
                    if discussion_urls:
                        flashcard_urls["urls"]["discussion"] = discussion_urls
                
                # Final card audio URLs
                if flashcard.final_card:
                    final_card_urls = {}
                    
                    if flashcard.final_card.question_audio:
                        audio = flashcard.final_card.question_audio
                        question_urls = {}
                        if audio.filename:
                            question_urls["audio_url"] = _generate_signed_url_for_blob(
                                storage_client, bucket_name, audio.filename, expiration_hours=expiration_hours
                            )
                        if audio.timing_filename:
                            question_urls["timing_url"] = _generate_signed_url_for_blob(
                                storage_client, bucket_name, audio.timing_filename, expiration_hours=expiration_hours
                            )
                        if question_urls:
                            final_card_urls["question"] = question_urls
                    
                    if flashcard.final_card.answer_audio:
                        audio = flashcard.final_card.answer_audio
                        answer_urls = {}
                        if audio.filename:
                            answer_urls["audio_url"] = _generate_signed_url_for_blob(
                                storage_client, bucket_name, audio.filename, expiration_hours=expiration_hours
                            )
                        if audio.timing_filename:
                            answer_urls["timing_url"] = _generate_signed_url_for_blob(
                                storage_client, bucket_name, audio.timing_filename, expiration_hours=expiration_hours
                            )
                        if answer_urls:
                            final_card_urls["answer"] = answer_urls
                    
                    if final_card_urls:
                        flashcard_urls["urls"]["final_card"] = final_card_urls
                
                # Only add flashcard if it has some URLs
                if flashcard_urls["urls"]:
                    all_urls["flashcards"].append(flashcard_urls)
                    print(f"Generated URLs for flashcard {flashcard.id}")
            
            # Save to JSON file
            output_file = f"flashcard_signed_urls_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            output_path = os.path.join(os.path.dirname(__file__), output_file)
            
            with open(output_path, 'w') as f:
                json.dump(all_urls, f, indent=2, default=str)
            
            print(f"\nGenerated signed URLs for {len(all_urls['flashcards'])} flashcards")
            print(f"URLs saved to: {output_path}")
            print(f"URLs expire in {expiration_hours} hours")
                        
        except Exception as e:
            print(f"Error generating signed URLs: {e}")


if __name__ == "__main__":
    asyncio.run(generate_all_flashcard_signed_urls())
