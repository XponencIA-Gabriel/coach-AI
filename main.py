"""Punto de entrada principal del Coach AI"""
import asyncio
import sys
from config import Config
from bot.telegram_bot import TelegramBot
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Función principal"""
    try:
        # Validar configuración
        Config.validate()
        logger.info("✅ Configuración validada correctamente")
        
        # Crear e iniciar el bot
        bot = TelegramBot()
        bot.run()
        
    except ValueError as e:
        logger.error(f"❌ Error de configuración: {e}")
        logger.error("Por favor, revisa tu archivo .env")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("👋 Bot detenido por el usuario")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
