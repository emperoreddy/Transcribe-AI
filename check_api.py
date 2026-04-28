import os
from openai import OpenAI
from dotenv import load_dotenv

def check_whisper_access():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        print("Error: OpenAI API Key is missing in .env")
        return

    client = OpenAI(api_key=api_key)
    try:
        models = client.models.list()
        model_ids = [m.id for m in models.data]
        if "whisper-1" in model_ids:
            print("SUCCESS: Your API key HAS access to 'whisper-1'.")
        else:
            print("FAILURE: Your API key does NOT have access to 'whisper-1'.")
            print(f"Available models for this key: {sorted(model_ids)}")
    except Exception as e:
        print(f"Error checking models: {e}")

if __name__ == "__main__":
    check_whisper_access()
