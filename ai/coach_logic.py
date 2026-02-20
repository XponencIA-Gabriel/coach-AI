"""Lógica principal del Coach AI con Context Caching de Gemini"""
from ai.gemini_client import GeminiClient
from ai.document_context import DocumentLoader
from integrations.notion import NotionIntegration
from integrations.google_calendar import GoogleCalendarIntegration
from integrations.clockify import ClockifyIntegration
from integrations.rescuetime import RescueTimeIntegration
from config import Config


class CoachAI:
    """Lógica central del Coach AI con soporte de Context Caching"""
    
    def __init__(self):
        self.gemini = GeminiClient()
        self.notion = NotionIntegration()
        self.calendar = GoogleCalendarIntegration()
        self.atracker = ClockifyIntegration()
        self.rescuetime = RescueTimeIntegration()
        
        # Inicializar cargador de documentos
        document_paths = None
        documents_dir = None
        
        if Config.DOCUMENT_PATHS:
            document_paths = [p.strip() for p in Config.DOCUMENT_PATHS.split(',')]
        
        if Config.DOCUMENTS_DIR:
            documents_dir = Config.DOCUMENTS_DIR
        
        self.document_loader = DocumentLoader(
            document_paths=document_paths,
            documents_dir=documents_dir
        )
        
        # Inicializar cache con documentos si hay contenido
        self._initialize_cache()
    
    def _initialize_cache(self):
        """Inicializa el cache de Gemini con los documentos cargados"""
        content = self.document_loader.get_content_for_cache()
        if content:
            success = self.gemini.create_cache(
                content=content,
                display_name="coach-documents",
                ttl_minutes=Config.CACHE_TTL_MINUTES
            )
            if success:
                stats = self.document_loader.get_stats()
                print(f"Cache inicializado con {stats['total_documents']} documentos ({stats['total_characters']} caracteres)")

    
    def refresh_cache(self):
        """Recarga el cache con los documentos actuales"""
        content = self.document_loader.get_content_for_cache()
        if content:
            return self.gemini.create_cache(
                content=content,
                display_name="coach-documents",
                ttl_minutes=Config.CACHE_TTL_MINUTES
            )
        return False
    
    def add_document_to_cache(self, document_path: str):
        """Agrega un documento y recrea el cache"""
        self.document_loader.add_document(document_path)
        return self.refresh_cache()
    
    def get_cache_status(self) -> dict:
        """Retorna el estado actual del cache y documentos"""
        return {
            "cache_info": self.gemini.get_cache_info(),
            "documents": self.document_loader.get_stats()
        }
    
    async def process_message(self, user_message: str, user_id: int) -> str:
        """
        Procesa un mensaje del usuario y genera una respuesta contextual
        
        Args:
            user_message: Mensaje del usuario
            user_id: ID del usuario en Telegram
        
        Returns:
            Respuesta del coach AI
        """
        # Obtener contexto dinámico de las integraciones
        context = await self._gather_dynamic_context(user_id)
        
        # Generar respuesta con Gemini (usa cache automáticamente si está disponible)
        response = self.gemini.generate_response(user_message, context)
        
        return response
    
    async def _gather_dynamic_context(self, user_id: int) -> str:
        """Recopila contexto dinámico de las integraciones (no cacheado)"""
        context_parts = []
        
        try:
            tasks = await self.notion.get_pending_tasks()
            if tasks:
                context_parts.append(f"TAREAS PENDIENTES (Notion):\n{self._format_tasks(tasks)}")
        except Exception as e:
            context_parts.append(f"Error obteniendo tareas de Notion: {str(e)}")
        
        try:
            events = await self.calendar.get_upcoming_events(limit=5)
            if events:
                context_parts.append(f"PRÓXIMOS EVENTOS (Calendar):\n{self._format_events(events)}")
        except Exception as e:
            context_parts.append(f"Error obteniendo eventos: {str(e)}")
        
        try:
            time_stats = await self.atracker.get_today_stats()
            if time_stats:
                context_parts.append(f"ESTADÍSTICAS DE HOY (aTracker):\n{time_stats}")
        except Exception as e:
            context_parts.append(f"Error obteniendo estadísticas: {str(e)}")
        
        try:
            rescuetime_summary = await self.rescuetime.get_today_summary()
            if rescuetime_summary:
                formatted = self.rescuetime.format_summary_text(rescuetime_summary)
                context_parts.append(f"PRODUCTIVIDAD DE HOY (RescueTime):\n{formatted}")
        except Exception as e:
            context_parts.append(f"Error obteniendo datos de RescueTime: {str(e)}")
        
        return "\n\n".join(context_parts) if context_parts else ""
    
    def _format_tasks(self, tasks: list) -> str:
        """Formatea las tareas para el contexto"""
        if not tasks:
            return "No hay tareas pendientes."
        
        formatted = []
        for task in tasks[:10]:
            priority = task.get('priority', 'N/A')
            title = task.get('title', 'Sin título')
            formatted.append(f"- {title} (Prioridad: {priority})")
        
        return "\n".join(formatted)
    
    def _format_events(self, events: list) -> str:
        """Formatea los eventos para el contexto"""
        if not events:
            return "No hay eventos próximos."
        
        formatted = []
        for event in events:
            summary = event.get('summary', 'Sin título')
            start = event.get('start', {}).get('dateTime', event.get('start', {}).get('date', 'N/A'))
            formatted.append(f"- {summary} ({start})")
        
        return "\n".join(formatted)
    
    async def create_task(self, task_description: str) -> str:
        """Crea una tarea en Notion"""
        try:
            result = await self.notion.create_task(task_description)
            return f"✅ Tarea creada exitosamente: {result}"
        except Exception as e:
            return f"❌ Error al crear tarea: {str(e)}"
    
    async def create_event(self, event_details: dict) -> str:
        """Crea un evento en Google Calendar"""
        try:
            result = await self.calendar.create_event(event_details)
            return f"✅ Evento creado exitosamente: {result}"
        except Exception as e:
            return f"❌ Error al crear evento: {str(e)}"
