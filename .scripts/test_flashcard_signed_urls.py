#!/usr/bin/env python3
"""
Test script to verify flashcard signed URLs generation
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.gcp_config import gcp_config
from app.database import AsyncSessionLocal, Flashcard
from sqlalchemy import select
from sqlalchemy.orm import joinedload

async def test_flashcard_signed_urls():
    """Test generating signed URLs for flashcard audio files"""
    
    async with AsyncSessionLocal() as session:
        # Get a flashcard with audio
        q = select(Flashcard).options(
            joinedload(Flashcard.discussion).joinedload(Flashcard.discussion.audio),
            joinedload(Flashcard.final_card).joinedload(Flashcard.final_card.question_audio),
            joinedload(Flashcard.final_card).joinedload(Flashcard.final_card.answer_audio),
        ).limit(1)
        
        result = await session.execute(q)
        flashcard = result.scalars().first()
        
        if not flashcard:
            print("No flashcards found in database")
            return
            
        print(f"Testing signed URLs for flashcard ID: {flashcard.id}")
        
        try:
            storage_client = gcp_config.get_storage_client()
            bucket_name = "ttsinfo"
            
            # Test discussion audio
            if flashcard.discussion and flashcard.discussion.audio:
                audio = flashcard.discussion.audio
                print(f"\nDiscussion audio:")
                print(f"  Filename: {audio.filename}")
                print(f"  Timing filename: {audio.timing_filename}")
                
                if audio.filename:
                    from app.routes.flashcards import _generate_signed_url_for_blob
                    audio_url = _generate_signed_url_for_blob(storage_client, bucket_name, audio.filename, expiration_hours=1)
                    print(f"  Audio URL: {audio_url}")
                
                if audio.timing_filename:
                    timing_url = _generate_signed_url_for_blob(storage_client, bucket_name, audio.timing_filename, expiration_hours=1)
                    print(f"  Timing URL: {timing_url}")
            
            # Test final card audio
            if flashcard.final_card:
                if flashcard.final_card.question_audio:
                    audio = flashcard.final_card.question_audio
                    print(f"\nQuestion audio:")
                    print(f"  Filename: {audio.filename}")
                    print(f"  Timing filename: {audio.timing_filename}")
                    
                    if audio.filename:
                        from app.routes.flashcards import _generate_signed_url_for_blob
                        audio_url = _generate_signed_url_for_blob(storage_client, bucket_name, audio.filename, expiration_hours=1)
                        print(f"  Audio URL: {audio_url}")
                    
                    if audio.timing_filename:
                        timing_url = _generate_signed_url_for_blob(storage_client, bucket_name, audio.timing_filename, expiration_hours=1)
                        print(f"  Timing URL: {timing_url}")
                
                if flashcard.final_card.answer_audio:
                    audio = flashcard.final_card.answer_audio
                    print(f"\nAnswer audio:")
                    print(f"  Filename: {audio.filename}")
                    print(f"  Timing filename: {audio.timing_filename}")
                    
                    if audio.filename:
                        from app.routes.flashcards import _generate_signed_url_for_blob
                        audio_url = _generate_signed_url_for_blob(storage_client, bucket_name, audio.filename, expiration_hours=1)
                        print(f"  Audio URL: {audio_url}")
                    
                    if audio.timing_filename:
                        timing_url = _generate_signed_url_for_blob(storage_client, bucket_name, audio.timing_filename, expiration_hours=1)
                        print(f"  Timing URL: {timing_url}")
                        
        except Exception as e:
            print(f"Error generating signed URLs: {e}")


if __name__ == "__main__":
    asyncio.run(test_flashcard_signed_urls())
