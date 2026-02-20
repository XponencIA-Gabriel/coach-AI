"""Integración con Notion API - Soporte para múltiples bases de datos"""
from notion_client import Client
from config import Config
import asyncio
from typing import Optional
from dataclasses import dataclass


@dataclass
class NotionDatabase:
    """Configuración de una base de datos de Notion"""
    id: str
    name: str
    type: str  # 'tasks', 'notes', 'projects', 'habits', 'custom'


class NotionIntegration:
    """Cliente para interactuar con múltiples bases de datos de Notion"""
    
    def __init__(self):
        if Config.NOTION_API_KEY:
            self.client = Client(auth=Config.NOTION_API_KEY)
            self.databases: dict[str, NotionDatabase] = {}
            self._load_databases()
        else:
            self.client = None
            self.databases = {}
    
    def _load_databases(self):
        """Carga las bases de datos configuradas desde Config"""
        # Base de datos principal (retrocompatibilidad)
        if Config.NOTION_DATABASE_ID:
            self.databases['tasks'] = NotionDatabase(
                id=Config.NOTION_DATABASE_ID,
                name="Tareas",
                type="tasks"
            )
        
        # Bases de datos adicionales
        if Config.NOTION_NOTES_DB_ID:
            self.databases['notes'] = NotionDatabase(
                id=Config.NOTION_NOTES_DB_ID,
                name="Notas",
                type="notes"
            )
        
        if Config.NOTION_PROJECTS_DB_ID:
            self.databases['projects'] = NotionDatabase(
                id=Config.NOTION_PROJECTS_DB_ID,
                name="Proyectos",
                type="projects"
            )
        
        if Config.NOTION_HABITS_DB_ID:
            self.databases['habits'] = NotionDatabase(
                id=Config.NOTION_HABITS_DB_ID,
                name="Hábitos",
                type="habits"
            )
    
    def add_database(self, key: str, database_id: str, name: str, db_type: str = "custom"):
        """Agrega una base de datos dinámicamente"""
        self.databases[key] = NotionDatabase(
            id=database_id,
            name=name,
            type=db_type
        )
    
    def list_databases(self) -> list[dict]:
        """Lista todas las bases de datos configuradas"""
        return [
            {"key": key, "name": db.name, "type": db.type}
            for key, db in self.databases.items()
        ]
    
    def _get_database(self, db_key: str) -> Optional[NotionDatabase]:
        """Obtiene una base de datos por su clave"""
        return self.databases.get(db_key)
    
    # ==================== TAREAS ====================
    
    async def get_pending_tasks(self, db_key: str = "tasks") -> list:
        """Obtiene las tareas pendientes de una base de datos"""
        db = self._get_database(db_key)
        if not self.client or not db:
            return []
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.databases.query(
                    database_id=db.id,
                    filter={
                        "property": "Status",
                        "select": {
                            "does_not_equal": "Completado"
                        }
                    }
                )
            )
            
            tasks = []
            for page in response.get("results", []):
                task = {
                    "id": page.get("id"),
                    "title": self._extract_title(page),
                    "priority": self._extract_property(page, "Prioridad"),
                    "status": self._extract_property(page, "Status"),
                    "database": db.name
                }
                tasks.append(task)
            
            return tasks
        except Exception as e:
            print(f"Error obteniendo tareas de Notion ({db.name}): {e}")
            return []
    
    async def create_task(self, description: str, priority: str = "Media", db_key: str = "tasks") -> dict:
        """Crea una nueva tarea en una base de datos"""
        db = self._get_database(db_key)
        if not self.client or not db:
            raise ValueError(f"Base de datos '{db_key}' no está configurada")
        
        try:
            loop = asyncio.get_event_loop()
            page = await loop.run_in_executor(
                None,
                lambda: self.client.pages.create(
                    parent={"database_id": db.id},
                    properties={
                        "Name": {
                            "title": [{"text": {"content": description}}]
                        },
                        "Status": {
                            "select": {"name": "Pendiente"}
                        },
                        "Prioridad": {
                            "select": {"name": priority}
                        }
                    }
                )
            )
            
            return {
                "id": page.get("id"),
                "title": description,
                "url": page.get("url"),
                "database": db.name
            }
        except Exception as e:
            raise Exception(f"Error creando tarea en Notion ({db.name}): {str(e)}")

    
    # ==================== NOTAS ====================
    
    async def create_note(self, title: str, content: str = "", db_key: str = "notes") -> dict:
        """Crea una nueva nota"""
        db = self._get_database(db_key)
        if not self.client or not db:
            raise ValueError(f"Base de datos '{db_key}' no está configurada")
        
        try:
            loop = asyncio.get_event_loop()
            
            # Crear página con contenido
            children = []
            if content:
                children.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": content}}]
                    }
                })
            
            page = await loop.run_in_executor(
                None,
                lambda: self.client.pages.create(
                    parent={"database_id": db.id},
                    properties={
                        "Name": {
                            "title": [{"text": {"content": title}}]
                        }
                    },
                    children=children if children else None
                )
            )
            
            return {
                "id": page.get("id"),
                "title": title,
                "url": page.get("url"),
                "database": db.name
            }
        except Exception as e:
            raise Exception(f"Error creando nota en Notion ({db.name}): {str(e)}")
    
    async def get_recent_notes(self, limit: int = 10, db_key: str = "notes") -> list:
        """Obtiene las notas más recientes"""
        db = self._get_database(db_key)
        if not self.client or not db:
            return []
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.databases.query(
                    database_id=db.id,
                    page_size=limit,
                    sorts=[{"timestamp": "created_time", "direction": "descending"}]
                )
            )
            
            notes = []
            for page in response.get("results", []):
                notes.append({
                    "id": page.get("id"),
                    "title": self._extract_title(page),
                    "created": page.get("created_time"),
                    "url": page.get("url"),
                    "database": db.name
                })
            
            return notes
        except Exception as e:
            print(f"Error obteniendo notas de Notion ({db.name}): {e}")
            return []
    
    # ==================== PROYECTOS ====================
    
    async def get_active_projects(self, db_key: str = "projects") -> list:
        """Obtiene los proyectos activos"""
        db = self._get_database(db_key)
        if not self.client or not db:
            return []
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.databases.query(
                    database_id=db.id,
                    filter={
                        "property": "Status",
                        "select": {
                            "does_not_equal": "Completado"
                        }
                    }
                )
            )
            
            projects = []
            for page in response.get("results", []):
                projects.append({
                    "id": page.get("id"),
                    "title": self._extract_title(page),
                    "status": self._extract_property(page, "Status"),
                    "url": page.get("url"),
                    "database": db.name
                })
            
            return projects
        except Exception as e:
            print(f"Error obteniendo proyectos de Notion ({db.name}): {e}")
            return []
    
    # ==================== HÁBITOS ====================
    
    async def log_habit(self, habit_name: str, completed: bool = True, db_key: str = "habits") -> dict:
        """Registra un hábito completado"""
        db = self._get_database(db_key)
        if not self.client or not db:
            raise ValueError(f"Base de datos '{db_key}' no está configurada")
        
        try:
            from datetime import date
            loop = asyncio.get_event_loop()
            
            page = await loop.run_in_executor(
                None,
                lambda: self.client.pages.create(
                    parent={"database_id": db.id},
                    properties={
                        "Name": {
                            "title": [{"text": {"content": habit_name}}]
                        },
                        "Fecha": {
                            "date": {"start": date.today().isoformat()}
                        },
                        "Completado": {
                            "checkbox": completed
                        }
                    }
                )
            )
            
            return {
                "id": page.get("id"),
                "habit": habit_name,
                "completed": completed,
                "database": db.name
            }
        except Exception as e:
            raise Exception(f"Error registrando hábito en Notion ({db.name}): {str(e)}")
    
    # ==================== CONSULTAS GENÉRICAS ====================
    
    async def query_database(self, db_key: str, filter_obj: dict = None, sorts: list = None, limit: int = 100) -> list:
        """Consulta genérica a cualquier base de datos"""
        db = self._get_database(db_key)
        if not self.client or not db:
            return []
        
        try:
            loop = asyncio.get_event_loop()
            
            query_params = {"database_id": db.id, "page_size": limit}
            if filter_obj:
                query_params["filter"] = filter_obj
            if sorts:
                query_params["sorts"] = sorts
            
            response = await loop.run_in_executor(
                None,
                lambda: self.client.databases.query(**query_params)
            )
            
            results = []
            for page in response.get("results", []):
                results.append({
                    "id": page.get("id"),
                    "title": self._extract_title(page),
                    "properties": page.get("properties", {}),
                    "url": page.get("url"),
                    "database": db.name
                })
            
            return results
        except Exception as e:
            print(f"Error consultando Notion ({db.name}): {e}")
            return []
    
    async def create_page(self, db_key: str, properties: dict, content: list = None) -> dict:
        """Crea una página genérica en cualquier base de datos"""
        db = self._get_database(db_key)
        if not self.client or not db:
            raise ValueError(f"Base de datos '{db_key}' no está configurada")
        
        try:
            loop = asyncio.get_event_loop()
            
            create_params = {
                "parent": {"database_id": db.id},
                "properties": properties
            }
            if content:
                create_params["children"] = content
            
            page = await loop.run_in_executor(
                None,
                lambda: self.client.pages.create(**create_params)
            )
            
            return {
                "id": page.get("id"),
                "url": page.get("url"),
                "database": db.name
            }
        except Exception as e:
            raise Exception(f"Error creando página en Notion ({db.name}): {str(e)}")
    
    # ==================== UTILIDADES ====================
    
    def _extract_title(self, page: dict) -> str:
        """Extrae el título de una página de Notion"""
        properties = page.get("properties", {})
        for prop_name, prop_data in properties.items():
            if prop_data.get("type") == "title":
                title_array = prop_data.get("title", [])
                if title_array:
                    return title_array[0].get("plain_text", "Sin título")
        return "Sin título"
    
    def _extract_property(self, page: dict, property_name: str) -> str:
        """Extrae una propiedad específica de una página"""
        properties = page.get("properties", {})
        prop_data = properties.get(property_name, {})
        
        prop_type = prop_data.get("type")
        
        if prop_type == "select":
            select = prop_data.get("select")
            return select.get("name", "N/A") if select else "N/A"
        elif prop_type == "multi_select":
            return ", ".join([s.get("name", "") for s in prop_data.get("multi_select", [])])
        elif prop_type == "checkbox":
            return "Sí" if prop_data.get("checkbox") else "No"
        elif prop_type == "date":
            date_obj = prop_data.get("date")
            return date_obj.get("start", "N/A") if date_obj else "N/A"
        elif prop_type == "number":
            return str(prop_data.get("number", "N/A"))
        
        return "N/A"
