"""Integración con Beeminder API"""
import aiohttp
from config import Config
from datetime import datetime
from typing import Optional


class BeeminderIntegration:
    """Cliente para interactuar con Beeminder"""
    
    BASE_URL = "https://www.beeminder.com/api/v1"
    
    def __init__(self):
        self.auth_token = Config.BEEMINDER_AUTH_TOKEN
        self.username = Config.BEEMINDER_USERNAME
    
    async def _request(self, method: str, endpoint: str, json_data: dict = None, params: dict = None) -> dict:
        """Realiza una petición a la API de Beeminder"""
        if not self.auth_token or not self.username:
            raise ValueError("Beeminder no está configurado")
        
        url = f"{self.BASE_URL}{endpoint}"
        
        # Agregar auth_token a los params
        if params is None:
            params = {}
        params["auth_token"] = self.auth_token
        
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, json=json_data, params=params) as response:
                if response.status >= 400:
                    text = await response.text()
                    raise Exception(f"Error Beeminder ({response.status}): {text}")
                return await response.json()
    
    async def get_user(self) -> dict:
        """Obtiene información del usuario"""
        return await self._request("GET", f"/users/{self.username}.json")
    
    async def get_goals(self) -> list:
        """Obtiene todos los goals del usuario"""
        return await self._request("GET", f"/users/{self.username}/goals.json")
    
    async def get_goal(self, goal_slug: str) -> dict:
        """Obtiene información de un goal específico"""
        return await self._request("GET", f"/users/{self.username}/goals/{goal_slug}.json")

    
    async def add_datapoint(self, goal_slug: str, value: float, comment: str = "") -> dict:
        """
        Agrega un datapoint a un goal
        
        Args:
            goal_slug: Identificador del goal
            value: Valor a agregar
            comment: Comentario opcional
        """
        data = {
            "value": value,
            "comment": comment,
            "auth_token": self.auth_token
        }
        return await self._request("POST", f"/users/{self.username}/goals/{goal_slug}/datapoints.json", json_data=data)
    
    async def get_datapoints(self, goal_slug: str, count: int = 10) -> list:
        """Obtiene los últimos datapoints de un goal"""
        params = {"count": count}
        return await self._request("GET", f"/users/{self.username}/goals/{goal_slug}/datapoints.json", params=params)
    
    async def get_goals_summary(self) -> str:
        """Obtiene un resumen de todos los goals"""
        if not self.auth_token or not self.username:
            return "Beeminder no está configurado"
        
        try:
            goals = await self.get_goals()
            
            if not goals:
                return "📊 No tienes goals en Beeminder"
            
            # Clasificar por urgencia
            derailing = []  # En peligro (menos de 1 día)
            warning = []    # Advertencia (1-2 días)
            safe = []       # Seguros (más de 2 días)
            
            for goal in goals:
                slug = goal.get("slug", "")
                title = goal.get("title", slug)
                safebuf = goal.get("safebuf", 0)  # Días de buffer
                limsum = goal.get("limsum", "")   # Resumen del límite
                
                goal_info = {
                    "slug": slug,
                    "title": title,
                    "safebuf": safebuf,
                    "limsum": limsum
                }
                
                if safebuf < 1:
                    derailing.append(goal_info)
                elif safebuf < 2:
                    warning.append(goal_info)
                else:
                    safe.append(goal_info)
            
            formatted = "🐝 Estado de Beeminder:\n\n"
            
            if derailing:
                formatted += "🔴 EN PELIGRO:\n"
                for g in derailing:
                    formatted += f"  • {g['title']}: {g['limsum']}\n"
                formatted += "\n"
            
            if warning:
                formatted += "🟡 ADVERTENCIA:\n"
                for g in warning:
                    formatted += f"  • {g['title']}: {g['limsum']}\n"
                formatted += "\n"
            
            if safe:
                formatted += "🟢 SEGUROS:\n"
                for g in safe[:5]:  # Mostrar máximo 5
                    formatted += f"  • {g['title']}: {g['safebuf']:.0f} días\n"
                if len(safe) > 5:
                    formatted += f"  ... y {len(safe) - 5} más\n"
            
            return formatted.strip()
            
        except Exception as e:
            return f"Error obteniendo goals: {str(e)}"
    
    async def get_derailing_goals(self) -> str:
        """Obtiene los goals que están en peligro de descarrilar"""
        if not self.auth_token or not self.username:
            return "Beeminder no está configurado"
        
        try:
            goals = await self.get_goals()
            
            derailing = [g for g in goals if g.get("safebuf", 0) < 1]
            
            if not derailing:
                return "✅ No tienes goals en peligro"
            
            formatted = "🚨 Goals en peligro:\n\n"
            for goal in derailing:
                title = goal.get("title", goal.get("slug", ""))
                limsum = goal.get("limsum", "")
                baremin = goal.get("baremin", "")
                
                formatted += f"  🔴 {title}\n"
                formatted += f"     {limsum}\n"
                if baremin:
                    formatted += f"     Mínimo: {baremin}\n"
                formatted += "\n"
            
            return formatted.strip()
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def get_goal_info(self, goal_slug: str) -> str:
        """Obtiene información detallada de un goal"""
        if not self.auth_token or not self.username:
            return "Beeminder no está configurado"
        
        try:
            goal = await self.get_goal(goal_slug)
            
            title = goal.get("title", goal_slug)
            safebuf = goal.get("safebuf", 0)
            limsum = goal.get("limsum", "")
            rate = goal.get("rate", 0)
            runits = goal.get("runits", "")
            curval = goal.get("curval", 0)
            goalval = goal.get("goalval", 0)
            baremin = goal.get("baremin", "")
            
            # Determinar estado
            if safebuf < 1:
                status = "🔴 EN PELIGRO"
            elif safebuf < 2:
                status = "🟡 ADVERTENCIA"
            else:
                status = "🟢 SEGURO"
            
            formatted = f"🎯 {title}\n\n"
            formatted += f"  Estado: {status}\n"
            formatted += f"  Buffer: {safebuf:.1f} días\n"
            formatted += f"  Límite: {limsum}\n"
            formatted += f"  Ritmo: {rate} por {runits}\n"
            formatted += f"  Progreso: {curval:.1f} / {goalval:.1f}\n"
            if baremin:
                formatted += f"  Mínimo hoy: {baremin}\n"
            
            return formatted
            
        except Exception as e:
            return f"Error obteniendo goal: {str(e)}"
    
    async def quick_add(self, goal_slug: str, value: float = 1, comment: str = "") -> str:
        """Agrega rápidamente un datapoint y devuelve confirmación"""
        if not self.auth_token or not self.username:
            return "Beeminder no está configurado"
        
        try:
            result = await self.add_datapoint(goal_slug, value, comment)
            
            goal = await self.get_goal(goal_slug)
            title = goal.get("title", goal_slug)
            safebuf = goal.get("safebuf", 0)
            
            formatted = f"✅ Agregado a {title}:\n"
            formatted += f"  Valor: +{value}\n"
            if comment:
                formatted += f"  Nota: {comment}\n"
            formatted += f"  Nuevo buffer: {safebuf:.1f} días"
            
            return formatted
            
        except Exception as e:
            return f"Error agregando datapoint: {str(e)}"
