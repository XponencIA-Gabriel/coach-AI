"""Integración con Clockify API"""
import aiohttp
from config import Config
from datetime import datetime, timedelta
from typing import Optional


class ClockifyIntegration:
    """Cliente para interactuar con Clockify"""
    
    BASE_URL = "https://api.clockify.me/api/v1"
    
    def __init__(self):
        self.api_key = Config.CLOCKIFY_API_KEY
        self.workspace_id = Config.CLOCKIFY_WORKSPACE_ID
        self.headers = {"X-Api-Key": self.api_key} if self.api_key else {}
    
    async def _request(self, method: str, endpoint: str, json_data: dict = None) -> dict:
        """Realiza una petición a la API de Clockify"""
        if not self.api_key:
            raise ValueError("Clockify no está configurado")
        
        url = f"{self.BASE_URL}{endpoint}"
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, headers=self.headers, json=json_data) as response:
                if response.status >= 400:
                    text = await response.text()
                    raise Exception(f"Error Clockify ({response.status}): {text}")
                return await response.json() if response.content_length else {}
    
    async def get_user(self) -> dict:
        """Obtiene información del usuario actual"""
        return await self._request("GET", "/user")
    
    async def get_workspaces(self) -> list:
        """Obtiene los workspaces del usuario"""
        return await self._request("GET", "/workspaces")
    
    async def get_projects(self, workspace_id: str = None) -> list:
        """Obtiene los proyectos de un workspace"""
        ws_id = workspace_id or self.workspace_id
        if not ws_id:
            raise ValueError("Workspace ID no configurado")
        return await self._request("GET", f"/workspaces/{ws_id}/projects")

    
    async def get_today_stats(self) -> str:
        """Obtiene las estadísticas de tiempo de hoy"""
        if not self.api_key or not self.workspace_id:
            return "Clockify no está configurado"
        
        try:
            user = await self.get_user()
            user_id = user.get("id")
            
            # Obtener entradas de hoy
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            entries = await self.get_time_entries(user_id, start_date=today)
            
            if not entries:
                return "📊 No hay registros de tiempo hoy"
            
            # Agrupar por proyecto
            projects_time = {}
            total_seconds = 0
            
            for entry in entries:
                project_name = entry.get("project", {}).get("name", "Sin proyecto") if entry.get("project") else "Sin proyecto"
                duration = entry.get("timeInterval", {})
                
                start = duration.get("start")
                end = duration.get("end")
                
                if start and end:
                    start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                    end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
                    seconds = (end_dt - start_dt).total_seconds()
                elif start and not end:  # Timer activo
                    start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                    seconds = (datetime.now(start_dt.tzinfo) - start_dt).total_seconds()
                else:
                    seconds = 0
                
                projects_time[project_name] = projects_time.get(project_name, 0) + seconds
                total_seconds += seconds
            
            # Formatear resultado
            formatted = "📊 Tiempo registrado hoy:\n"
            for project, seconds in sorted(projects_time.items(), key=lambda x: -x[1]):
                formatted += f"  • {project}: {self._format_duration(seconds)}\n"
            
            formatted += f"\n⏱️ Total: {self._format_duration(total_seconds)}"
            return formatted
            
        except Exception as e:
            return f"Error obteniendo estadísticas: {str(e)}"
    
    async def get_time_entries(self, user_id: str = None, start_date: datetime = None, 
                                end_date: datetime = None, workspace_id: str = None) -> list:
        """Obtiene las entradas de tiempo"""
        ws_id = workspace_id or self.workspace_id
        if not ws_id:
            raise ValueError("Workspace ID no configurado")
        
        if not user_id:
            user = await self.get_user()
            user_id = user.get("id")
        
        params = []
        if start_date:
            params.append(f"start={start_date.isoformat()}Z")
        if end_date:
            params.append(f"end={end_date.isoformat()}Z")
        
        query = f"?{'&'.join(params)}" if params else ""
        return await self._request("GET", f"/workspaces/{ws_id}/user/{user_id}/time-entries{query}")
    
    async def get_current_timer(self) -> Optional[dict]:
        """Obtiene el timer activo actual (datos raw)"""
        user = await self.get_user()
        user_id = user.get("id")
        ws_id = self.workspace_id
        
        entries = await self._request("GET", f"/workspaces/{ws_id}/user/{user_id}/time-entries?in-progress=true")
        return entries[0] if entries else None
    
    async def get_current_task_info(self) -> str:
        """Obtiene información formateada de la tarea actual"""
        if not self.api_key or not self.workspace_id:
            return "Clockify no está configurado"
        
        try:
            timer = await self.get_current_timer()
            
            if not timer:
                return "⏸️ No hay ningún timer activo en este momento"
            
            # Extraer información
            description = timer.get("description", "Sin descripción")
            project = timer.get("project")
            project_name = project.get("name") if project else "Sin proyecto"
            tags = timer.get("tags", [])
            tag_names = ", ".join([t.get("name", "") for t in tags]) if tags else "Sin etiquetas"
            
            # Calcular tiempo transcurrido
            time_interval = timer.get("timeInterval", {})
            start = time_interval.get("start")
            
            elapsed = "Desconocido"
            start_time = "Desconocido"
            if start:
                start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                now = datetime.now(start_dt.tzinfo)
                elapsed_seconds = (now - start_dt).total_seconds()
                elapsed = self._format_duration(elapsed_seconds)
                start_time = start_dt.strftime("%H:%M")
            
            # Formatear respuesta
            formatted = f"⏱️ Tarea actual:\n"
            formatted += f"  📝 {description}\n"
            formatted += f"  📁 Proyecto: {project_name}\n"
            formatted += f"  🏷️ Tags: {tag_names}\n"
            formatted += f"  🕐 Iniciado: {start_time}\n"
            formatted += f"  ⏳ Tiempo: {elapsed}"
            
            return formatted
            
        except Exception as e:
            return f"Error obteniendo tarea actual: {str(e)}"
    
    async def start_timer(self, description: str, project_id: str = None) -> dict:
        """Inicia un nuevo timer"""
        ws_id = self.workspace_id
        if not ws_id:
            raise ValueError("Workspace ID no configurado")
        
        data = {
            "start": datetime.utcnow().isoformat() + "Z",
            "description": description
        }
        if project_id:
            data["projectId"] = project_id
        
        return await self._request("POST", f"/workspaces/{ws_id}/time-entries", data)
    
    async def stop_timer(self) -> dict:
        """Detiene el timer activo"""
        user = await self.get_user()
        user_id = user.get("id")
        ws_id = self.workspace_id
        
        data = {"end": datetime.utcnow().isoformat() + "Z"}
        return await self._request("PATCH", f"/workspaces/{ws_id}/user/{user_id}/time-entries", data)
    
    async def get_weekly_summary(self) -> str:
        """Obtiene resumen de la semana"""
        if not self.api_key or not self.workspace_id:
            return "Clockify no está configurado"
        
        try:
            user = await self.get_user()
            user_id = user.get("id")
            
            # Calcular inicio de semana (lunes)
            today = datetime.now()
            start_of_week = today - timedelta(days=today.weekday())
            start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
            
            entries = await self.get_time_entries(user_id, start_date=start_of_week)
            
            if not entries:
                return "📊 No hay registros esta semana"
            
            # Agrupar por día y proyecto
            daily_totals = {}
            project_totals = {}
            total_seconds = 0
            
            for entry in entries:
                project_name = entry.get("project", {}).get("name", "Sin proyecto") if entry.get("project") else "Sin proyecto"
                duration = entry.get("timeInterval", {})
                start = duration.get("start")
                end = duration.get("end")
                
                if start:
                    start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                    day_name = start_dt.strftime("%A")
                    
                    if end:
                        end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
                        seconds = (end_dt - start_dt).total_seconds()
                    else:
                        seconds = (datetime.now(start_dt.tzinfo) - start_dt).total_seconds()
                    
                    daily_totals[day_name] = daily_totals.get(day_name, 0) + seconds
                    project_totals[project_name] = project_totals.get(project_name, 0) + seconds
                    total_seconds += seconds
            
            formatted = "📊 Resumen semanal:\n\n"
            formatted += "Por día:\n"
            for day, seconds in daily_totals.items():
                formatted += f"  • {day}: {self._format_duration(seconds)}\n"
            
            formatted += "\nPor proyecto:\n"
            for project, seconds in sorted(project_totals.items(), key=lambda x: -x[1]):
                formatted += f"  • {project}: {self._format_duration(seconds)}\n"
            
            formatted += f"\n⏱️ Total semana: {self._format_duration(total_seconds)}"
            return formatted
            
        except Exception as e:
            return f"Error obteniendo resumen: {str(e)}"
    
    def _format_duration(self, seconds: float) -> str:
        """Formatea segundos a formato legible"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
