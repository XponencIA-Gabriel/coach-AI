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
    _gemini_keys_str = os.getenv("GEMINI_API_KEYS", os.getenv("GEMINI_API_KEY", ""))
    GEMINI_API_KEYS = [k.strip() for k in _gemini_keys_str.split(",") if k.strip()]
    GEMINI_API_KEY = GEMINI_API_KEYS[0] if GEMINI_API_KEYS else None
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")
    
    # OpenRouter Fallback
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    _models_str = os.getenv("OPENROUTER_MODELS", "anthropic/claude-3.5-sonnet")
    OPENROUTER_MODELS = [m.strip() for m in _models_str.split(",") if m.strip()]
    
    # IA y Comportamiento
    COACH_DIALECT = os.getenv("COACH_DIALECT", "argentino").lower()  # Opciones: argentino, neutro, españa
    
    # Integraciones y Bases de Datos
    NOTION_API_KEY = os.getenv("NOTION_API_KEY")
    NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")  # Tareas Laborales
    NOTION_PERSONAL_DB_ID = os.getenv("NOTION_PERSONAL_DB_ID")  # Tareas Personales
    NOTION_NOTES_DB_ID = os.getenv("NOTION_NOTES_DB_ID")  # Notas
    NOTION_PROJECTS_DB_ID = os.getenv("NOTION_PROJECTS_DB_ID")  # Proyectos
    NOTION_HABITS_DB_ID = os.getenv("NOTION_HABITS_DB_ID")  # Hábitos
    NOTION_MAPA_GUERRA_ID = os.getenv("NOTION_MAPA_GUERRA_ID")  # Mapa de Guerra
    NOTION_HOURLY_TRACKING_DB_ID = os.getenv("NOTION_HOURLY_TRACKING_DB_ID")  # Seguimiento Horario Coach
    NOTION_CHALLENGES_DB_ID = os.getenv("NOTION_CHALLENGES_DB_ID")  # Desafíos de Rendición de Cuentas


    
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
    PYTTSX3_ENABLED = os.getenv("PYTTSX3_ENABLED", "false").lower() == "true"
    PYTTSX3_VOICE_INDEX = int(os.getenv("PYTTSX3_VOICE_INDEX", "0"))
    
    # Audio Effects (Pitch and Reverb)
    AUDIO_PITCH_ELEVENLABS = float(os.getenv("AUDIO_PITCH_ELEVENLABS", "-0.2"))
    AUDIO_PITCH_FALLBACK = float(os.getenv("AUDIO_PITCH_FALLBACK", os.getenv("AUDIO_PITCH_PYTTSX3", "-0.35")))  # Pitch para Edge TTS y pyttsx3
    AUDIO_REVERB_DELAY_MS = int(os.getenv("AUDIO_REVERB_DELAY_MS", "45"))
    AUDIO_REVERB_DECAY_DB = int(os.getenv("AUDIO_REVERB_DECAY_DB", "6"))
    AUDIO_REVERB_REFLECTIONS = int(os.getenv("AUDIO_REVERB_REFLECTIONS", "4"))
    
    # Proactive Messaging
    PROACTIVE_MESSAGING_ENABLED = os.getenv("PROACTIVE_MESSAGING_ENABLED", "false").lower() == "true"
    PROACTIVE_CHECK_INTERVAL_MINUTES = int(os.getenv("PROACTIVE_CHECK_INTERVAL_MINUTES", "60"))
    
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
        
        if cls.PROACTIVE_MESSAGING_ENABLED and not cls.TELEGRAM_CHAT_ID:
            print("⚠️ ADVERTENCIA: Mensajes proactivos habilitados pero TELEGRAM_CHAT_ID no configurado.")
        
        return True

