"""Bot principal de Telegram para el Coach AI"""
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import Config
from ai.coach_logic import CoachAI
from utils.audio_handler import AudioHandler
from utils.notifications import NotificationService
import logging
import os

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramBot:
    """Bot de Telegram para el Coach AI"""
    
    def __init__(self):
        self.token = Config.TELEGRAM_BOT_TOKEN
        self.coach = CoachAI()
        self.audio_handler = AudioHandler()
        self.notifications = NotificationService()
        self.application = None
        
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN no está configurado")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja el comando /start"""
        welcome_message = """🤖 ¡Hola! Soy tu Coach AI personal.

Puedo ayudarte con:
• 📝 Gestionar tareas en Notion
• 📅 Consultar y crear eventos en Google Calendar
• ⏱️ Monitorear tu tiempo con aTracker
• 💬 Responder tus preguntas y darte consejos
• 🎤 Procesar mensajes de voz

¡Escribe cualquier cosa o envía un audio para comenzar!"""
        
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja el comando /help"""
        help_text = """📚 Comandos disponibles:

/start - Iniciar el bot
/help - Mostrar esta ayuda
/tareas - Ver tareas pendientes de Notion
/eventos - Ver próximos eventos del calendario
/estadisticas - Ver estadísticas de tiempo de hoy (aTracker + RescueTime)
/productividad - Ver análisis detallado de productividad (RescueTime)
/crear_tarea <descripción> - Crear una nueva tarea
/crear_evento <título> <fecha> - Crear un evento

También puedes:
• Escribir mensajes normales para conversar
• Enviar audios que serán transcritos y procesados"""
        
        await update.message.reply_text(help_text)
    
    async def tareas_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja el comando /tareas"""
        try:
            tasks = await self.coach.notion.get_pending_tasks()
            if not tasks:
                await update.message.reply_text("✅ No tienes tareas pendientes en Notion.")
                return
            
            message = "📋 Tus tareas pendientes:\n\n"
            for i, task in enumerate(tasks[:10], 1):
                priority_emoji = {
                    "Alta": "🔴",
                    "Media": "🟡",
                    "Baja": "🟢"
                }.get(task.get('priority', 'Media'), "⚪")
                
                message += f"{i}. {priority_emoji} {task.get('title', 'Sin título')}\n"
            
            await update.message.reply_text(message)
        except Exception as e:
            await update.message.reply_text(f"❌ Error obteniendo tareas: {str(e)}")
    
    async def eventos_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja el comando /eventos"""
        try:
            events = await self.coach.calendar.get_upcoming_events(limit=10)
            if not events:
                await update.message.reply_text("📅 No tienes eventos próximos.")
                return
            
            message = "📅 Tus próximos eventos:\n\n"
            for event in events:
                summary = event.get('summary', 'Sin título')
                start = event.get('start', {})
                start_time = start.get('dateTime', start.get('date', 'N/A'))
                message += f"• {summary}\n  🕐 {start_time}\n\n"
            
            await update.message.reply_text(message)
        except Exception as e:
            await update.message.reply_text(f"❌ Error obteniendo eventos: {str(e)}")
    
    async def estadisticas_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja el comando /estadisticas"""
        try:
            # Obtener estadísticas de aTracker
            atracker_stats = await self.coach.atracker.get_today_stats()
            
            # Obtener estadísticas de RescueTime
            rescuetime_summary = await self.coach.rescuetime.get_today_summary()
            rescuetime_text = self.coach.rescuetime.format_summary_text(rescuetime_summary)
            
            # Combinar estadísticas
            message = "📊 Estadísticas de hoy:\n\n"
            
            if atracker_stats and "No hay datos" not in atracker_stats:
                message += f"⏱️ aTracker:\n{atracker_stats}\n\n"
            
            if rescuetime_text and "No hay datos" not in rescuetime_text:
                message += f"{rescuetime_text}"
            
            if message == "📊 Estadísticas de hoy:\n\n":
                message = "❌ No hay estadísticas disponibles en este momento."
            
            await update.message.reply_text(message)
        except Exception as e:
            await update.message.reply_text(f"❌ Error obteniendo estadísticas: {str(e)}")
    
    async def productividad_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja el comando /productividad - Muestra datos detallados de RescueTime"""
        try:
            # Obtener puntaje de productividad
            productivity = await self.coach.rescuetime.get_productivity_score()
            
            # Obtener actividades principales
            top_activities = await self.coach.rescuetime.get_top_activities(limit=5)
            
            message = "📈 Análisis de Productividad (RescueTime):\n\n"
            
            if productivity:
                score = productivity.get("average_score", 0)
                total_hours = productivity.get("total_hours", 0)
                
                # Interpretar el puntaje
                if score >= 1.5:
                    emoji = "🟢"
                    nivel = "Excelente"
                elif score >= 0.5:
                    emoji = "🟡"
                    nivel = "Buena"
                elif score >= -0.5:
                    emoji = "⚪"
                    nivel = "Neutral"
                elif score >= -1.5:
                    emoji = "🟠"
                    nivel = "Baja"
                else:
                    emoji = "🔴"
                    nivel = "Muy baja"
                
                message += f"{emoji} Puntaje promedio: {score:.2f} ({nivel})\n"
                message += f"⏱️ Tiempo total: {total_hours:.2f} horas\n\n"
            
            if top_activities:
                message += "🔝 Actividades principales:\n"
                for i, activity in enumerate(top_activities, 1):
                    prod_emoji = {
                        2: "🟢",
                        1: "🟡",
                        0: "⚪",
                        -1: "🟠",
                        -2: "🔴"
                    }.get(activity.get("productivity", 0), "•")
                    
                    message += f"{i}. {prod_emoji} {activity.get('name', 'Desconocido')}\n"
                    message += f"   ⏱️ {activity.get('time_hours', 0):.2f} horas\n"
            
            if message == "📈 Análisis de Productividad (RescueTime):\n\n":
                message = "❌ No hay datos de productividad disponibles."
            
            await update.message.reply_text(message)
        except Exception as e:
            await update.message.reply_text(f"❌ Error obteniendo productividad: {str(e)}")
    
    async def crear_tarea_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja el comando /crear_tarea"""
        if not context.args:
            await update.message.reply_text("❌ Uso: /crear_tarea <descripción de la tarea>")
            return
        
        task_description = " ".join(context.args)
        try:
            result = await self.coach.create_task(task_description)
            await update.message.reply_text(result)
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja mensajes de texto"""
        user_message = update.message.text
        user_id = update.message.from_user.id
        
        # Mostrar que está procesando
        await update.message.reply_chat_action("typing")
        
        try:
            # Procesar con el coach AI
            response = await self.coach.process_message(user_message, user_id)
            
            # Enviar respuesta en texto
            await update.message.reply_text(response)
            
            # Enviar respuesta en voz
            await self._send_voice_response(update, response)
            
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")
            await update.message.reply_text(f"❌ Lo siento, hubo un error: {str(e)}")
    
    async def _send_voice_response(self, update: Update, text: str):
        """Envía una respuesta como nota de voz"""
        try:
            # Mostrar que está generando audio
            await update.message.reply_chat_action("record_voice")
            
            # Generar audio desde el texto
            audio_path = await self.audio_handler.text_to_speech(text, language="es")
            
            # Convertir a OGG si es necesario (Telegram prefiere OGG)
            try:
                ogg_path = await self.audio_handler.convert_mp3_to_ogg(audio_path)
                audio_file_path = ogg_path
            except:
                # Si falla la conversión, usar el MP3 original
                audio_file_path = audio_path
            
            # Enviar el audio
            with open(audio_file_path, 'rb') as audio_file:
                await update.message.reply_voice(voice=audio_file)
            
            # Limpiar archivos temporales
            self.audio_handler.cleanup(audio_path)
            if audio_file_path != audio_path and os.path.exists(audio_file_path):
                self.audio_handler.cleanup(audio_file_path)
                
        except Exception as e:
            logger.error(f"Error enviando respuesta de voz: {e}")
            # No fallar si el audio falla, solo loguear el error
    
    async def handle_voice_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja mensajes de voz"""
        voice = update.message.voice
        user_id = update.message.from_user.id
        
        # Mostrar que está procesando
        await update.message.reply_chat_action("typing")
        
        try:
            # Descargar audio
            file_id = voice.file_id
            audio_path = await self.audio_handler.download_audio(file_id, context.bot)
            
            # Transcribir
            transcription = await self.audio_handler.transcribe_audio(audio_path)
            
            if not transcription or "No se pudo entender" in transcription:
                await update.message.reply_text("❌ No pude entender el audio. ¿Puedes intentar de nuevo?")
                self.audio_handler.cleanup(audio_path)
                return
            
            # Mostrar transcripción
            await update.message.reply_text(f"🎤 Escuché: {transcription}")
            
            # Procesar con el coach AI
            response = await self.coach.process_message(transcription, user_id)
            
            # Enviar respuesta en texto
            await update.message.reply_text(response)
            
            # Enviar respuesta en voz
            await self._send_voice_response(update, response)
            
            # Limpiar archivo temporal
            self.audio_handler.cleanup(audio_path)
            
        except Exception as e:
            logger.error(f"Error procesando audio: {e}")
            await update.message.reply_text(f"❌ Error procesando el audio: {str(e)}")
    
    def setup_handlers(self):
        """Configura los manejadores del bot"""
        # Comandos
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("tareas", self.tareas_command))
        self.application.add_handler(CommandHandler("eventos", self.eventos_command))
        self.application.add_handler(CommandHandler("estadisticas", self.estadisticas_command))
        self.application.add_handler(CommandHandler("productividad", self.productividad_command))
        self.application.add_handler(CommandHandler("crear_tarea", self.crear_tarea_command))
        
        # Mensajes de texto
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))
        
        # Mensajes de voz
        self.application.add_handler(MessageHandler(filters.VOICE, self.handle_voice_message))
    
    def run(self):
        """Inicia el bot"""
        self.application = Application.builder().token(self.token).build()
        self.setup_handlers()
        
        logger.info("🤖 Bot iniciado. Presiona Ctrl+C para detener.")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
