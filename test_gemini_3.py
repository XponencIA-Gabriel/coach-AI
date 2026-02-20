
import sys
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

def test_gemini_3_flash():
    print("Testing Gemini 3 Flash Preview...")
    if not api_key:
        print("Error: GEMINI_API_KEY not found.")
        return

    genai.configure(api_key=api_key)
    model_name = "models/gemini-3-flash-preview"
    
    try:
        model = genai.GenerativeModel(model_name)
        prompt = "Hola! Soy un test para verificar que el modelo Gemini 3 Flash funciona correctamente. ¿Puedes confirmarme que estás activo y qué versión eres?"
        
        print(f"Sending prompt to {model_name}...")
        response = model.generate_content(prompt)
        
        print("\n--- Response ---")
        print(response.text)
        print("----------------")
        print("\nTest SUCCESSFUL!")
        
    except Exception as e:
        print(f"\nTest FAILED with error: {e}")

if __name__ == "__main__":
    test_gemini_3_flash()
