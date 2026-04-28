import os
import json
from openai import OpenAI
from dotenv import load_dotenv

class Summarizer:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "your_openai_api_key_here":
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)

    def summarize(self, text):
        if not self.client:
            return {"title": "Error", "summary": "Error: OpenAI API Key is missing or invalid. Please set it in the .env file."}
        
        if not text.strip():
            return {"title": "Error", "summary": "Error: No text provided to summarize."}

        prompt = f"""
You are an expert meeting assistant. Please read the following meeting transcript and generate a clear, concise summary.
Format your output as a JSON object with exactly two keys:
1. "title": A short, descriptive title for the meeting (e.g., "Q3 Marketing Sync" or "Project Kickoff"). Avoid special characters that can't be used in filenames.
2. "summary": The summary text formatted using markdown with the following sections:
- **Key Highlights**
- **Action Items**
- **Brief Summary**

Transcript:
{text}
"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-5.4-nano",
                response_format={ "type": "json_object" },
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes meetings. You always reply with a valid JSON object."},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=1000,
                temperature=0.5
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {"title": "Error", "summary": f"An error occurred during summarization: {e}"}
