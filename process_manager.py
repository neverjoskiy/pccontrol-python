"""
Модуль управления процессами Windows.
Просмотр, запуск, завершение, перезапуск процессов, изменение приоритета.
"""

import logging
import subprocess
from typing import Optional

import psutil

logger = logging.getLogger(__name__)


def list_processes(limit: int = 50) -> list:
    """
    Получение списка запущенных процессов.
    
    Args:
        limit: Максимальное количество процессов для возврата
        
    Returns:
        Список словарей с информацией о процессах
    """
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
        try:
            mem_info = proc.info.get('memory_info')
            ram_mb = mem_info.rss / (1024 * 1024) if mem_info else 0
            processes.append({
                'pid': proc.info['pid'],
                'name': proc.info['name'] or 'Unknown',
                'ram': ram_mb,
                'cpu': proc.info.get('cpu_percent', 0)
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    # Сортировка по использованию RAM
    processes.sort(key=lambda x: x['ram'], reverse=True)
    return processes[:limit]


def get_process_info(pid: int) -> Optional[dict]:
    """
    Получение подробной информации о процессе.
    
    Args:
        pid: ID процесса
        
    Returns:
        Словарь с информацией или None если процесс не найден
    """
    try:
        proc = psutil.Process(pid)
        mem_info = proc.memory_info()
        return {
            'pid': pid,
            'name': proc.name(),
            'status': proc.status(),
            'ram': mem_info.rss / (1024 * 1024),
            'cpu': proc.cpu_percent(),
            'username': proc.username(),
            'create_time': proc.create_time(),
            'exe': proc.exe(),
            'cmdline': proc.cmdline()
        }
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
        logger.error(f"Ошибка получения информации о процессе {pid}: {e}")
        return None


def kill_process(pid: int) -> tuple[bool, str]:
    """
    Завершение процесса.
    
    Args:
        pid: ID процесса
        
    Returns:
        Кортеж (success, message)
    """
    try:
        proc = psutil.Process(pid)
        proc_name = proc.name()
        proc.kill()
        proc.wait(timeout=5)
        message = f"✅ Process '{proc_name}' (PID: {pid}) has been terminated."
        logger.info(message)
        return True, message
    except psutil.NoSuchProcess:
        message = f"❌ Process with PID {pid} not found."
        logger.warning(message)
        return False, message
    except psutil.AccessDenied:
        message = f"❌ Access denied to terminate process {pid}."
        logger.error(message)
        return False, message
    except Exception as e:
        message = f"❌ Error terminating process {pid}: {e}"
        logger.error(message)
        return False, message


def restart_process(pid: int) -> tuple[bool, str]:
    """
    Перезапуск процесса (завершение и новый запуск).

    Args:
        pid: ID процесса

    Returns:
        Кортеж (success, message)
    """
    try:
        proc = psutil.Process(pid)
        proc_name = proc.name()
        exe_path = proc.exe()
        cmdline = proc.cmdline()
        cwd = proc.cwd()

        proc.kill()
        proc.wait(timeout=5)

        if cmdline and len(cmdline) > 0:
            subprocess.Popen(cmdline, cwd=cwd)
        else:
            subprocess.Popen([exe_path], cwd=cwd)

        message = f"✅ Process '{proc_name}' (PID: {pid}) has been restarted."
        logger.info(message)
        return True, message
    except psutil.NoSuchProcess:
        message = f"❌ Process with PID {pid} not found."
        logger.warning(message)
        return False, message
    except psutil.AccessDenied:
        message = f"❌ Access denied to restart process {pid}."
        logger.error(message)
        return False, message
    except Exception as e:
        message = f"❌ Error restarting process {pid}: {e}"
        logger.error(message)
        return False, message


def change_priority(pid: int, priority: str) -> tuple[bool, str]:
    """
    Изменение приоритета процесса.
    
    Args:
        pid: ID процесса
        priority: Приоритет ('low', 'normal', 'high', 'realtime')
        
    Returns:
        Кортеж (success, message)
    """
    priority_map = {
        'low': psutil.BELOW_NORMAL_PRIORITY_CLASS,
        'normal': psutil.NORMAL_PRIORITY_CLASS,
        'high': psutil.HIGH_PRIORITY_CLASS,
        'realtime': psutil.REALTIME_PRIORITY_CLASS
    }
    
    if priority not in priority_map:
        return False, f"❌ Invalid priority: {priority}"
    
    try:
        proc = psutil.Process(pid)
        proc_name = proc.name()
        proc.nice(priority_map[priority])
        message = f"✅ Priority of '{proc_name}' (PID: {pid}) changed to {priority}."
        logger.info(message)
        return True, message
    except psutil.NoSuchProcess:
        message = f"❌ Process with PID {pid} not found."
        logger.warning(message)
        return False, message
    except psutil.AccessDenied:
        message = f"❌ Access denied to change priority of process {pid}."
        logger.error(message)
        return False, message
    except Exception as e:
        message = f"❌ Error changing priority of process {pid}: {e}"
        logger.error(message)
        return False, message


def run_process(file_path: str, args: str = "") -> tuple[bool, str]:
    """
    Запуск нового процесса.
    
    Args:
        file_path: Путь к исполняемому файлу
        args: Дополнительные аргументы командной строки
        
    Returns:
        Кортеж (success, message)
    """
    try:
        cmd = f'"{file_path}"'
        if args:
            cmd += f" {args}"
        
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        message = f"✅ Process started: {file_path} (PID: {process.pid})"
        logger.info(message)
        return True, message
    except FileNotFoundError:
        message = f"❌ File not found: {file_path}"
        logger.error(message)
        return False, message
    except PermissionError:
        message = f"❌ Permission denied to execute: {file_path}"
        logger.error(message)
        return False, message
    except Exception as e:
        message = f"❌ Error starting process: {e}"
        logger.error(message)
        return False, message


def search_process_by_name(name: str) -> list:
    """
    Поиск процесса по имени.
    
    Args:
        name: Имя процесса (часть имени)
        
    Returns:
        Список найденных процессов
    """
    processes = list_processes(limit=500)
    name_lower = name.lower()
    return [p for p in processes if name_lower in p['name'].lower()]


def watch_process(pid: int) -> Optional[dict]:
    """
    Получение текущей информации о процессе для мониторинга.
    
    Args:
        pid: ID процесса
        
    Returns:
        Словарь с текущей информацией или None
    """
    return get_process_info(pid)
