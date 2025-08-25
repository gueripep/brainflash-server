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

    def delete_blob(self, bucket_name: str, blob_name: str) -> dict:
        """
        Delete a blob from a Google Cloud Storage bucket.

        Returns a dict with status information. Example:
        {"status": "deleted", "bucket": <bucket_name>, "blob": <blob_name>}
        or
        {"status": "error", "message": <error message>}
        """
        try:
            client = self.get_storage_client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            blob.delete()
            return {"status": "deleted", "bucket": bucket_name, "blob": blob_name}
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
        print(f"Converting text to SSML: {text}")
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

        print(f"Generated SSML: {ssml}")
        return ssml, word_marks
    
    def ssml_to_ssml_with_marks(self, ssml_text: str) -> tuple[str, List[str]]:
        """
        Add mark tags to existing SSML content before each word, preserving SSML structure.
        Returns the modified SSML string and a list of word marks.
        """
        print(f"Adding marks to existing SSML: {ssml_text}")
        
        # Remove markdown code block markers if present
        cleaned_text = ssml_text.strip()
        if cleaned_text.startswith('```xml'):
            cleaned_text = cleaned_text[6:].strip()
        if cleaned_text.endswith('```'):
            cleaned_text = cleaned_text[:-3].strip()
        
        # Remove any existing <speak> tags to get the inner content
        inner_content = cleaned_text.strip()
        if inner_content.startswith('<speak>'):
            inner_content = inner_content[7:]  # Remove opening <speak>
        if inner_content.endswith('</speak>'):
            inner_content = inner_content[:-8]  # Remove closing </speak>
        
        word_marks = []
        word_index = 0
        
        # Process the SSML content and insert marks before words
        # This regex finds text content outside of SSML tags
        def add_marks_to_text(match):
            nonlocal word_index
            text_segment = match.group(0).strip()
            if not text_segment:  # Skip empty matches
                return text_segment
                
            words_in_segment = re.findall(r'\S+', text_segment)
            
            marked_words = []
            for word in words_in_segment:
                mark_name = f"word_{word_index}"
                word_marks.append(mark_name)
                marked_words.append(f'<mark name="{mark_name}"/>{word}')
                word_index += 1
            
            return ' '.join(marked_words)
        
        # Split content by tags and process text parts
        # This regex matches text that is not inside angle brackets
        marked_content = re.sub(r'(?<=>)[^<]+(?=<)|(?<=>)[^<]+$|^[^<]+(?=<)', add_marks_to_text, inner_content)
        
        # Wrap in speak tags
        ssml = f'<speak>{marked_content}</speak>'
        
        print(f"Generated marked SSML: {ssml}")
        return ssml, word_marks

    def prepare_ssml_with_marks(self, text: str, is_ssml: bool) -> tuple[str, List[str]]:
        """
        Prepare SSML with marks, automatically detecting if input is plain text or SSML.
        Returns the SSML string and a list of word marks.
        """
        if is_ssml:
            return self.ssml_to_ssml_with_marks(text)
        else:
            return self.text_to_ssml_with_marks(text)
    
    def extract_word_timestamps(self, timing_info, word_marks: List[str], original_text, filter_ssml_tags: bool = False) -> List[Dict]:
        """
        Extract word timestamps from TTS timing information.
        """
        word_timings = []
        
        # Extract words from original text to match with indices
        if filter_ssml_tags:
            # Remove SSML tags and extract only actual words
            text_without_tags = re.sub(r'<[^>]+>', '', original_text)
            words = re.findall(r'\S+', text_without_tags)
        else:
            words = re.findall(r'\S+', original_text)

        print(timing_info)
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
                        "can": None  # We'd need next mark to calculate duration
                    })
            
            # Calculate durations
            for i in range(len(word_timings) - 1):
                word_timings[i]["duration"] = word_timings[i + 1]["start_time"] - word_timings[i]["start_time"]
        
        return word_timings

# Global config instance
gcp_config = GCPConfig()
