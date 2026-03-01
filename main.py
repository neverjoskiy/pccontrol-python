"""
Точка входа для Telegram-бота и веб-интерфейса.
Запуск бота и веб-сервера параллельно с поддержкой system tray.
"""

import logging
import os
import sys
import threading
import json
from pathlib import Path
from io import BytesIO

try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

from bot import create_application
from security import load_config, set_telegram_token, get_telegram_token
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


def create_tray_icon():
    """Создание иконки для system tray."""
    if not TRAY_AVAILABLE:
        return None
    
    size = (64, 64)
    image = Image.new('RGB', size, color=(0, 128, 0))
    draw = ImageDraw.Draw(image)
    
    # Рисуем простой круг
    draw.ellipse([5, 5, 59, 59], fill=(34, 177, 76), outline=(255, 255, 255))
    
    return image


def prompt_for_token() -> str:
    """
    Интерактивный запрос токена у пользователя.
    
    Returns:
        Введённый токен
    """
    print("\n" + "=" * 60)
    print("🔑  TELEGRAM BOT CONFIGURATION")
    print("=" * 60)
    print("\nNo telegram token found in configuration.")
    print("Please enter your Telegram bot token.")
    print("\nTo get a token:")
    print("  1. Open Telegram and find @BotFather")
    print("  2. Send /newbot command")
    print("  3. Follow the instructions")
    print("  4. Copy your bot token")
    print("\n" + "-" * 60)
    
    while True:
        token = input("\n📌 Enter your Telegram bot token: ").strip()
        
        if not token:
            print("❌ Token cannot be empty. Please try again.")
            continue
        
        if len(token) < 10:
            print("❌ Token seems too short. Please verify and try again.")
            continue
        
        confirm = input(f"\n✓ Token: {token[:10]}...{token[-5:]}\nConfirm? (yes/no): ").strip().lower()
        
        if confirm in ['yes', 'y', 'да']:
            return token
        else:
            print("❌ Token rejected. Please try again.")


def get_token() -> str:
    """
    Получение токена бота из различных источников.

    Returns:
        Токен бота
    """
    # Проверяем переменную окружения
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if token:
        return token

    # Проверяем .env файл
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('TELEGRAM_BOT_TOKEN='):
                        token = line.split('=', 1)[1].strip()
                        if token.startswith('"') or token.startswith("'"):
                            token = token[1:-1]
                        if token:
                            return token
        except Exception as e:
            logger.error(f"Error reading .env file: {e}")

    # Проверяем config.json
    try:
        token = get_telegram_token()
        if token:
            return token
    except Exception as e:
        logger.error(f"Error reading config.json: {e}")

    # Если токена нет нигде - просим его у пользователя
    token = prompt_for_token()
    
    # Сохраняем токен в config.json
    try:
        set_telegram_token(token)
        logger.info("✓ Token saved to config.json")
        print("\n✓ Token saved to config.json successfully!\n")
    except Exception as e:
        logger.error(f"Error saving token: {e}")
        print(f"\n⚠️  Warning: Could not save token to config.json: {e}\n")
    
    return token


def create_icon_image():
    """Создание простой иконки для трея."""
    try:
        size = (64, 64)
        image = Image.new('RGB', size, color=(255, 255, 255))
        draw = ImageDraw.Draw(image)
        # Зелёная точка
        draw.ellipse([10, 10, 54, 54], fill=(34, 177, 76))
        return image
    except Exception as e:
        logger.error(f"Error creating icon: {e}")
        # Возвращаем пустую иконку
        return Image.new('RGB', (64, 64), color=(100, 100, 100))


def show_popup(title, message):
    """Показать всплывающее сообщение (если возможно)."""
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, message, title, 0x00000040)
    except Exception:
        pass


class TrayApp:
    """Класс для управления приложением в system tray."""
    
    def __init__(self, application):
        self.application = application
        self.icon = None
        self.running = True
    
    def create_menu(self):
        """Создание меню для трея."""
        def show_status():
            show_popup("Status", "✓ Bot is running\n✓ Web server is active")
        
        def quit_app(icon, item):
            logger.info("Quit command received from tray")
            self.running = False
            icon.stop()
            self.application.stop()
        
        menu = pystray.Menu(
            pystray.MenuItem('Status', show_status),
            pystray.MenuItem('Quit', quit_app)
        )
        return menu
    
    def run_tray(self):
        """Запуск иконки в system tray."""
        try:
            icon_image = create_icon_image()
            self.icon = pystray.Icon(
                "TelegramBot",
                icon_image,
                "PC Control Bot",
                menu=self.create_menu()
            )
            logger.info("✓ System tray icon created")
            self.icon.run()
        except Exception as e:
            logger.error(f"Tray error: {e}")


def main():
    """Основная функция запуска бота и веб-сервера."""
    print("\n" + "=" * 60)
    print("🚀  PC CONTROL BOT - ADVANCED TELEGRAM BOT")
    print("=" * 60)
    
    logger.info("=" * 60)
    logger.info("Starting Advanced Telegram Bot + Web Interface...")
    logger.info("=" * 60)

    token = get_token()
    
    if not token:
        logger.error("❌ TELEGRAM_BOT_TOKEN not found!")
        print("\n❌ ERROR: Telegram bot token not found!")
        print("=" * 60)
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    logger.info("✓ Token loaded successfully")
    print("✓ Token loaded successfully")

    try:
        application = create_application(token)
        logger.info("✓ Application created successfully")
        print("✓ Application created successfully")
    except Exception as e:
        logger.error(f"❌ Error creating application: {e}")
        print(f"❌ Error creating application: {e}")
        sys.exit(1)

    # Запуск веб-сервера в отдельном потоке
    web_thread = threading.Thread(target=start_web_server, daemon=False)
    web_thread.start()
    logger.info("✓ Web server thread started")
    print("✓ Web server thread started")
    
    # Сообщение об успешном запуске
    print("\n" + "=" * 60)
    print("✅  BOT STARTED SUCCESSFULLY")
    print("=" * 60)
    print("\n📊 Services running:")
    print("  ✓ Telegram Bot (polling)")
    print("  ✓ Web Interface (Flask server)")
    if TRAY_AVAILABLE:
        print("  ✓ System Tray Icon")
    print("\n💾 Configuration saved to: config.json")
    print("📝 Logs saved to: bot.log")
    print("\n" + "=" * 60 + "\n")
    
    logger.info("✅ BOT STARTED SUCCESSFULLY")
    logger.info("All services are running")
    
    # Запуск иконки в system tray (если доступно)
    tray_app = None
    tray_thread = None
    
    if TRAY_AVAILABLE:
        try:
            tray_app = TrayApp(application)
            tray_thread = threading.Thread(target=tray_app.run_tray, daemon=False)
            tray_thread.start()
            logger.info("✓ System tray icon started")
        except Exception as e:
            logger.warning(f"System tray not available: {e}")
            print(f"⚠️  System tray not available: {e}")

    try:
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        print("\n\n⚠️  Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")
        print(f"\n❌ Bot error: {e}")
        sys.exit(1)
    finally:
        if tray_app:
            try:
                tray_app.running = False
                if tray_app.icon:
                    tray_app.icon.stop()
            except Exception:
                pass
        logger.info("Bot shutdown complete")
        print("✓ Bot shutdown complete")


from telegram import Update

if __name__ == '__main__':
    main()
