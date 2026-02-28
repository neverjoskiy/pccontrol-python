"""
Файловый менеджер для Telegram-бота.
Навигация по дискам и папкам, просмотр содержимого, операции с файлами.
"""

import logging
import os
import shutil
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def get_drives() -> list:
    """
    Получение списка доступных дисков.
    
    Returns:
        Список доступных дисков (C:\, D:\, etc.)
    """
    import string
    drives = []
    for drive in string.ascii_uppercase:
        drive_path = f"{drive}:\\"
        if Path(drive_path).exists():
            drives.append(drive_path)
    return drives


def get_directory_contents(path: str) -> tuple[list, str]:
    """
    Получение содержимого директории.
    
    Args:
        path: Путь к директории
        
    Returns:
        Кортеж (items, error)
        items: Список элементов (папки и файлы)
        error: Сообщение об ошибке или пустая строка
    """
    try:
        dir_path = Path(path)
        if not dir_path.exists():
            return [], f"Directory does not exist: {path}"
        if not dir_path.is_dir():
            return [], f"Not a directory: {path}"
        
        items = []
        # Сначала папки
        for item in sorted(dir_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            try:
                stat = item.stat()
                size = stat.st_size if item.is_file() else 0
                items.append({
                    'name': item.name,
                    'path': str(item),
                    'is_dir': item.is_dir(),
                    'size': size,
                    'modified': stat.st_mtime
                })
            except (PermissionError, OSError):
                # Пропускаем элементы без доступа
                continue
        
        return items, ""
    except PermissionError:
        return [], f"Access denied to: {path}"
    except Exception as e:
        logger.error(f"Ошибка чтения директории {path}: {e}")
        return [], f"Error: {e}"


def get_parent_directory(path: str) -> str:
    """
    Получение родительской директории.

    Args:
        path: Текущий путь

    Returns:
        Путь к родительской директории
    """
    if not path:
        return ""

    parent = Path(path).parent
    if str(parent) == path or str(parent) == path[:3]:
        return ""
    return str(parent)


def navigate_to_path(path: str) -> tuple[Optional[list], str]:
    """
    Навигация к указанному пути.

    Args:
        path: Путь для навигации

    Returns:
        Кортеж (items, error)
    """
    if not path:
        drives = get_drives()
        items = [{'name': d, 'path': d, 'is_dir': True, 'size': 0} for d in drives]
        return items, ""

    return get_directory_contents(path)


def delete_file(file_path: str) -> tuple[bool, str]:
    """
    Удаление файла или папки.
    
    Args:
        file_path: Путь к файлу/папке
        
    Returns:
        Кортеж (success, message)
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return False, f"Path does not exist: {file_path}"
        
        if path.is_file():
            path.unlink()
            message = f"✅ File deleted: {file_path}"
        else:
            shutil.rmtree(path)
            message = f"✅ Directory deleted: {file_path}"
        
        logger.info(message)
        return True, message
    except PermissionError:
        message = f"❌ Access denied to delete: {file_path}"
        logger.error(message)
        return False, message
    except Exception as e:
        message = f"❌ Error deleting {file_path}: {e}"
        logger.error(message)
        return False, message


def rename_file(file_path: str, new_name: str) -> tuple[bool, str]:
    """
    Переименование файла или папки.
    
    Args:
        file_path: Текущий путь
        new_name: Новое имя
        
    Returns:
        Кортеж (success, message)
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return False, f"Path does not exist: {file_path}"
        
        new_path = path.parent / new_name
        if new_path.exists():
            return False, f"Destination already exists: {new_path}"
        
        path.rename(new_path)
        message = f"✅ Renamed to: {new_name}"
        logger.info(message)
        return True, message
    except PermissionError:
        message = f"❌ Access denied to rename: {file_path}"
        logger.error(message)
        return False, message
    except Exception as e:
        message = f"❌ Error renaming {file_path}: {e}"
        logger.error(message)
        return False, message


def move_file(file_path: str, destination: str) -> tuple[bool, str]:
    """
    Перемещение файла или папки.
    
    Args:
        file_path: Путь к файлу
        destination: Путь назначения
        
    Returns:
        Кортеж (success, message)
    """
    try:
        path = Path(file_path)
        dest_path = Path(destination)
        
        if not path.exists():
            return False, f"Source does not exist: {file_path}"
        
        if not dest_path.parent.exists():
            return False, f"Destination directory does not exist: {dest_path.parent}"
        
        shutil.move(str(path), str(dest_path))
        message = f"✅ Moved to: {destination}"
        logger.info(message)
        return True, message
    except PermissionError:
        message = f"❌ Access denied to move: {file_path}"
        logger.error(message)
        return False, message
    except Exception as e:
        message = f"❌ Error moving {file_path}: {e}"
        logger.error(message)
        return False, message


def copy_file(file_path: str, destination: str) -> tuple[bool, str]:
    """
    Копирование файла или папки.
    
    Args:
        file_path: Путь к файлу
        destination: Путь назначения
        
    Returns:
        Кортеж (success, message)
    """
    try:
        path = Path(file_path)
        dest_path = Path(destination)
        
        if not path.exists():
            return False, f"Source does not exist: {file_path}"
        
        if not dest_path.parent.exists():
            return False, f"Destination directory does not exist: {dest_path.parent}"
        
        if path.is_file():
            shutil.copy2(str(path), str(dest_path))
        else:
            shutil.copytree(str(path), str(dest_path))
        
        message = f"✅ Copied to: {destination}"
        logger.info(message)
        return True, message
    except PermissionError:
        message = f"❌ Access denied to copy: {file_path}"
        logger.error(message)
        return False, message
    except Exception as e:
        message = f"❌ Error copying {file_path}: {e}"
        logger.error(message)
        return False, message


def get_file_info(file_path: str) -> Optional[dict]:
    """
    Получение информации о файле.
    
    Args:
        file_path: Путь к файлу
        
    Returns:
        Словарь с информацией о файле или None
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return None
        
        stat = path.stat()
        return {
            'name': path.name,
            'path': str(path),
            'is_file': path.is_file(),
            'is_dir': path.is_dir(),
            'size': stat.st_size,
            'created': stat.st_ctime,
            'modified': stat.st_mtime,
            'extension': path.suffix
        }
    except Exception as e:
        logger.error(f"Ошибка получения информации о файле {file_path}: {e}")
        return None


def format_size(size: int) -> str:
    """
    Форматирование размера файла.
    
    Args:
        size: Размер в байтах
        
    Returns:
        Отформатированная строка
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


def save_uploaded_file(file_path: str, content: bytes) -> tuple[bool, str]:
    """
    Сохранение загруженного файла.
    
    Args:
        file_path: Путь для сохранения
        content: Содержимое файла
        
    Returns:
        Кортеж (success, message)
    """
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'wb') as f:
            f.write(content)
        
        message = f"✅ File saved: {file_path}"
        logger.info(message)
        return True, message
    except PermissionError:
        message = f"❌ Access denied to save: {file_path}"
        logger.error(message)
        return False, message
    except Exception as e:
        message = f"❌ Error saving {file_path}: {e}"
        logger.error(message)
        return False, message


def create_directory(dir_path: str) -> tuple[bool, str]:
    """
    Создание директории.
    
    Args:
        dir_path: Путь к новой директории
        
    Returns:
        Кортеж (success, message)
    """
    try:
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        message = f"✅ Directory created: {dir_path}"
        logger.info(message)
        return True, message
    except PermissionError:
        message = f"❌ Access denied to create directory: {dir_path}"
        logger.error(message)
        return False, message
    except Exception as e:
        message = f"❌ Error creating directory {dir_path}: {e}"
        logger.error(message)
        return False, message
