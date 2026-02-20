"""Integración con RescueTime API"""
import requests
from config import Config
import asyncio
from datetime import datetime, timedelta

class RescueTimeIntegration:
    """Cliente para interactuar con RescueTime API"""
    
    def __init__(self):
        self.api_key = Config.RESCUETIME_API_KEY
        self.base_url = "https://www.rescuetime.com/anapi/data"
    
    async def get_today_summary(self) -> dict:
        """
        Obtiene el resumen de productividad de hoy
        
        Returns:
            Diccionario con estadísticas del día
        """
        if not self.api_key:
            return {}
        
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            params = {
                "key": self.api_key,
                "format": "json",
                "rs": "day",
                "rk": "productivity",
                "rt": "summary",
                "rb": today,
                "re": today
            }
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(self.base_url, params=params, timeout=10)
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_summary(data)
            else:
                print(f"Error RescueTime API: {response.status_code}")
                return {}
        
        except Exception as e:
            print(f"Error obteniendo datos de RescueTime: {e}")
            return {}
    
    async def get_productivity_score(self) -> dict:
        """
        Obtiene el puntaje de productividad de hoy
        
        Returns:
            Diccionario con puntaje y detalles
        """
        if not self.api_key:
            return {}
        
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            params = {
                "key": self.api_key,
                "format": "json",
                "rs": "day",
                "rk": "productivity",
                "rt": "overview",
                "rb": today,
                "re": today
            }
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(self.base_url, params=params, timeout=10)
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_productivity(data)
            else:
                return {}
        
        except Exception as e:
            print(f"Error obteniendo productividad: {e}")
            return {}
    
    async def get_top_activities(self, limit: int = 5) -> list:
        """
        Obtiene las actividades más frecuentes de hoy
        
        Args:
            limit: Número máximo de actividades a retornar
        
        Returns:
            Lista de actividades con tiempo dedicado
        """
        if not self.api_key:
            return []
        
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            params = {
                "key": self.api_key,
                "format": "json",
                "rs": "day",
                "rk": "productivity",
                "rt": "activity",
                "rb": today,
                "re": today
            }
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(self.base_url, params=params, timeout=10)
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_activities(data, limit)
            else:
                return []
        
        except Exception as e:
            print(f"Error obteniendo actividades: {e}")
            return []
    
    def _parse_summary(self, data: dict) -> dict:
        """Parsea los datos del resumen de RescueTime"""
        rows = data.get("rows", [])
        if not rows:
            return {}
        
        # Agrupar por nivel de productividad
        productivity_levels = {
            2: "Muy productivo",
            1: "Productivo",
            0: "Neutral",
            -1: "Distractor",
            -2: "Muy distractor"
        }
        
        summary = {
            "total_time": 0,
            "by_level": {}
        }
        
        for row in rows:
            productivity = row[1]  # Nivel de productividad
            time_seconds = row[0]  # Tiempo en segundos
            
            summary["total_time"] += time_seconds
            level_name = productivity_levels.get(productivity, "Desconocido")
            
            if level_name not in summary["by_level"]:
                summary["by_level"][level_name] = 0
            summary["by_level"][level_name] += time_seconds
        
        # Convertir segundos a horas y minutos
        summary["total_hours"] = summary["total_time"] / 3600
        for level in summary["by_level"]:
            summary["by_level"][level] = summary["by_level"][level] / 3600
        
        return summary
    
    def _parse_productivity(self, data: dict) -> dict:
        """Parsea los datos de productividad"""
        rows = data.get("rows", [])
        if not rows:
            return {}
        
        # Calcular puntaje promedio
        total_time = 0
        weighted_score = 0
        
        for row in rows:
            time_seconds = row[0]
            productivity = row[1]
            
            total_time += time_seconds
            weighted_score += time_seconds * productivity
        
        if total_time > 0:
            avg_score = weighted_score / total_time
        else:
            avg_score = 0
        
        return {
            "average_score": round(avg_score, 2),
            "total_hours": round(total_time / 3600, 2),
            "score_range": "De -2 (muy distractor) a +2 (muy productivo)"
        }
    
    def _parse_activities(self, data: dict, limit: int) -> list:
        """Parsea las actividades más frecuentes"""
        rows = data.get("rows", [])
        if not rows:
            return []
        
        activities = []
        for row in rows[:limit]:
            time_seconds = row[0]
            productivity = row[1]
            activity_name = row[3] if len(row) > 3 else "Desconocido"
            category = row[4] if len(row) > 4 else ""
            
            activities.append({
                "name": activity_name,
                "category": category,
                "time_hours": round(time_seconds / 3600, 2),
                "productivity": productivity
            })
        
        return activities
    
    def format_summary_text(self, summary: dict) -> str:
        """Formatea el resumen como texto legible"""
        if not summary:
            return "No hay datos disponibles de RescueTime"
        
        text = "📊 Resumen de productividad (RescueTime):\n\n"
        
        if "total_hours" in summary:
            text += f"⏱️ Tiempo total: {summary['total_hours']:.2f} horas\n\n"
        
        if "by_level" in summary:
            text += "Por nivel de productividad:\n"
            for level, hours in summary["by_level"].items():
                emoji = {
                    "Muy productivo": "🟢",
                    "Productivo": "🟡",
                    "Neutral": "⚪",
                    "Distractor": "🟠",
                    "Muy distractor": "🔴"
                }.get(level, "•")
                text += f"  {emoji} {level}: {hours:.2f} horas\n"
        
        return text

