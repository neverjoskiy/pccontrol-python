"""
Модуль мониторинга системы.
Мониторинг CPU, RAM, отслеживание изменений в директориях.
"""

import logging
import time
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime

import psutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

logger = logging.getLogger(__name__)


def get_cpu_usage(interval: float = 1.0) -> float:
    """
    Получение текущей загрузки CPU.
    
    Args:
        interval: Интервал измерения в секундах
        
    Returns:
        Процент загрузки CPU
    """
    return psutil.cpu_percent(interval=interval)


def get_cpu_usage_per_core() -> list:
    """
    Получение загрузки CPU по ядрам.
    
    Returns:
        Список процентов загрузки по ядрам
    """
    return psutil.cpu_percent(interval=1, percpu=True)


def get_ram_usage() -> dict:
    """
    Получение информации об использовании RAM.
    
    Returns:
        Словарь с информацией о RAM
    """
    mem = psutil.virtual_memory()
    return {
        'total': mem.total,
        'total_gb': mem.total / (1024 ** 3),
        'available': mem.available,
        'available_gb': mem.available / (1024 ** 3),
        'used': mem.used,
        'used_gb': mem.used / (1024 ** 3),
        'percent': mem.percent
    }


def get_disk_usage() -> list:
    """
    Получение информации об использовании дисков.
    
    Returns:
        Список с информацией о дисках
    """
    disks = []
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            disks.append({
                'device': partition.device,
                'mountpoint': partition.mountpoint,
                'fstype': partition.fstype,
                'total': usage.total,
                'total_gb': usage.total / (1024 ** 3),
                'used': usage.used,
                'used_gb': usage.used / (1024 ** 3),
                'free': usage.free,
                'free_gb': usage.free / (1024 ** 3),
                'percent': usage.percent
            })
        except PermissionError:
            continue
    return disks


def get_network_io() -> dict:
    """
    Получение статистики сетевого трафика.
    
    Returns:
        Словарь со статистикой
    """
    net_io = psutil.net_io_counters()
    return {
        'bytes_sent': net_io.bytes_sent,
        'bytes_sent_mb': net_io.bytes_sent / (1024 ** 2),
        'bytes_recv': net_io.bytes_recv,
        'bytes_recv_mb': net_io.bytes_recv / (1024 ** 2),
        'packets_sent': net_io.packets_sent,
        'packets_recv': net_io.packets_recv,
        'errin': net_io.errin,
        'errout': net_io.errout,
        'dropin': net_io.dropin,
        'dropout': net_io.dropout
    }


def get_system_status() -> dict:
    """
    Получение общего статуса системы.
    
    Returns:
        Словарь со статусом системы
    """
    return {
        'cpu_percent': get_cpu_usage(0.1),
        'ram': get_ram_usage(),
        'disk': get_disk_usage(),
        'network': get_network_io(),
        'boot_time': datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M:%S'),
        'uptime': str(datetime.now() - datetime.fromtimestamp(psutil.boot_time()))
    }


def format_cpu_status(cpu_percent: float) -> str:
    """
    Форматирование статуса CPU для вывода.
    
    Args:
        cpu_percent: Процент загрузки CPU
        
    Returns:
        Отформатированная строка
    """
    if cpu_percent < 30:
        status = "🟢 Normal"
    elif cpu_percent < 60:
        status = "🟡 Moderate"
    elif cpu_percent < 80:
        status = "🟠 High"
    else:
        status = "🔴 Critical"
    
    return f"""📈 CPU Monitor

Load: {cpu_percent:.1f}%
Status: {status}
"""


def format_ram_status(ram_info: dict) -> str:
    """
    Форматирование статуса RAM для вывода.
    
    Args:
        ram_info: Информация о RAM
        
    Returns:
        Отформатированная строка
    """
    percent = ram_info['percent']
    if percent < 50:
        status = "🟢 Normal"
    elif percent < 75:
        status = "🟡 Moderate"
    elif percent < 90:
        status = "🟠 High"
    else:
        status = "🔴 Critical"
    
    return f"""💾 RAM Monitor

Total: {ram_info['total_gb']:.1f} GB
Used: {ram_info['used_gb']:.1f} GB ({percent:.1f}%)
Available: {ram_info['available_gb']:.1f} GB
Status: {status}
"""


class DirectoryChangeHandler(FileSystemEventHandler):
    """
    Обработчик изменений в директории.
    """
    
    def __init__(self, callback: Callable, path: str):
        """
        Инициализация обработчика.
        
        Args:
            callback: Функция обратного вызова
            path: Путь к отслеживаемой директории
        """
        super().__init__()
        self.callback = callback
        self.path = path
    
    def on_created(self, event: FileSystemEvent):
        """Событие создания файла/папки."""
        if not event.is_directory:
            self.callback('created', event.src_path)
        else:
            self.callback('dir_created', event.src_path)
    
    def on_deleted(self, event: FileSystemEvent):
        """Событие удаления файла/папки."""
        if not event.is_directory:
            self.callback('deleted', event.src_path)
        else:
            self.callback('dir_deleted', event.src_path)
    
    def on_modified(self, event: FileSystemEvent):
        """Событие изменения файла/папки."""
        if not event.is_directory:
            self.callback('modified', event.src_path)
    
    def on_moved(self, event: FileSystemEvent):
        """Событие перемещения файла/папки."""
        if not event.is_directory:
            self.callback('moved', event.src_path, event.dest_path)
        else:
            self.callback('dir_moved', event.src_path, event.dest_path)


class DirectoryWatcher:
    """
    Класс для отслеживания изменений в директории.
    """
    
    def __init__(self, path: str, callback: Callable):
        """
        Инициализация наблюдателя.
        
        Args:
            path: Путь к директории
            callback: Функция обратного вызова
        """
        self.path = path
        self.callback = callback
        self.observer: Optional[Observer] = None
        self.is_running = False
    
    def start(self) -> bool:
        """
        Запуск наблюдения.
        
        Returns:
            True если успешно запущен
        """
        try:
            path = Path(self.path)
            if not path.exists():
                logger.error(f"Path does not exist: {self.path}")
                return False
            
            event_handler = DirectoryChangeHandler(self.callback, self.path)
            self.observer = Observer()
            self.observer.schedule(event_handler, self.path, recursive=True)
            self.observer.start()
            self.is_running = True
            logger.info(f"Started watching directory: {self.path}")
            return True
        except Exception as e:
            logger.error(f"Error starting directory watcher: {e}")
            return False
    
    def stop(self):
        """Остановка наблюдения."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            self.is_running = False
            logger.info(f"Stopped watching directory: {self.path}")


_active_watchers: list[DirectoryWatcher] = []


def start_directory_watch(path: str, callback: Callable) -> bool:
    """
    Запуск отслеживания директории.
    
    Args:
        path: Путь к директории
        callback: Функция обратного вызова
        
    Returns:
        True если успешно запущен
    """
    watcher = DirectoryWatcher(path, callback)
    if watcher.start():
        _active_watchers.append(watcher)
        return True
    return False


def stop_all_watchers():
    """Остановка всех наблюдателей."""
    for watcher in _active_watchers:
        watcher.stop()
    _active_watchers.clear()
    logger.info("Stopped all directory watchers")


def get_active_watchers_count() -> int:
    """
    Получение количества активных наблюдателей.
    
    Returns:
        Количество активных наблюдателей
    """
    return len(_active_watchers)


def format_disk_status(disks: list) -> str:
    """
    Форматирование статуса дисков для вывода.
    
    Args:
        disks: Список дисков
        
    Returns:
        Отформатированная строка
    """
    result = "💽 Disk Usage:\n\n"
    for disk in disks:
        percent = disk['percent']
        if percent < 50:
            status = "🟢"
        elif percent < 75:
            status = "🟡"
        elif percent < 90:
            status = "🟠"
        else:
            status = "🔴"
        
        result += f"{status} {disk['mountpoint']}: {disk['used_gb']:.1f}/{disk['total_gb']:.1f} GB ({percent:.1f}%)\n"
    
    return result


def get_full_system_report() -> str:
    """
    Получение полного отчёта о системе.
    
    Returns:
        Отформатированный отчёт
    """
    status = get_system_status()
    
    report = f"""🖥️ System Report
📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{format_cpu_status(status['cpu_percent'])}
{format_ram_status(status['ram'])}
{format_disk_status(status['disk'])}

⏱️ Uptime: {status['uptime']}
🚀 Boot Time: {status['boot_time']}
"""
    return report
