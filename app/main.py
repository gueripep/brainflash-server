import os
from typing import Union
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import hashlib
import datetime
from google.cloud import texttospeech_v1beta1
from gcp_config import gcp_config

app = FastAPI(
    title="BrainFlash TTS Server",
    description="A text-to-speech server using Google Cloud TTS",
    version="1.0.0"
)

@app.get("/")
def read_root():
    """
    Root endpoint - returns basic information about the API
    """
    return {
        "message": "Welcome to BrainFlash TTS Server",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "gcp_test": "/gcp/test",
            "synthesize": "/tts/synthesize",
            "speak": "/tts/speak/{text}",
            "download": "/tts/download/{filename}",
            "timing": "/tts/timing/{filename}",
            "list_files": "/tts/list"
        }
    }

# Pydantic models for request validation
class TTSRequest(BaseModel):
    text: str
    language_code: str = "en-US"
    voice_name: str = "en-US-Wavenet-D"
    audio_encoding: str = "MP3"
    enable_time_pointing: bool = True  # Enable word-level timing


@app.post("/tts/synthesize")
def synthesize_speech(request: TTSRequest):
    """
    Convert text to speech using Google Cloud TTS and save the audio file
    """
    try:
        # Initialize the TTS client
        client = gcp_config.get_tts_client()
        
        # Convert text to SSML with word marks if timing is enabled
        if request.enable_time_pointing:
            ssml_text, word_marks = gcp_config.text_to_ssml_with_marks(request.text)
            synthesis_input = texttospeech_v1beta1.SynthesisInput(ssml=ssml_text)
        else:
            synthesis_input = texttospeech_v1beta1.SynthesisInput(text=request.text)
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
        response = client.synthesize_speech(
            request=gcp_request
        )
                
        # Extract word timestamps if available
        word_timings = []
        if request.enable_time_pointing and hasattr(response, 'timepoints'):
            word_timings = gcp_config.extract_word_timestamps(response.timepoints, word_marks, request.text)
        
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
        timing_file = None
        if word_timings:
            timing_filename = f"timing_{timestamp}_{text_hash}.json"
            timing_file = os.path.join(audio_dir, timing_filename)
            import json
            with open(timing_file, "w") as f:
                json.dump({
                    "text": request.text,
                    "word_timings": word_timings,
                    "audio_file": filename
                }, f, indent=2)
            
        return {
            "status": "success",
            "message": "Audio synthesized successfully",
            "filename": filename,
            "file_path": file_path,
            "text_length": len(request.text),
            "language": request.language_code,
            "voice": request.voice_name,
            "word_timings": word_timings,
            "timing_file": timing_file
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {str(e)}")