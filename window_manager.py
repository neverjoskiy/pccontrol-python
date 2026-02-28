"""
Модуль управления окнами и эмуляции ввода.
Список окон, закрытие, сворачивание, горячие клавиши.
"""

import logging
import time
import ctypes
import subprocess
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

SW_MINIMIZE = 6
SW_MAXIMIZE = 3
SW_RESTORE = 9

def get_open_windows() -> List[Dict]:
    """
    Получение списка открытых окон с их заголовками и PID.
    Использует PowerShell для простоты.
    """
    try:
        ps_script = 'Get-Process | Where-Object { $_.MainWindowTitle } | Select-Object Id, Name, MainWindowTitle | ForEach-Object { "$($_.Id)|$($_.Name)|$($_.MainWindowTitle)" }'
        result = subprocess.run(['powershell', '-Command', ps_script], capture_output=True, text=True, encoding='cp866')
        
        windows = []
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                if '|' in line:

                    parts = line.split('|')
                    if len(parts) >= 3:
                        windows.append({
                            'pid': parts[0],
                            'name': parts[1],
                            'title': parts[2]
                        })
        return windows
    except Exception as e:
        logger.error(f"Error getting windows: {e}")
        return []

def close_window(pid: int) -> bool:
    """Закрытие окна (процесса) по PID."""
    try:
        import psutil
        process = psutil.Process(pid)
        process.terminate()
        return True
    except Exception as e:
        logger.error(f"Error closing window {pid}: {e}")
        return False

def press_hotkey(keys: List[str]):
    """
    Эмуляция нажатия горячих клавиш.
    keys: список клавиш, например ['win', 'd'] или ['alt', 'f4']
    """
    try:
        import pyautogui
        pyautogui.hotkey(*keys)
        return True, f"✅ Pressed: {'+'.join(keys)}"
    except ImportError:
        key_map = {
            'win': '^{ESC}',
            'alt': '%',
            'ctrl': '^',
            'shift': '+',
            'f4': '{F4}',
            'd': 'd',
            'l': 'l'
        }

        if 'win' in keys and 'd' in keys:
            ps_cmd = "(New-Object -ComObject shell.application).ToggleDesktop()"
        elif 'win' in keys and 'l' in keys:
            ps_cmd = "rundll32.exe user32.dll,LockWorkStation"
        else:
            send_keys = ""
            for k in keys:
                send_keys += key_map.get(k.lower(), k)
            ps_cmd = f"$wshell = New-Object -ComObject WScript.Shell; $wshell.SendKeys('{send_keys}')"

        subprocess.run(['powershell', '-Command', ps_cmd])
        return True, f"✅ Executed via PS: {'+'.join(keys)}"

def minimize_all():
    """Свернуть все окна (Win+D)."""
    return press_hotkey(['win', 'd'])


def get_active_window() -> str:
    """Получение заголовка текущего активного окна."""
    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value if buf.value else "Unknown"
    except Exception:
        return "Unknown"


def move_mouse(dx: int, dy: int):
    """Относительное перемещение мыши."""
    try:
        import ctypes
        MOUSEEVENTF_MOVE = 0x0001
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_MOVE, dx, dy, 0, 0)
        return True
    except Exception:
        return False


def mouse_click(button: str = 'left'):
    """Клик мышью."""
    try:
        import ctypes
        if button == 'left':
            events = [0x0002, 0x0004] # Down, Up
        else:
            events = [0x0008, 0x0010] # Right Down, Up
        for event in events:
            ctypes.windll.user32.mouse_event(event, 0, 0, 0, 0)
        return True
    except Exception:
        return False
