from google import genai
import os

class GeminiConfig:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is nott set")
        self.client = genai.Client(api_key=api_key)
        
    def generate_content(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        if not response or not response.text:
            raise ValueError("No content generated from Gemini model")
        return response.text