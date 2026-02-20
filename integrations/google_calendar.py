"""Integración con Google Calendar API"""
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import Config
import os
import pickle
import asyncio
from datetime import datetime, timedelta

SCOPES = ['https://www.googleapis.com/auth/calendar']

class GoogleCalendarIntegration:
    """Cliente para interactuar con Google Calendar"""
    
    def __init__(self):
        self.service = None
        self.calendar_id = Config.GOOGLE_CALENDAR_ID
        self._authenticate()
    
    def _authenticate(self):
        """Autentica con Google Calendar API"""
        creds = None
        
        # Cargar credenciales existentes
        if os.path.exists(Config.GOOGLE_CALENDAR_TOKEN_PATH):
            with open(Config.GOOGLE_CALENDAR_TOKEN_PATH, 'rb') as token:
                creds = pickle.load(token)
        
        # Si no hay credenciales válidas, hacer login
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(Config.GOOGLE_CALENDAR_CREDENTIALS_PATH):
                    print(f"⚠️  No se encontró {Config.GOOGLE_CALENDAR_CREDENTIALS_PATH}")
                    return
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    Config.GOOGLE_CALENDAR_CREDENTIALS_PATH, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Guardar credenciales
            with open(Config.GOOGLE_CALENDAR_TOKEN_PATH, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('calendar', 'v3', credentials=creds)
    
    async def get_upcoming_events(self, limit: int = 10) -> list:
        """
        Obtiene los próximos eventos del calendario
        
        Args:
            limit: Número máximo de eventos a obtener
        
        Returns:
            Lista de eventos próximos
        """
        if not self.service:
            return []
        
        try:
            now = datetime.utcnow().isoformat() + 'Z'
            time_max = (datetime.utcnow() + timedelta(days=7)).isoformat() + 'Z'
            
            loop = asyncio.get_event_loop()
            events_result = await loop.run_in_executor(
                None,
                lambda: self.service.events().list(
                    calendarId=self.calendar_id,
                    timeMin=now,
                    timeMax=time_max,
                    maxResults=limit,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
            )
            
            events = events_result.get('items', [])
            return events
        except HttpError as e:
            print(f"Error obteniendo eventos: {e}")
            return []
    
    async def create_event(self, event_details: dict) -> dict:
        """
        Crea un nuevo evento en el calendario
        
        Args:
            event_details: Diccionario con detalles del evento
                - summary: Título del evento
                - start: Fecha/hora de inicio (ISO format)
                - end: Fecha/hora de fin (ISO format)
                - description: Descripción opcional
        
        Returns:
            Información del evento creado
        """
        if not self.service:
            raise ValueError("Google Calendar no está configurado correctamente")
        
        try:
            event = {
                'summary': event_details.get('summary', 'Nuevo evento'),
                'description': event_details.get('description', ''),
                'start': {
                    'dateTime': event_details.get('start'),
                    'timeZone': 'America/Argentina/Buenos_Aires',
                },
                'end': {
                    'dateTime': event_details.get('end'),
                    'timeZone': 'America/Argentina/Buenos_Aires',
                },
            }
            
            loop = asyncio.get_event_loop()
            created_event = await loop.run_in_executor(
                None,
                lambda: self.service.events().insert(
                    calendarId=self.calendar_id,
                    body=event
                ).execute()
            )
            
            return {
                'id': created_event.get('id'),
                'summary': created_event.get('summary'),
                'htmlLink': created_event.get('htmlLink')
            }
        except HttpError as e:
            raise Exception(f"Error creando evento: {str(e)}")

