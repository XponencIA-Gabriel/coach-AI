"""Integración con Focusmate API"""
import aiohttp
from config import Config
from datetime import datetime, timedelta
from typing import Optional


class FocusmateIntegration:
    """Cliente para interactuar con Focusmate"""
    
    BASE_URL = "https://api.focusmate.com/v1"
    
    def __init__(self):
        self.api_key = Config.FOCUSMATE_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        } if self.api_key else {}
    
    async def _request(self, method: str, endpoint: str, json_data: dict = None, params: dict = None) -> dict:
        """Realiza una petición a la API de Focusmate"""
        if not self.api_key:
            raise ValueError("Focusmate no está configurado")
        
        url = f"{self.BASE_URL}{endpoint}"
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, headers=self.headers, json=json_data, params=params) as response:
                if response.status >= 400:
                    text = await response.text()
                    raise Exception(f"Error Focusmate ({response.status}): {text}")
                return await response.json() if response.content_length else {}
    
    async def get_profile(self) -> dict:
        """Obtiene el perfil del usuario"""
        return await self._request("GET", "/me")
    
    async def get_sessions(self, start_date: datetime = None, end_date: datetime = None) -> list:
        """
        Obtiene las sesiones del usuario
        
        Args:
            start_date: Fecha de inicio (default: hace 7 días)
            end_date: Fecha de fin (default: 7 días en el futuro)
        """
        if not start_date:
            start_date = datetime.now() - timedelta(days=7)
        if not end_date:
            end_date = datetime.now() + timedelta(days=7)
        
        params = {
            "start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end": end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        
        response = await self._request("GET", "/sessions", params=params)
        return response.get("sessions", [])

    
    async def get_upcoming_sessions(self) -> list:
        """Obtiene las próximas sesiones programadas"""
        now = datetime.now()
        future = now + timedelta(days=7)
        
        sessions = await self.get_sessions(start_date=now, end_date=future)
        
        # Filtrar solo sesiones futuras
        upcoming = []
        for session in sessions:
            start_time = session.get("startTime")
            if start_time:
                session_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                if session_dt > datetime.now(session_dt.tzinfo):
                    upcoming.append(session)
        
        return sorted(upcoming, key=lambda x: x.get("startTime", ""))
    
    async def get_upcoming_sessions_formatted(self) -> str:
        """Obtiene las próximas sesiones formateadas"""
        if not self.api_key:
            return "Focusmate no está configurado"
        
        try:
            sessions = await self.get_upcoming_sessions()
            
            if not sessions:
                return "📅 No tienes sesiones de Focusmate programadas"
            
            formatted = "📅 Próximas sesiones de Focusmate:\n\n"
            
            for session in sessions[:5]:  # Máximo 5 sesiones
                start_time = session.get("startTime")
                duration = session.get("duration", 50)
                partner = session.get("partner", {})
                partner_name = partner.get("name", "Por asignar") if partner else "Por asignar"
                
                if start_time:
                    dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                    date_str = dt.strftime("%d/%m %H:%M")
                else:
                    date_str = "Fecha desconocida"
                
                formatted += f"  🕐 {date_str} ({duration}min)\n"
                formatted += f"     👤 Partner: {partner_name}\n\n"
            
            return formatted.strip()
            
        except Exception as e:
            return f"Error obteniendo sesiones: {str(e)}"
    
    async def get_current_session(self) -> Optional[dict]:
        """Obtiene la sesión activa actual si existe"""
        now = datetime.now()
        start = now - timedelta(hours=1)
        end = now + timedelta(hours=1)
        
        sessions = await self.get_sessions(start_date=start, end_date=end)
        
        for session in sessions:
            start_time = session.get("startTime")
            duration = session.get("duration", 50)
            
            if start_time:
                session_start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                session_end = session_start + timedelta(minutes=duration)
                now_tz = datetime.now(session_start.tzinfo)
                
                if session_start <= now_tz <= session_end:
                    return session
        
        return None
    
    async def get_current_session_info(self) -> str:
        """Obtiene información de la sesión actual formateada"""
        if not self.api_key:
            return "Focusmate no está configurado"
        
        try:
            session = await self.get_current_session()
            
            if not session:
                return "⏸️ No hay sesión de Focusmate activa en este momento"
            
            start_time = session.get("startTime")
            duration = session.get("duration", 50)
            partner = session.get("partner", {})
            partner_name = partner.get("name", "Sin partner") if partner else "Sin partner"
            session_url = session.get("joinUrl", "")
            
            # Calcular tiempo restante
            remaining = "Desconocido"
            if start_time:
                session_start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                session_end = session_start + timedelta(minutes=duration)
                now_tz = datetime.now(session_start.tzinfo)
                remaining_seconds = (session_end - now_tz).total_seconds()
                remaining_mins = int(remaining_seconds // 60)
                remaining = f"{remaining_mins}min"
            
            formatted = f"🎯 Sesión Focusmate activa:\n"
            formatted += f"  👤 Partner: {partner_name}\n"
            formatted += f"  ⏱️ Duración: {duration}min\n"
            formatted += f"  ⏳ Restante: {remaining}\n"
            if session_url:
                formatted += f"  🔗 {session_url}"
            
            return formatted
            
        except Exception as e:
            return f"Error obteniendo sesión: {str(e)}"
    
    async def get_stats(self, days: int = 30) -> str:
        """Obtiene estadísticas de sesiones completadas"""
        if not self.api_key:
            return "Focusmate no está configurado"
        
        try:
            end = datetime.now()
            start = end - timedelta(days=days)
            
            sessions = await self.get_sessions(start_date=start, end_date=end)
            
            # Filtrar sesiones pasadas (completadas)
            completed = []
            for session in sessions:
                start_time = session.get("startTime")
                if start_time:
                    session_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                    if session_dt < datetime.now(session_dt.tzinfo):
                        completed.append(session)
            
            total_sessions = len(completed)
            total_minutes = sum(s.get("duration", 50) for s in completed)
            total_hours = total_minutes / 60
            
            # Sesiones por semana
            sessions_per_week = total_sessions / (days / 7) if days >= 7 else total_sessions
            
            formatted = f"📊 Estadísticas Focusmate ({days} días):\n\n"
            formatted += f"  🎯 Sesiones completadas: {total_sessions}\n"
            formatted += f"  ⏱️ Tiempo total: {total_hours:.1f}h\n"
            formatted += f"  📈 Promedio semanal: {sessions_per_week:.1f} sesiones\n"
            
            return formatted
            
        except Exception as e:
            return f"Error obteniendo estadísticas: {str(e)}"
    
    async def get_next_session(self) -> Optional[dict]:
        """Obtiene la próxima sesión programada"""
        sessions = await self.get_upcoming_sessions()
        return sessions[0] if sessions else None
    
    async def get_next_session_info(self) -> str:
        """Obtiene información de la próxima sesión formateada"""
        if not self.api_key:
            return "Focusmate no está configurado"
        
        try:
            session = await self.get_next_session()
            
            if not session:
                return "📅 No tienes próximas sesiones programadas"
            
            start_time = session.get("startTime")
            duration = session.get("duration", 50)
            partner = session.get("partner", {})
            partner_name = partner.get("name", "Por asignar") if partner else "Por asignar"
            
            # Calcular tiempo hasta la sesión
            time_until = "Desconocido"
            date_str = "Fecha desconocida"
            if start_time:
                session_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                now_tz = datetime.now(session_dt.tzinfo)
                delta = session_dt - now_tz
                
                date_str = session_dt.strftime("%d/%m a las %H:%M")
                
                if delta.days > 0:
                    time_until = f"en {delta.days} día(s)"
                else:
                    hours = int(delta.seconds // 3600)
                    mins = int((delta.seconds % 3600) // 60)
                    if hours > 0:
                        time_until = f"en {hours}h {mins}m"
                    else:
                        time_until = f"en {mins}min"
            
            formatted = f"📅 Próxima sesión Focusmate:\n"
            formatted += f"  🗓️ {date_str} ({time_until})\n"
            formatted += f"  ⏱️ Duración: {duration}min\n"
            formatted += f"  👤 Partner: {partner_name}"
            
            return formatted
            
        except Exception as e:
            return f"Error obteniendo próxima sesión: {str(e)}"
