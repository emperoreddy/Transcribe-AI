import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()
response = client.with_raw_response.models.list()
project_id = response.headers.get("openai-project")
print(f"Project ID tied to this API Key: {project_id}")
