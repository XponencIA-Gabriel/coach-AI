"""Manejo de audio para el bot de Telegram"""
import os
import tempfile
import asyncio
from pydub import AudioSegment
import speech_recognition as sr
from gtts import gTTS
from config import Config
from integrations.elevenlabs import ElevenLabsClient
import uuid
import threading
import traceback
import logging

logger = logging.getLogger(__name__)

# Evitar garbage collection de pyttsx3 y serializar su ejecución para prevenir errores de weakref/threading
_pyttsx3_engine = None
_pyttsx3_lock = threading.Lock()

class AudioHandler:
    """Maneja la conversión y procesamiento de audio"""
    
    def __init__(self):
        self.temp_dir = Config.AUDIO_TEMP_DIR
        self.max_duration = Config.MAX_AUDIO_DURATION
        self.recognizer = sr.Recognizer()
        self.elevenlabs = ElevenLabsClient()
        
        # Crear directorio temporal si no existe
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Verificar que ffmpeg esté disponible (necesario para pitch/reverb con pydub)
        from pydub.utils import which as pydub_which
        ffmpeg_path = pydub_which('ffmpeg')
        if ffmpeg_path:
            logger.info(f"[AudioHandler] ffmpeg encontrado en: {ffmpeg_path}")
            print(f"[AudioHandler] ffmpeg encontrado en: {ffmpeg_path}")
        else:
            logger.warning("[AudioHandler] ⚠️  ffmpeg NO encontrado en PATH. Los efectos de pitch/reverb en MP3 no funcionarán.")
            print("[AudioHandler] ⚠️  ffmpeg NO encontrado en PATH. Los efectos de pitch/reverb en MP3 no funcionarán.")
    
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
        Convierte texto a voz usando ElevenLabs (si está configurado) o fallbacks
        
        Orden: 1. ElevenLabs, 2. pyttsx3 (si habilitado), 3. Edge TTS, 4. gTTS
        Los efectos de pitch/reverb se aplican en todos los motores excepto para ElevenLabs que tiene su propio pitch.
        """
        # Limitar la longitud del texto
        max_length = 5000
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        # 1. Intentar con ElevenLabs
        if use_elevenlabs and self.elevenlabs.is_configured():
            try:
                audio_path = await self.elevenlabs.text_to_speech(text)
                if audio_path:
                    # Aplicar efectos para hacer la voz aún más masculina, grave y con eco/reverb
                    try:
                        loop = asyncio.get_event_loop()
                        def _apply_effects_elevenlabs():
                            sound = AudioSegment.from_file(audio_path)
                            # Bajar el tono (ideal para una voz masculina pre-made para hacerla grave sin distorsionar)
                            sound_deep = self._change_pitch(sound, Config.AUDIO_PITCH_ELEVENLABS)
                            # Añadir reverb
                            sound_final = self._add_reverb(
                                sound_deep, 
                                delay_ms=Config.AUDIO_REVERB_DELAY_MS, 
                                decay_db=Config.AUDIO_REVERB_DECAY_DB, 
                                reflections=Config.AUDIO_REVERB_REFLECTIONS
                            )
                            sound_final.export(audio_path, format="mp3")
                        
                        await loop.run_in_executor(None, _apply_effects_elevenlabs)
                    except Exception as audio_err:
                        logger.error(f"[AudioHandler] Error aplicando efectos a ElevenLabs: {audio_err}\n{traceback.format_exc()}")
                        print(f"Error aplicando efectos a ElevenLabs: {audio_err}")
                        
                    return audio_path
                print("ElevenLabs falló, intentando siguiente fallback")
            except Exception as e:
                print(f"Error con ElevenLabs: {e}")
        
        # 2. Intentar con pyttsx3 (Voces del sistema) si está habilitado
        if Config.PYTTSX3_ENABLED:
            try:
                import pyttsx3
                audio_filename = f"pyttsx3_{uuid.uuid4().hex[:8]}.wav"
                audio_path = os.path.join(self.temp_dir, audio_filename)
                
                # Ejecutar pyttsx3 en un hilo separado ya que es síncrono y bloqueante
                def _run_pyttsx3():
                    global _pyttsx3_engine
                    with _pyttsx3_lock:
                        if _pyttsx3_engine is None:
                            _pyttsx3_engine = pyttsx3.init()
                        engine = _pyttsx3_engine
                        voices = engine.getProperty('voices')
                        # Intentar seleccionar la voz configurada
                        if Config.PYTTSX3_VOICE_INDEX < len(voices):
                            engine.setProperty('voice', voices[Config.PYTTSX3_VOICE_INDEX].id)
                        
                        engine.save_to_file(text, audio_path)
                        engine.runAndWait()
                
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, _run_pyttsx3)
                
                if os.path.exists(audio_path):
                    # Aplicar efectos para hacer la voz masculina, grave y con eco/reverb
                    try:
                        def _apply_effects():
                            sound = AudioSegment.from_file(audio_path)
                            # Bajar tono (baja la voz femenina a registro de hombre y la ralentiza)
                            sound_masculine = self._change_pitch(sound, Config.AUDIO_PITCH_FALLBACK)
                            # Añadir reverb/presencia espacial
                            sound_final = self._add_reverb(
                                sound_masculine, 
                                delay_ms=Config.AUDIO_REVERB_DELAY_MS, 
                                decay_db=Config.AUDIO_REVERB_DECAY_DB, 
                                reflections=Config.AUDIO_REVERB_REFLECTIONS
                            )
                            sound_final.export(audio_path, format="wav")
                        
                        await loop.run_in_executor(None, _apply_effects)
                    except Exception as audio_err:
                        logger.error(f"[AudioHandler] Error aplicando efectos a pyttsx3: {audio_err}\n{traceback.format_exc()}")
                        print(f"Error procesando efectos de audio local: {audio_err}")
                    
                    return audio_path
                print("pyttsx3 no generó el archivo, intentando gTTS")
            except Exception as e:
                print(f"Error con pyttsx3: {e}")
        
        # 3. Fallback final a Edge-TTS / gTTS
        return await self._text_to_speech_fallback(text, language, slow)
    
    async def _text_to_speech_fallback(self, text: str, language: str = "es", slow: bool = False) -> str:
        """
        Convierte texto a voz usando Edge-TTS (voces neuronales masculinas) o gTTS como último recurso.
        """
        audio_filename = f"tts_{uuid.uuid4().hex[:8]}.mp3"
        audio_path = os.path.join(self.temp_dir, audio_filename)
        
        try:
            # Intentar primero con Edge TTS (voz masculina realista)
            import edge_tts
            
            # Seleccionar voz según el dialecto configurado
            dialect = Config.COACH_DIALECT
            if dialect == "argentino":
                voice = "es-AR-TomasNeural"
            elif dialect == "españa":
                voice = "es-ES-AlvaroNeural"
            else:
                voice = "es-MX-JorgeNeural"  # Fallback a neutro
                
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(audio_path)
            
            # Opcional: aplicar los mismos efectos de eco/grave
            try:
                loop = asyncio.get_event_loop()
                def _apply_effects():
                    sound = AudioSegment.from_file(audio_path)
                    sound_deep = self._change_pitch(sound, Config.AUDIO_PITCH_FALLBACK)
                    sound_final = self._add_reverb(
                        sound_deep, 
                        delay_ms=Config.AUDIO_REVERB_DELAY_MS, 
                        decay_db=Config.AUDIO_REVERB_DECAY_DB, 
                        reflections=Config.AUDIO_REVERB_REFLECTIONS
                    )
                    sound_final.export(audio_path, format="mp3")
                await loop.run_in_executor(None, _apply_effects)
            except Exception as eff_err:
                logger.error(f"[AudioHandler] Error aplicando efectos a Edge-TTS: {eff_err}\n{traceback.format_exc()}")
                print(f"Error aplicando efectos a Edge-TTS: {eff_err}")
                
            return audio_path
        except Exception as e:
            print(f"Error con Edge-TTS: {e}. Usando voz de robot mujer (gTTS)...")
            try:
                # Fallback final y seguro a gTTS
                tts = gTTS(text=text, lang=language[:2], slow=slow)
                tts.save(audio_path)
                return audio_path
            except Exception as e2:
                raise Exception(f"Error en el fallback definitivo: {str(e2)}")
    
    async def convert_to_ogg(self, audio_path: str) -> str:
        """
        Convierte un archivo de audio (MP3, WAV, etc.) a OGG (formato preferido por Telegram)
        
        Args:
            audio_path: Ruta del archivo de audio original
        
        Returns:
            Ruta del archivo OGG convertido
        """
        try:
            # from_file detecta automáticamente si es WAV, MP3, etc.
            audio = AudioSegment.from_file(audio_path)
            ogg_path = audio_path.rsplit('.', 1)[0] + '.ogg'
            audio.export(ogg_path, format="ogg")
            return ogg_path
        except Exception as e:
            raise Exception(f"Error convirtiendo audio a OGG: {str(e)}")

    async def convert_mp3_to_ogg(self, mp3_path: str) -> str:
        """Mantiene compatibilidad con el código que llama a convert_mp3_to_ogg"""
        return await self.convert_to_ogg(mp3_path)

    def _change_pitch(self, sound: AudioSegment, octaves: float) -> AudioSegment:
        """Modifica el tono del audio (valores negativos lo hacen más grave)"""
        new_sample_rate = int(sound.frame_rate * (2.0 ** octaves))
        shifted = sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate})
        return shifted.set_frame_rate(sound.frame_rate)

    def _add_reverb(self, sound: AudioSegment, delay_ms: int = 45, decay_db: int = 6, reflections: int = 4) -> AudioSegment:
        """Simula un eco de sala o reverb mezclando reflejos atenuados"""
        reverb = sound
        for i in range(1, reflections + 1):
            delay = AudioSegment.silent(duration=delay_ms * i, frame_rate=sound.frame_rate)
            reflected = delay + (sound - (decay_db * i))
            reverb = reverb.overlay(reflected)
        return reverb

