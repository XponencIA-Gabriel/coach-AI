
import sys
import os
from dotenv import load_dotenv

# Add the current directory to path so we can import ai
sys.path.append(os.getcwd())

from ai.gemini_client import GeminiClient
from config import Config

def test_gemini():
    print("Testing Gemini configuration...")
    try:
        # Check if API key is set
        if not Config.GEMINI_API_KEY:
            print("Error: GEMINI_API_KEY not found in environment.")
            return

        client = GeminiClient()
        print(f"Using model: {client.CACHE_MODEL}")
        
        test_prompt = "Hola, eres el Coach AI? Responde brevemente para confirmar que funcionas."
        print(f"Sending prompt: '{test_prompt}'")
        
        response = client.generate_response(test_prompt)
        print("\nResponse from Gemini:")
        print("-" * 20)
        print(response)
        print("-" * 20)
        
        if "Error" in response:
            print("Test FAILED.")
        else:
            print("Test SUCCESSFUL.")
            
    except Exception as e:
        print(f"An error occurred during testing: {e}")

if __name__ == "__main__":
    test_gemini()
