"""Cliente para Google Gemini API con Context Caching"""
import google.generativeai as genai
from google.generativeai import caching
import datetime
from typing import Optional
from config import Config
from ai.prompts import SYSTEM_PROMPT, build_dynamic_prompt, build_full_prompt, build_audio_prompt


class GeminiClient:
    """Cliente para interactuar con Google Gemini con soporte de Context Caching"""
    
    # Modelo compatible con caching (debe ser estable, no latest)
    CACHE_MODEL = "models/gemini-3-flash-preview"
    
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(self.CACHE_MODEL)
        self.cached_model: Optional[genai.GenerativeModel] = None
        self.cache: Optional[caching.CachedContent] = None

    
    def create_cache(self, content: str, display_name: str = "coach-context", ttl_minutes: int = 60) -> bool:
        """
        Crea un cache con el contenido proporcionado
        
        Args:
            content: Contenido a cachear (documentos, contexto, etc.)
            display_name: Nombre identificador del cache
            ttl_minutes: Tiempo de vida del cache en minutos
        
        Returns:
            True si el cache se creó exitosamente
        """
        try:
            # Eliminar cache anterior si existe
            self.delete_cache()
            
            # Crear nuevo cache (incluye SYSTEM_PROMPT + documentos)
            self.cache = caching.CachedContent.create(
                model=self.CACHE_MODEL,
                display_name=display_name,
                system_instruction=SYSTEM_PROMPT,
                contents=[content],
                ttl=datetime.timedelta(minutes=ttl_minutes)
            )
            
            # Crear modelo que usa el cache
            self.cached_model = genai.GenerativeModel.from_cached_content(self.cache)
            
            print(f"Cache creado: {self.cache.name} (expira en {ttl_minutes} min)")
            return True
            
        except Exception as e:
            print(f"Error creando cache: {e}")
            return False
    
    def delete_cache(self):
        """Elimina el cache actual si existe"""
        if self.cache:
            try:
                self.cache.delete()
                print(f"Cache eliminado: {self.cache.name}")
            except Exception as e:
                print(f"Error eliminando cache: {e}")
            finally:
                self.cache = None
                self.cached_model = None
    
    def refresh_cache(self, additional_minutes: int = 30):
        """Extiende el TTL del cache actual"""
        if self.cache:
            try:
                self.cache.update(ttl=datetime.timedelta(minutes=additional_minutes))
                print(f"Cache extendido por {additional_minutes} minutos")
            except Exception as e:
                print(f"Error extendiendo cache: {e}")
    
    def get_cache_info(self) -> Optional[dict]:
        """Retorna información del cache actual"""
        if self.cache:
            return {
                "name": self.cache.name,
                "display_name": self.cache.display_name,
                "model": self.cache.model,
                "expire_time": str(self.cache.expire_time),
                "usage_metadata": self.cache.usage_metadata
            }
        return None
    
    def generate_response(self, prompt: str, context: str = "") -> str:
        """
        Genera una respuesta usando Gemini (con cache si está disponible)
        
        Args:
            prompt: El mensaje del usuario
            context: Contexto adicional dinámico (tareas, eventos, etc.)
        
        Returns:
            Respuesta generada por Gemini
        """
        try:
            # Usar modelo con cache si está disponible
            if self.cached_model:
                full_prompt = build_dynamic_prompt(prompt, context)
                response = self.cached_model.generate_content(full_prompt)
            else:
                full_prompt = build_full_prompt(prompt, context)
                response = self.model.generate_content(full_prompt)
            
            return response.text
            
        except Exception as e:
            return f"Error al generar respuesta: {str(e)}"
    
    def process_audio_transcription(self, transcription: str) -> str:
        """Procesa una transcripción de audio y genera una respuesta"""
        return self.generate_response(build_audio_prompt(transcription))
    
    @staticmethod
    def list_all_caches() -> list:
        """Lista todos los caches existentes"""
        try:
            return list(caching.CachedContent.list())
        except Exception as e:
            print(f"Error listando caches: {e}")
            return []
