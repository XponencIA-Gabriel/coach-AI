"""Sistema de notificaciones push con Telegram"""
from telegram import Bot
from config import Config
import asyncio
from datetime import datetime

class NotificationService:
    """Servicio para enviar notificaciones push a través de Telegram"""
    
    def __init__(self):
        self.bot_token = Config.TELEGRAM_BOT_TOKEN
        self.chat_id = Config.TELEGRAM_CHAT_ID
        self.bot = None
        
        if self.bot_token:
            self.bot = Bot(token=self.bot_token)
    
    async def send_notification(self, message: str, priority: str = "normal") -> bool:
        """
        Envía una notificación push
        
        Args:
            message: Mensaje a enviar
            priority: Prioridad (low, normal, high, urgent)
        
        Returns:
            True si se envió correctamente
        """
        if not self.bot or not self.chat_id:
            print("⚠️  Notificaciones no configuradas")
            return False
        
        try:
            # Agregar emoji según prioridad
            emoji_map = {
                "low": "🔔",
                "normal": "📢",
                "high": "⚠️",
                "urgent": "🚨"
            }
            emoji = emoji_map.get(priority, "📢")
            
            formatted_message = f"{emoji} {message}"
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=formatted_message
            )
            return True
        except Exception as e:
            print(f"Error enviando notificación: {e}")
            return False
    
    async def send_reminder(self, task: str, due_time: str) -> bool:
        """
        Envía un recordatorio de tarea
        
        Args:
            task: Descripción de la tarea
            due_time: Hora de vencimiento
        
        Returns:
            True si se envió correctamente
        """
        message = f"⏰ Recordatorio: {task}\n🕐 Vence: {due_time}"
        return await self.send_notification(message, priority="high")
    
    async def send_calendar_reminder(self, event_summary: str, event_time: str) -> bool:
        """
        Envía un recordatorio de evento del calendario
        
        Args:
            event_summary: Título del evento
            event_time: Hora del evento
        
        Returns:
            True si se envió correctamente
        """
        message = f"📅 Próximo evento: {event_summary}\n🕐 Hora: {event_time}"
        return await self.send_notification(message, priority="normal")
    
    async def send_voice_message(self, audio_path: str, caption: str = "") -> bool:
        """
        Envía un mensaje de voz como notificación
        
        Args:
            audio_path: Ruta del archivo de audio
            caption: Texto opcional
        
        Returns:
            True si se envió correctamente
        """
        if not self.bot or not self.chat_id:
            return False
        
        try:
            with open(audio_path, 'rb') as audio_file:
                await self.bot.send_voice(
                    chat_id=self.chat_id,
                    voice=audio_file,
                    caption=caption
                )
            return True
        except Exception as e:
            print(f"Error enviando mensaje de voz: {e}")
            return False

