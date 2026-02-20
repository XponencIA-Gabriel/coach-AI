"""Configuración centralizada del Coach AI"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuración del sistema"""
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    
    # Gemini
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # Notion - Múltiples bases de datos
    NOTION_API_KEY = os.getenv("NOTION_API_KEY")
    NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")  # Tareas (principal)
    NOTION_NOTES_DB_ID = os.getenv("NOTION_NOTES_DB_ID")  # Notas
    NOTION_PROJECTS_DB_ID = os.getenv("NOTION_PROJECTS_DB_ID")  # Proyectos
    NOTION_HABITS_DB_ID = os.getenv("NOTION_HABITS_DB_ID")  # Hábitos
    
    # Google Calendar
    GOOGLE_CALENDAR_CREDENTIALS_PATH = os.getenv("GOOGLE_CALENDAR_CREDENTIALS_PATH", "credentials.json")
    GOOGLE_CALENDAR_TOKEN_PATH = os.getenv("GOOGLE_CALENDAR_TOKEN_PATH", "token.json")
    GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")
    
    # Clockify
    CLOCKIFY_API_KEY = os.getenv("CLOCKIFY_API_KEY")
    CLOCKIFY_WORKSPACE_ID = os.getenv("CLOCKIFY_WORKSPACE_ID")
    
    # Focusmate
    FOCUSMATE_API_KEY = os.getenv("FOCUSMATE_API_KEY")
    
    # Beeminder
    BEEMINDER_AUTH_TOKEN = os.getenv("BEEMINDER_AUTH_TOKEN")
    BEEMINDER_USERNAME = os.getenv("BEEMINDER_USERNAME")
    
    # RescueTime
    RESCUETIME_API_KEY = os.getenv("RESCUETIME_API_KEY")
    
    # ElevenLabs
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Rachel por defecto
    ELEVENLABS_MODEL_ID = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")
    
    # Audio
    AUDIO_TEMP_DIR = os.getenv("AUDIO_TEMP_DIR", "./temp_audio")
    MAX_AUDIO_DURATION = int(os.getenv("MAX_AUDIO_DURATION", "300"))
    
    # Documentos para Context Caching
    DOCUMENTS_DIR = os.getenv("DOCUMENTS_DIR", None)  # Directorio con documentos
    DOCUMENT_PATHS = os.getenv("DOCUMENT_PATHS", None)  # Rutas separadas por coma
    CACHE_TTL_MINUTES = int(os.getenv("CACHE_TTL_MINUTES", "60"))  # TTL del cache en minutos
    
    @classmethod
    def validate(cls):
        """Valida que las configuraciones esenciales estén presentes"""
        required = [
            ("TELEGRAM_BOT_TOKEN", cls.TELEGRAM_BOT_TOKEN),
            ("GEMINI_API_KEY", cls.GEMINI_API_KEY),
        ]
        
        missing = [name for name, value in required if not value]
        if missing:
            raise ValueError(f"Faltan configuraciones requeridas: {', '.join(missing)}")
        
        return True

