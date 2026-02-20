# 🤖 Coach AI - Bot de Telegram con Integraciones

Un coach AI inteligente que se integra con Notion, Google Calendar, aTracker y envía notificaciones push a través de Telegram. Alimentado por Google Gemini.

## 🚀 Características

- **Bot de Telegram**: Interfaz conversacional completa
- **Soporte de Audio**: Envía y recibe mensajes de voz
- **RAG (Retrieval Augmented Generation)**: Acceso inteligente a documentos específicos con búsqueda semántica
- **Respuestas Multimodales**: Envía respuestas tanto en texto como en notas de voz
- **Integración con Notion**: Lee y escribe en bases de datos de Notion
- **Integración con Google Calendar**: Gestiona eventos y recordatorios
- **Integración con aTracker**: Monitorea tiempo y actividades
- **Integración con RescueTime**: Analiza productividad y uso del tiempo
- **Notificaciones Push**: Envía recordatorios y alertas
- **IA con Gemini**: Procesamiento de lenguaje natural avanzado

## 📋 Requisitos

- Python 3.9+
- Cuenta de Telegram con Bot Token
- API Key de Google Gemini
- Token de integración de Notion
- Credenciales de Google Calendar API
- Acceso a aTracker (API o configuración)
- API Key de RescueTime

## 🔧 Instalación

1. Clona o descarga este repositorio
2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. Copia `.env.example` a `.env` y completa las variables:
```bash
cp .env.example .env
```

4. Configura las credenciales de Google Calendar:
   - Descarga `credentials.json` desde Google Cloud Console
   - Colócalo en la raíz del proyecto

5. Ejecuta el bot:
```bash
python main.py
```

## 📁 Estructura del Proyecto

```
coach_ai/
├── main.py                 # Punto de entrada principal
├── bot/
│   ├── __init__.py
│   ├── telegram_bot.py    # Bot de Telegram
│   └── handlers.py        # Manejadores de comandos
├── integrations/
│   ├── __init__.py
│   ├── notion.py          # Integración con Notion
│   ├── google_calendar.py # Integración con Google Calendar
│   └── atracker.py        # Integración con aTracker
├── ai/
│   ├── __init__.py
│   ├── gemini_client.py   # Cliente de Gemini
│   └── coach_logic.py     # Lógica del coach AI
├── utils/
│   ├── __init__.py
│   ├── audio_handler.py   # Manejo de audio
│   └── notifications.py  # Sistema de notificaciones
└── config.py              # Configuración centralizada
```

## 🔑 Configuración de APIs

### Telegram
1. Habla con @BotFather en Telegram
2. Crea un nuevo bot con `/newbot`
3. Copia el token al archivo `.env`

### Google Gemini
1. Ve a [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Crea una API key
3. Cópiala al archivo `.env`

### Notion
1. Ve a [Notion Integrations](https://www.notion.so/my-integrations)
2. Crea una nueva integración
3. Copia el token interno
4. Comparte tu base de datos con la integración

### Google Calendar
1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un proyecto o selecciona uno existente
3. Habilita la API de Google Calendar
4. Crea credenciales OAuth 2.0
5. Descarga `credentials.json`

### RescueTime
1. Inicia sesión en [RescueTime](https://www.rescuetime.com/)
2. Ve a Settings > Data API
3. Genera una nueva API Key
4. Cópiala al archivo `.env`

### Documentos RAG (Opcional)
El bot puede usar documentos específicos para proporcionar contexto más relevante. Configura esto en tu archivo `.env`:

**Opción 1: Directorio con documentos**
```bash
DOCUMENTS_DIR=./mis_documentos
```

**Opción 2: Rutas específicas de documentos (separadas por coma)**
```bash
DOCUMENT_PATHS=./doc1.md,./doc2.md,./doc3.txt
```

**Nota**: Si no configuras ninguna opción, el bot buscará automáticamente `organizacion_xponencia_gabo.md` en la raíz del proyecto.

Los documentos soportados son: `.md`, `.txt`, `.mdx`

## 🎯 Uso

Una vez configurado, simplemente inicia una conversación con el bot en Telegram. El coach AI puede:

- **Responder preguntas usando tus documentos**: El bot usa RAG (búsqueda semántica) para encontrar información relevante en tus documentos específicos
- **Enviar respuestas en texto y voz**: Cada respuesta se envía tanto como mensaje de texto como nota de voz
- Gestionar tareas en Notion
- Consultar y crear eventos en Google Calendar
- Monitorear tiempo con aTracker
- Analizar productividad con RescueTime
- Enviar recordatorios y notificaciones
- Procesar mensajes de voz

### Características RAG

El sistema RAG permite al bot:
- Buscar información relevante en tus documentos usando búsqueda semántica
- Encontrar contexto relacionado incluso si no coincide exactamente con las palabras clave
- Usar múltiples documentos simultáneamente
- Proporcionar respuestas más precisas basadas en tu información personal

### Respuestas Multimodales

Cada respuesta del bot incluye:
- **Mensaje de texto**: Respuesta escrita completa
- **Nota de voz**: Audio generado automáticamente desde el texto (en español)

## 📝 Licencia

MIT

