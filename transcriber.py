import os
from openai import OpenAI
from dotenv import load_dotenv

class CloudTranscriber:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "your_openai_api_key_here":
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)

    def load_model(self):
        # No model to load locally when using the Cloud API!
        pass

    def transcribe(self, audio_path):
        if not self.client:
            return "Error: OpenAI API Key is missing. Please set it in the .env file."
        
        try:
            with open(audio_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file,
                    response_format="text"
                )
            return transcript.strip()
        except Exception as e:
            return f"An error occurred during cloud transcription: {e}"
