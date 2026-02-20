
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
    try:
        with open("full_models_list.txt", "w") as f:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    f.write(f"{m.name}\n")
    except Exception as e:
        with open("full_models_list.txt", "w") as f:
            f.write(f"ERROR: {str(e)}")
