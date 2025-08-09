import os
from typing import Optional, List, Dict
import re
from google.cloud import storage
from google.cloud import texttospeech_v1beta1
from google.oauth2 import service_account

class GCPConfig:
    """Configuration for GCP services"""
    
    def __init__(self):
        self.service_account_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "gcp-service-account.json"
        )
        self.project_id = self._get_project_id()
    
    def _get_project_id(self) -> Optional[str]:
        """Extract project ID from service account file"""
        try:
            import json
            if os.path.exists(self.service_account_path):
                with open(self.service_account_path, 'r') as f:
                    data = json.load(f)
                    return data.get('project_id')
        except Exception:
            pass
        return None
    
    @property
    def has_service_account(self) -> bool:
        """Check if service account file exists"""
        return os.path.exists(self.service_account_path)
    
    def get_storage_client(self) -> storage.Client:
        """Initialize GCP Storage client using service account key"""
        if self.has_service_account:
            credentials = service_account.Credentials.from_service_account_file(self.service_account_path)
            client = storage.Client(credentials=credentials, project=self.project_id)
            return client
        else:
            # Fallback to default credentials (useful for production)
            return storage.Client()
    
    def get_tts_client(self) -> texttospeech_v1beta1.TextToSpeechClient:
        """Initialize GCP Text-to-Speech client using service account key"""
        if self.has_service_account:
            credentials = service_account.Credentials.from_service_account_file(self.service_account_path)
            client = texttospeech_v1beta1.TextToSpeechClient(credentials=credentials)
            return client
        else:
            # Fallback to default credentials (useful for production)
            return texttospeech_v1beta1.TextToSpeechClient()
    
    def test_connection(self) -> dict:
        """Test GCP connection"""
        try:
            client = self.get_storage_client()
            # Try to get project info
            project = client.project
            return {"status": "connected", "project": project}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_audio_directory(self) -> str:
        """Get the audio directory path for both local and Docker environments"""
        if os.path.exists("/code"):  # Docker environment
            audio_dir = "/code/audio"
        else:  # Local development - use host-audio directory
            audio_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "host-audio")
        
        # Ensure the audio directory exists
        os.makedirs(audio_dir, exist_ok=True)
        return audio_dir
    
    def text_to_ssml_with_marks(self, text: str) -> tuple[str, List[str]]:
        """
        Convert text to SSML with mark tags before each word.
        Returns the SSML string and a list of word marks.
        """
        # Split text into words, preserving punctuation
        words = re.findall(r'\S+', text)
        word_marks = []
        ssml_parts = ['<speak>']
        
        for i, word in enumerate(words):
            mark_name = f"word_{i}"
            word_marks.append(mark_name)
            ssml_parts.append(f'<mark name="{mark_name}"/>{word}')
        
        ssml_parts.append('</speak>')
        ssml = ' '.join(ssml_parts)
        
        return ssml, word_marks
    
    def extract_word_timestamps(self, timing_info, word_marks: List[str], original_text: str = "") -> List[Dict]:
        """
        Extract word timestamps from TTS timing information.
        """
        word_timings = []
        
        # Extract words from original text to match with indices
        words = re.findall(r'\S+', original_text) if original_text else []
        
        # The timing_info is a list of timepoints directly
        if timing_info:
            # Create a dictionary mapping mark names to timestamps
            mark_dict = {}
            for timepoint in timing_info:
                if hasattr(timepoint, 'mark_name') and hasattr(timepoint, 'time_seconds'):
                    mark_dict[timepoint.mark_name] = timepoint.time_seconds
            
            # Match the marks with the word marks we created
            for i, mark_name in enumerate(word_marks):
                if mark_name in mark_dict:
                    word_timings.append({
                        "word_index": i,
                        "word": words[i] if i < len(words) else f"word_{i}",
                        "start_time": mark_dict[mark_name],
                        "duration": None  # We'd need next mark to calculate duration
                    })
            
            # Calculate durations
            for i in range(len(word_timings) - 1):
                word_timings[i]["duration"] = word_timings[i + 1]["start_time"] - word_timings[i]["start_time"]
        
        return word_timings

# Global config instance
gcp_config = GCPConfig()
