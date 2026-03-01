"""
Flask веб-интерфейс для управления ПК.
Работает параллельно с Telegram ботом.
"""

import os
import logging
from pathlib import Path
from functools import wraps

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import psutil

from security import verify_password

logger = logging.getLogger(__name__)

# Инициализация Flask
app = Flask(__name__)
app.secret_key = 'telegram_bot_web_secret_key_2024'

# Конфигурация загрузки файлов
UPLOADS_FOLDER = Path(__file__).parent / 'uploads'
UPLOADS_FOLDER.mkdir(exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOADS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB

ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'zip', 'rar', 
    'exe', 'msi', 'iso', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
    'mp3', 'mp4', 'avi', 'mkv', '7z'
}


def allowed_file(filename):
    """Проверка расширения файла."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def login_required(f):
    """Декоратор для проверки авторизации."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'authenticated' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа."""
    if request.method == 'POST':
        password = request.form.get('password', '')
        
        if verify_password(password):
            session['authenticated'] = True
            logger.info("✓ User logged in via web interface")
            return redirect(url_for('dashboard'))
        else:
            logger.warning("✗ Failed login attempt via web interface")
            return render_template('login.html', error='Неверный пароль')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Выход из аккаунта."""
    session.pop('authenticated', None)
    logger.info("User logged out from web interface")
    return redirect(url_for('login'))


@app.route('/')
@login_required
def dashboard():
    """Главная страница Dashboard."""
    try:
        # Информация о системе
        cpu_percent = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('C:\\')
        
        system_info = {
            'cpu_percent': cpu_percent,
            'cpu_count': psutil.cpu_count(),
            'ram_total_gb': round(ram.total / (1024**3), 2),
            'ram_used_gb': round(ram.used / (1024**3), 2),
            'ram_percent': ram.percent,
            'disk_total_gb': round(disk.total / (1024**3), 2),
            'disk_used_gb': round(disk.used / (1024**3), 2),
            'disk_percent': disk.percent,
        }
        
        # Список загруженных файлов
        uploaded_files = []
        if UPLOADS_FOLDER.exists():
            for file in UPLOADS_FOLDER.iterdir():
                if file.is_file():
                    uploaded_files.append({
                        'name': file.name,
                        'size_mb': round(file.stat().st_size / (1024**2), 2),
                        'modified': file.stat().st_mtime
                    })
        
        return render_template('dashboard.html', system_info=system_info, files=uploaded_files)
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return render_template('error.html', error=str(e))


@app.route('/api/system-info', methods=['GET'])
@login_required
def get_system_info():
    """API для получения информации о системе."""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('C:\\')
        
        return jsonify({
            'cpu_percent': cpu_percent,
            'ram_percent': ram.percent,
            'disk_percent': disk.percent,
            'ram_used_gb': round(ram.used / (1024**3), 2),
            'disk_used_gb': round(disk.used / (1024**3), 2),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Загрузка файла на ПК."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Файл не найден'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'Имя файла пусто'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Расширение файла не разрешено'}), 400
        
        filename = secure_filename(file.filename)
        filepath = UPLOADS_FOLDER / filename
        
        file.save(filepath)
        logger.info(f"✓ File uploaded: {filename}")
        
        return jsonify({
            'success': True,
            'message': f'Файл {filename} загружен успешно',
            'filename': filename,
            'size_mb': round(filepath.stat().st_size / (1024**2), 2)
        })
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'error': f'Ошибка загрузки: {str(e)}'}), 500


@app.route('/files/<filename>', methods=['GET'])
@login_required
def download_file(filename):
    """Скачивание загруженного файла."""
    try:
        filename = secure_filename(filename)
        filepath = UPLOADS_FOLDER / filename
        
        if not filepath.exists():
            return jsonify({'error': 'Файл не найден'}), 404
        
        logger.info(f"✓ File downloaded: {filename}")
        return send_from_directory(UPLOADS_FOLDER, filename)
    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/files/<filename>', methods=['DELETE'])
@login_required
def delete_file(filename):
    """Удаление загруженного файла."""
    try:
        filename = secure_filename(filename)
        filepath = UPLOADS_FOLDER / filename
        
        if not filepath.exists():
            return jsonify({'error': 'Файл не найден'}), 404
        
        filepath.unlink()
        logger.info(f"✓ File deleted: {filename}")
        
        return jsonify({'success': True, 'message': f'Файл {filename} удален'})
    except Exception as e:
        logger.error(f"Delete error: {e}")
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    """Обработка 404."""
    return render_template('error.html', error='Страница не найдена'), 404


@app.errorhandler(500)
def server_error(error):
    """Обработка 500."""
    return render_template('error.html', error='Ошибка сервера'), 500


def start_web_server(port=5000):
    """Запуск веб-сервера."""
    logger.info(f"🌐 Starting web server on http://localhost:{port}")
    app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)


if __name__ == '__main__':
    start_web_server()
