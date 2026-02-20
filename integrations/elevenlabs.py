"""Integración con ElevenLabs para síntesis de voz de alta calidad"""
import os
import aiohttp
import uuid
from typing import Optional
from config import Config


class ElevenLabsClient:
    """Cliente para la API de ElevenLabs"""
    
    BASE_URL = "https://api.elevenlabs.io/v1"
    
    def __init__(self):
        self.api_key = Config.ELEVENLABS_API_KEY
        self.voice_id = Config.ELEVENLABS_VOICE_ID
        self.model_id = Config.ELEVENLABS_MODEL_ID
        self.temp_dir = Config.AUDIO_TEMP_DIR
        
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def is_configured(self) -> bool:
        """Verifica si ElevenLabs está configurado"""
        return bool(self.api_key and self.voice_id)
    
    async def text_to_speech(
        self,
        text: str,
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        style: float = 0.0,
        use_speaker_boost: bool = True
    ) -> Optional[str]:
        """
        Convierte texto a voz usando ElevenLabs
        
        Args:
            text: Texto a convertir
            stability: Estabilidad de la voz (0-1)
            similarity_boost: Similitud con la voz original (0-1)
            style: Estilo de la voz (0-1)
            use_speaker_boost: Mejora la calidad del speaker
        
        Returns:
            Ruta del archivo de audio generado o None si falla
        """
        if not self.is_configured():
            return None
        
        url = f"{self.BASE_URL}/text-to-speech/{self.voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        payload = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
                "style": style,
                "use_speaker_boost": use_speaker_boost
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        audio_filename = f"elevenlabs_{uuid.uuid4().hex[:8]}.mp3"
                        audio_path = os.path.join(self.temp_dir, audio_filename)
                        
                        with open(audio_path, "wb") as f:
                            f.write(await response.read())
                        
                        return audio_path
                    else:
                        error_text = await response.text()
                        print(f"Error ElevenLabs ({response.status}): {error_text}")
                        return None
        except Exception as e:
            print(f"Error en ElevenLabs TTS: {e}")
            return None
    
    async def get_voices(self) -> list:
        """Obtiene la lista de voces disponibles"""
        if not self.api_key:
            return []
        
        url = f"{self.BASE_URL}/voices"
        headers = {"xi-api-key": self.api_key}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("voices", [])
                    return []
        except Exception as e:
            print(f"Error obteniendo voces: {e}")
            return []
    
    async def get_user_info(self) -> Optional[dict]:
        """Obtiene información del usuario y uso de la API"""
        if not self.api_key:
            return None
        
        url = f"{self.BASE_URL}/user"
        headers = {"xi-api-key": self.api_key}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except Exception as e:
            print(f"Error obteniendo info de usuario: {e}")
            return None
