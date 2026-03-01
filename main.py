"""
Точка входа для Telegram-бота и веб-интерфейса.
Запуск бота и веб-сервера параллельно.
"""

import logging
import os
import sys
import threading
from pathlib import Path

from bot import create_application
from security import load_config
from web_app import start_web_server

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def get_token() -> str:
    """
    Получение токена бота из переменной окружения или файла.

    Returns:
        Токен бота
    """
    token = os.environ.get('TELEGRAM_BOT_TOKEN')

    if token:
        return token

    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('TELEGRAM_BOT_TOKEN='):
                    token = line.split('=', 1)[1].strip()
                    if token.startswith('"') or token.startswith("'"):
                        token = token[1:-1]
                    return token

    try:
        config = load_config()
        token = config.get('telegram_token', '')
        if token:
            return token
    except Exception:
        pass

    return ''


def main():
    """Основная функция запуска бота и веб-сервера."""
    logger.info("=" * 50)
    logger.info("Starting Advanced Telegram Bot + Web Interface...")
    logger.info("=" * 50)

    token = get_token()
    
    if not token:
        logger.error(
            "❌ TELEGRAM_BOT_TOKEN not found!\n"
            "Please set the environment variable TELEGRAM_BOT_TOKEN\n"
            "or create a .env file with the token."
        )
        print("\n" + "=" * 50)
        print("❌ ERROR: Telegram bot token not found!")
        print("=" * 50)
        print("\nTo fix this, please:")
        print("1. Get your bot token from @BotFather on Telegram")
        print("2. Set environment variable:")
        print('   setx TELEGRAM_BOT_TOKEN "your_token_here"')
        print("\nOr create a .env file in the bot directory:")
        print('   TELEGRAM_BOT_TOKEN=your_token_here')
        print("=" * 50)
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    logger.info("✓ Token loaded successfully")

    try:
        application = create_application(token)
        logger.info("✓ Application created successfully")
    except Exception as e:
        logger.error(f"❌ Error creating application: {e}")
        print(f"❌ Error creating application: {e}")
        sys.exit(1)

    # Запуск веб-сервера в отдельном потоке
    web_thread = threading.Thread(target=start_web_server, daemon=False)
    web_thread.start()
    logger.info("✓ Web server thread started")

    try:
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        print("\n\n⚠️ Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")
        print(f"\n❌ Bot error: {e}")
        sys.exit(1)
    finally:
        logger.info("Bot shutdown complete")


from telegram import Update

if __name__ == '__main__':
    main()
