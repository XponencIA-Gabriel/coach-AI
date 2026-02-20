"""Manejo de audio para el bot de Telegram"""
import os
import tempfile
from pydub import AudioSegment
import speech_recognition as sr
from gtts import gTTS
from config import Config
from integrations.elevenlabs import ElevenLabsClient
import uuid

class AudioHandler:
    """Maneja la conversión y procesamiento de audio"""
    
    def __init__(self):
        self.temp_dir = Config.AUDIO_TEMP_DIR
        self.max_duration = Config.MAX_AUDIO_DURATION
        self.recognizer = sr.Recognizer()
        self.elevenlabs = ElevenLabsClient()
        
        # Crear directorio temporal si no existe
        os.makedirs(self.temp_dir, exist_ok=True)
    
    async def download_audio(self, file_path: str, bot) -> str:
        """
        Descarga un archivo de audio de Telegram
        
        Args:
            file_path: Ruta del archivo en Telegram
            bot: Instancia del bot de Telegram
        
        Returns:
            Ruta local del archivo descargado
        """
        file = await bot.get_file(file_path)
        local_path = os.path.join(self.temp_dir, f"audio_{file_path.split('/')[-1]}")
        
        await file.download_to_drive(local_path)
        return local_path
    
    async def convert_to_wav(self, audio_path: str) -> str:
        """
        Convierte un archivo de audio a formato WAV
        
        Args:
            audio_path: Ruta del archivo de audio
        
        Returns:
            Ruta del archivo WAV convertido
        """
        try:
            audio = AudioSegment.from_file(audio_path)
            
            # Verificar duración
            duration_seconds = len(audio) / 1000.0
            if duration_seconds > self.max_duration:
                raise ValueError(f"El audio es demasiado largo ({duration_seconds}s > {self.max_duration}s)")
            
            # Convertir a WAV
            wav_path = audio_path.rsplit('.', 1)[0] + '.wav'
            audio.export(wav_path, format="wav")
            
            return wav_path
        except Exception as e:
            raise Exception(f"Error convirtiendo audio: {str(e)}")
    
    async def transcribe_audio(self, audio_path: str, language: str = "es-AR") -> str:
        """
        Transcribe un archivo de audio a texto
        
        Args:
            audio_path: Ruta del archivo de audio
            language: Idioma para la transcripción (default: español argentino)
        
        Returns:
            Texto transcrito
        """
        try:
            # Convertir a WAV si es necesario
            if not audio_path.endswith('.wav'):
                audio_path = await self.convert_to_wav(audio_path)
            
            with sr.AudioFile(audio_path) as source:
                audio_data = self.recognizer.record(source)
            
            # Intentar transcribir con Google Speech Recognition
            try:
                text = self.recognizer.recognize_google(audio_data, language=language)
                return text
            except sr.UnknownValueError:
                return "No se pudo entender el audio"
            except sr.RequestError as e:
                return f"Error en el servicio de reconocimiento: {str(e)}"
        
        except Exception as e:
            raise Exception(f"Error transcribiendo audio: {str(e)}")
    
    def cleanup(self, file_path: str):
        """Elimina un archivo temporal"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error eliminando archivo {file_path}: {e}")
    
    async def text_to_speech(
        self, 
        text: str, 
        language: str = "es", 
        slow: bool = False,
        use_elevenlabs: bool = True
    ) -> str:
        """
        Convierte texto a voz usando ElevenLabs (si está configurado) o gTTS como fallback
        
        Args:
            text: Texto a convertir a voz
            language: Idioma para la síntesis (default: español) - usado solo en gTTS
            slow: Si True, habla más lento - usado solo en gTTS
            use_elevenlabs: Si True, intenta usar ElevenLabs primero
        
        Returns:
            Ruta del archivo de audio generado
        """
        # Limitar la longitud del texto
        max_length = 5000
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        # Intentar con ElevenLabs primero si está habilitado y configurado
        if use_elevenlabs and self.elevenlabs.is_configured():
            try:
                audio_path = await self.elevenlabs.text_to_speech(text)
                if audio_path:
                    return audio_path
                print("ElevenLabs falló, usando gTTS como fallback")
            except Exception as e:
                print(f"Error con ElevenLabs: {e}, usando gTTS como fallback")
        
        # Fallback a gTTS
        return await self._text_to_speech_gtts(text, language, slow)
    
    async def _text_to_speech_gtts(self, text: str, language: str = "es", slow: bool = False) -> str:
        """
        Convierte texto a voz usando Google Text-to-Speech (fallback)
        
        Args:
            text: Texto a convertir a voz
            language: Idioma para la síntesis
            slow: Si True, habla más lento
        
        Returns:
            Ruta del archivo de audio generado
        """
        try:
            audio_filename = f"tts_{uuid.uuid4().hex[:8]}.mp3"
            audio_path = os.path.join(self.temp_dir, audio_filename)
            
            tts = gTTS(text=text, lang=language, slow=slow)
            tts.save(audio_path)
            
            return audio_path
        except Exception as e:
            raise Exception(f"Error generando audio desde texto: {str(e)}")
    
    async def convert_mp3_to_ogg(self, mp3_path: str) -> str:
        """
        Convierte un archivo MP3 a OGG (formato preferido por Telegram)
        
        Args:
            mp3_path: Ruta del archivo MP3
        
        Returns:
            Ruta del archivo OGG convertido
        """
        try:
            audio = AudioSegment.from_mp3(mp3_path)
            ogg_path = mp3_path.rsplit('.', 1)[0] + '.ogg'
            audio.export(ogg_path, format="ogg")
            return ogg_path
        except Exception as e:
            raise Exception(f"Error convirtiendo MP3 a OGG: {str(e)}")

