"""
TTS (Text-to-Speech) route handlers
"""
import os
import hashlib
import datetime
import json
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from google.cloud import texttospeech_v1beta1

from models import TTSRequest
from gcp_config import gcp_config

router = APIRouter(prefix="/tts", tags=["Text-to-Speech"])


@router.post("/synthesize")
def synthesize_speech(request: TTSRequest) -> Dict[str, Any]:
    """
    Convert text to speech using Google Cloud TTS and save the audio file
    """
    try:
        # Initialize the TTS client
        client = gcp_config.get_tts_client()
        
        # Convert text to SSML with word marks if timing is enabled
        if request.enable_time_pointing:
            ssml_text, word_marks = gcp_config.prepare_ssml_with_marks(request.text, request.is_ssml)
            synthesis_input = texttospeech_v1beta1.SynthesisInput(ssml=ssml_text)
        else:
            # For non-timing requests
            synthesis_input = texttospeech_v1beta1.SynthesisInput(ssml=request.text)
            word_marks = []
        
        # Build the voice request
        voice = texttospeech_v1beta1.VoiceSelectionParams(
            language_code=request.language_code,
            name=request.voice_name
        )
        
        # Select the type of audio file to return
        audio_config = texttospeech_v1beta1.AudioConfig(
            audio_encoding=getattr(texttospeech_v1beta1.AudioEncoding, request.audio_encoding)
        )
            
        # Perform the text-to-speech request
        gcp_request = texttospeech_v1beta1.SynthesizeSpeechRequest(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config,
            enable_time_pointing=[
                texttospeech_v1beta1.SynthesizeSpeechRequest.TimepointType.SSML_MARK
            ] if request.enable_time_pointing else []
        )
        
        # Perform the text-to-speech request
        response = client.synthesize_speech(request=gcp_request)
                
        # Extract word timestamps if available
        word_timings = []
        if request.enable_time_pointing and hasattr(response, 'timepoints'):
            word_timings = gcp_config.extract_word_timestamps(
                response.timepoints, word_marks, request.text, filter_ssml_tags=request.is_ssml
            )
        
        # Generate a unique filename based on text hash and timestamp
        text_hash = hashlib.md5(request.text.encode()).hexdigest()[:8]
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tts_{timestamp}_{text_hash}.mp3"
        
        # Get the audio directory
        audio_dir = gcp_config.get_audio_directory()
        file_path = os.path.join(audio_dir, filename)
        
        # Write the response to the output file
        with open(file_path, "wb") as out:
            out.write(response.audio_content)
        
        # Save timing information if available
        timing_filename = None
        if word_timings:
            timing_filename = f"timing_{timestamp}_{text_hash}.json"
            timing_file_path = os.path.join(audio_dir, timing_filename)
            with open(timing_file_path, "w") as f:
                json.dump({
                    "text": request.text,
                    "word_timings": word_timings,
                    "audio_file": filename
                }, f, indent=2)
            
        return {
            "status": "success",
            "message": "Audio synthesized successfully",
            "filename": filename,
            "text_length": len(request.text),
            "language": request.language_code,
            "voice": request.voice_name,
            "word_timings": word_timings,
            "timing_filename": timing_filename
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {str(e)}")


@router.get("/download/{filename}")
def download_audio(filename: str):
    """
    Download an audio file by filename
    """
    try:
        audio_dir = gcp_config.get_audio_directory()
        file_path = os.path.join(audio_dir, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        return FileResponse(
            path=file_path,
            media_type="audio/mpeg",
            filename=filename
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.get("/timing/{filename}")
def download_timing(filename: str):
    """
    Download a timing JSON file by filename
    """
    try:
        audio_dir = gcp_config.get_audio_directory()
        # Convert audio filename to timing filename
        if filename.startswith("tts_"):
            timing_filename = filename.replace("tts_", "timing_").replace(".mp3", ".json")
        else:
            timing_filename = filename
            
        file_path = os.path.join(audio_dir, timing_filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Timing file not found")
        
        return FileResponse(
            path=file_path,
            media_type="application/json",
            filename=timing_filename
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.get("/list")
def list_files() -> Dict[str, Any]:
    """
    List all available audio and timing files
    """
    try:
        audio_dir = gcp_config.get_audio_directory()
        
        if not os.path.exists(audio_dir):
            return {"audio_files": [], "timing_files": []}
        
        files = os.listdir(audio_dir)
        audio_files = [f for f in files if f.endswith('.mp3')]
        timing_files = [f for f in files if f.endswith('.json')]
        
        return {
            "audio_files": sorted(audio_files, reverse=True),  # Most recent first
            "timing_files": sorted(timing_files, reverse=True),
            "total_audio": len(audio_files),
            "total_timing": len(timing_files)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"List files failed: {str(e)}")
