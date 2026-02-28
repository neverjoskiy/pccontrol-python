"""
Модуль управления системой Windows.
Выключение, перезагрузка, сон, блокировка, скриншоты, веб-камера, микрофон, буфер обмена.
"""

import logging
import subprocess
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def shutdown_pc(timeout: int = 5) -> tuple[bool, str]:
    """
    Выключение компьютера.
    
    Args:
        timeout: Задержка в секундах перед выключением
        
    Returns:
        Кортеж (success, message)
    """
    try:
        subprocess.run(
            ['shutdown', '/s', '/f', '/t', str(timeout)],
            check=True
        )
        message = f"✅ System shutdown initiated (in {timeout} seconds)."
        logger.warning(message)
        return True, message
    except subprocess.CalledProcessError as e:
        message = f"❌ Error initiating shutdown: {e}"
        logger.error(message)
        return False, message
    except Exception as e:
        message = f"❌ Unexpected error during shutdown: {e}"
        logger.error(message)
        return False, message


def restart_pc(timeout: int = 5) -> tuple[bool, str]:
    """
    Перезагрузка компьютера.
    
    Args:
        timeout: Задержка в секундах перед перезагрузкой
        
    Returns:
        Кортеж (success, message)
    """
    try:
        subprocess.run(
            ['shutdown', '/r', '/f', '/t', str(timeout)],
            check=True
        )
        message = f"✅ System restart initiated (in {timeout} seconds)."
        logger.warning(message)
        return True, message
    except subprocess.CalledProcessError as e:
        message = f"❌ Error initiating restart: {e}"
        logger.error(message)
        return False, message
    except Exception as e:
        message = f"❌ Unexpected error during restart: {e}"
        logger.error(message)
        return False, message


def sleep_pc() -> tuple[bool, str]:
    """
    Перевод компьютера в спящий режим.
    
    Returns:
        Кортеж (success, message)
    """
    try:
        # Используем PowerShell для перехода в спящий режим
        subprocess.run(
            ['powershell', '-Command', '(Add-Type -PassThru -TypeDefinition \"using System;using System.Runtime.InteropServices;public class PInvoke { [DllImport(\\\"powrprof.dll\\\") public static extern uint SetSuspendState(bool bHibernate, bool bForce, bool bWakeup);] }\" -Language CSharp).SetSuspendState(0,1,0)'],
            check=True
        )
        message = "✅ System entering sleep mode."
        logger.info(message)
        return True, message
    except subprocess.CalledProcessError as e:
        message = f"❌ Error entering sleep mode: {e}"
        logger.error(message)
        return False, message
    except Exception as e:
        message = f"❌ Unexpected error during sleep: {e}"
        logger.error(message)
        return False, message


def lock_pc() -> tuple[bool, str]:
    """
    Блокировка компьютера.
    
    Returns:
        Кортеж (success, message)
    """
    try:
        subprocess.run(
            ['rundll32.exe', 'user32.dll,LockWorkStation'],
            check=True
        )
        message = "✅ System locked."
        logger.info(message)
        return True, message
    except subprocess.CalledProcessError as e:
        message = f"❌ Error locking system: {e}"
        logger.error(message)
        return False, message
    except Exception as e:
        message = f"❌ Unexpected error during lock: {e}"
        logger.error(message)
        return False, message


def take_screenshot(save_path: Optional[str] = None) -> tuple[bool, str, Optional[bytes]]:
    """
    Создание скриншота экрана.

    Args:
        save_path: Путь для сохранения (опционально)

    Returns:
        Кортеж (success, message, image_data)
        image_data: Байты изображения или None
    """
    try:
        from PIL import ImageGrab
        import io

        screenshot = ImageGrab.grab()

        buffer = io.BytesIO()
        screenshot.save(buffer, format='PNG')
        image_data = buffer.getvalue()
        buffer.close()

        if save_path:
            screenshot.save(save_path)

        message = f"✅ Screenshot captured ({len(image_data)} bytes)."
        logger.info(message)
        return True, message, image_data
    except ImportError:
        # Пробуем через PowerShell
        try:
            import tempfile
            temp_path = Path(tempfile.gettempdir()) / f"screenshot_{int(time.time())}.png"
            
            ps_script = f"""
            Add-Type -AssemblyName System.Windows.Forms
            Add-Type -AssemblyName System.Drawing
            $screen = [System.Windows.Forms.Screen]::PrimaryScreen
            $bitmap = New-Object System.Drawing.Bitmap $screen.Bounds.Width, $screen.Bounds.Height
            $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
            $graphics.CopyFromScreen($screen.Bounds.Location, [System.Drawing.Point]::Empty, $screen.Bounds.Size)
            $bitmap.Save('{temp_path}')
            $graphics.Dispose()
            $bitmap.Dispose()
            """
            
            subprocess.run(['powershell', '-Command', ps_script], check=True)
            
            with open(temp_path, 'rb') as f:
                image_data = f.read()
            
            message = f"✅ Screenshot captured: {temp_path}"
            logger.info(message)
            return True, message, image_data
        except Exception as e:
            message = f"❌ Error taking screenshot via PowerShell: {e}"
            logger.error(message)
            return False, message, None
    except Exception as e:
        message = f"❌ Error taking screenshot: {e}"
        logger.error(message)
        return False, message, None


def capture_webcam(save_path: Optional[str] = None) -> tuple[bool, str, Optional[bytes]]:
    """
    Снимок с веб-камеры.

    Args:
        save_path: Путь для сохранения (опционально)

    Returns:
        Кортеж (success, message, image_data)
    """
    try:
        import cv2
        import tempfile

        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            return False, "❌ No webcam found or access denied.", None

        ret, frame = cap.read()
        cap.release()

        if not ret:
            return False, "❌ Failed to capture image from webcam.", None

        if save_path:
            cv2.imwrite(save_path, frame)
            message = f"✅ Webcam photo saved: {save_path}"
            with open(save_path, 'rb') as f:
                image_data = f.read()
        else:
            import tempfile
            temp_path = Path(tempfile.gettempdir()) / f"webcam_{int(time.time())}.jpg"
            cv2.imwrite(str(temp_path), frame)
            with open(temp_path, 'rb') as f:
                image_data = f.read()
            temp_path.unlink()
            message = "✅ Webcam photo captured."

        logger.info(message)
        return True, message, image_data
    except ImportError:
        message = "❌ OpenCV (cv2) not installed. Install with: pip install opencv-python"
        logger.error(message)
        return False, message, None
    except Exception as e:
        message = f"❌ Error capturing webcam: {e}"
        logger.error(message)
        return False, message, None


def record_audio(duration: int = 10, save_path: Optional[str] = None) -> tuple[bool, str, Optional[bytes]]:
    """
    Запись аудио с микрофона.

    Args:
        duration: Длительность записи в секундах
        save_path: Путь для сохранения (опционально)

    Returns:
        Кортеж (success, message, audio_data)
    """
    try:
        import pyaudio
        import wave
        import tempfile
        import io

        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100

        p = pyaudio.PyAudio()

        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )

        frames = []

        for _ in range(0, int(RATE / CHUNK * duration)):
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)

        stream.stop_stream()
        stream.close()
        p.terminate()

        audio_buffer = io.BytesIO()
        wf = wave.open(audio_buffer, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

        audio_data = audio_buffer.getvalue()
        audio_buffer.close()

        if save_path:
            with open(save_path, 'wb') as f:
                f.write(audio_data)
            message = f"✅ Audio recorded ({duration}s) and saved: {save_path}"
        else:
            message = f"✅ Audio recorded ({duration}s, {len(audio_data)} bytes)."

        logger.info(message)
        return True, message, audio_data
    except ImportError:
        message = "❌ PyAudio not installed. Install with: pip install pyaudio"
        logger.error(message)
        return False, message, None
    except Exception as e:
        message = f"❌ Error recording audio: {e}"
        logger.error(message)
        return False, message, None


def get_clipboard_content() -> tuple[bool, str, Optional[str]]:
    """
    Получение содержимого буфера обмена.
    
    Returns:
        Кортеж (success, message, content)
    """
    try:
        import pyperclip
        
        content = pyperclip.paste()
        message = f"✅ Clipboard content retrieved ({len(content)} chars)."
        logger.info(message)
        return True, message, content
    except ImportError:
        # Пробуем через PowerShell
        try:
            result = subprocess.run(
                ['powershell', '-Command', 'Get-Clipboard'],
                capture_output=True,
                text=True,
                check=True
            )
            content = result.stdout
            message = f"✅ Clipboard content retrieved ({len(content)} chars)."
            logger.info(message)
            return True, message, content
        except Exception as e:
            message = f"❌ Error getting clipboard: {e}"
            logger.error(message)
            return False, message, None
    except Exception as e:
        message = f"❌ Error getting clipboard: {e}"
        logger.error(message)
        return False, message, None


def set_clipboard_content(text: str) -> tuple[bool, str]:
    """
    Установка содержимого буфера обмена.
    
    Args:
        text: Текст для установки в буфер
        
    Returns:
        Кортеж (success, message)
    """
    try:
        import pyperclip
        
        pyperclip.copy(text)
        message = f"✅ Clipboard set ({len(text)} chars)."
        logger.info(message)
        return True, message
    except ImportError:
        # Пробуем через PowerShell
        try:
            process = subprocess.Popen(
                ['powershell', '-Command', 'Set-Clipboard'],
                stdin=subprocess.PIPE,
                text=True
            )
            process.communicate(text)
            message = f"✅ Clipboard set ({len(text)} chars)."
            logger.info(message)
            return True, message
        except Exception as e:
            message = f"❌ Error setting clipboard: {e}"
            logger.error(message)
            return False, message
    except Exception as e:
        message = f"❌ Error setting clipboard: {e}"
        logger.error(message)
        return False, message


def get_system_info() -> dict:
    """
    Получение информации о системе.
    
    Returns:
        Словарь с информацией о системе
    """
    import platform
    import psutil
    
    info = {
        'platform': platform.system(),
        'platform_release': platform.release(),
        'platform_version': platform.version(),
        'architecture': platform.machine(),
        'hostname': platform.node(),
        'processor': platform.processor(),
        'ram_total': f"{psutil.virtual_memory().total / (1024**3):.1f} GB",
        'cpu_count': psutil.cpu_count(),
    }
    
    return info


def clean_temp_files() -> tuple[bool, str, int]:
    """
    Очистка временных файлов Windows и корзины.

    Returns:
        Кортеж (success, message, deleted_size_mb)
    """
    import os
    import shutil

    deleted_size = 0
    errors = 0

    temp_paths = [
        os.environ.get('TEMP'),
        os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Temp'),
        os.path.join(os.environ.get('LocalAppData', ''), 'Temp'),
    ]

    try:
        subprocess.run(['powershell', '-Command', 'Clear-RecycleBin -Force -ErrorAction SilentlyContinue'], capture_output=True)
    except:
        pass

    for path in temp_paths:
        if not path or not os.path.exists(path):
            continue

        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            try:
                current_size = 0
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    current_size = os.path.getsize(item_path)
                    os.unlink(item_path)
                elif os.path.is_dir(item_path):
                    for root, dirs, files in os.walk(item_path):
                        for f in files:
                            fp = os.path.join(root, f)
                            if os.path.exists(fp):
                                current_size += os.path.getsize(fp)
                    shutil.rmtree(item_path)
                deleted_size += current_size
            except Exception:
                errors += 1

    size_mb = deleted_size / (1024 * 1024)
    message = f"✅ Cleanup finished. Deleted: {size_mb:.2f} MB. Skipped {errors} files (in use)."
    logger.info(message)
    return True, message, int(size_mb)


def get_top_large_folders(drive: str = "C:\\", count: int = 10) -> tuple[bool, str]:
    """
    Поиск топ-10 самых тяжелых папок на диске.
    Использует PowerShell для быстрого сканирования.
    """
    try:
        # PowerShell скрипт для поиска тяжелых папок (только первый уровень для скорости)
        ps_script = f"""
        Get-ChildItem -Path '{drive}' -ErrorAction SilentlyContinue | 
        Where-Object {{ $_.PSIsContainer }} | 
        Select-Object Name, @{{Name="Size";Expression={{ (Get-ChildItem $_.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB }}}} | 
        Sort-Object Size -Descending | 
        Select-Object -First {count} | 
        ForEach-Object {{ "$($_.Name)|$([Math]::Round($_.Size, 2))" }}
        """
        
        result = subprocess.run(['powershell', '-Command', ps_script], capture_output=True, text=True, encoding='cp866')
        
        if not result.stdout.strip():
            return False, "❌ No folders found or access denied."
            
        lines = result.stdout.strip().split('\n')
        report = f"📊 Top {count} largest folders on {drive}:\n\n"
        for line in lines:
            if '|' in line:
                name, size = line.split('|')
                report += f"📁 {name}: {size} MB\n"
        
        return True, report
    except Exception as e:
        message = f"❌ Error analyzing disk: {e}"
        logger.error(message)
        return False, message


def turn_off_monitor() -> tuple[bool, str]:
    """Выключение монитора (энергосбережение)."""
    try:
        import ctypes
        ctypes.windll.user32.SendMessageW(0xFFFF, 0x0112, 0xF170, 2)
        return True, "✅ Monitor turned off."
    except Exception as e:
        logger.error(f"Error turning off monitor: {e}")
        subprocess.run(['powershell', '-Command', '(Add-Type -PassThru -TypeDefinition "using System; using System.Runtime.InteropServices; public class Power { [DllImport(\"user32.dll\")] public static extern int SendMessage(int hWnd, int hMsg, int wParam, int lParam); }").SendMessage(0xFFFF, 0x0112, 0xF170, 2)'], shell=True)
        return True, "✅ Monitor turned off (via PS)."


def open_url(url: str) -> tuple[bool, str]:
    """Открытие URL в браузере по умолчанию."""
    try:
        import webbrowser
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        webbrowser.open(url)
        return True, f"✅ URL opened: {url}"
    except Exception as e:
        return False, f"❌ Failed to open URL: {e}"
