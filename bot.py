"""
Основной модуль Telegram-бота.
Обработчики команд, callback-запросов, файлов.
"""

import logging
import os
import base64
import json
from pathlib import Path
from typing import Optional
import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

import keyboards
import security
import process_manager
import file_manager
import system_manager
import network_manager
import monitor
import window_manager

logger = logging.getLogger(__name__)

path_cache: dict[int, dict[str, str]] = {}


def encode_path(path: str) -> str:
    """Кодирует путь в base64 для использования в callback_data."""
    encoded = base64.b64encode(path.encode('utf-8')).decode('utf-8')
    return encoded[:60]


def decode_path(encoded: str) -> str:
    """Декодирует путь из base64."""
    padding = 4 - len(encoded) % 4
    if padding != 4:
        encoded += '=' * padding
    return base64.b64decode(encoded).decode('utf-8')


user_states: dict[int, dict] = {}


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start."""
    user_id = update.effective_user.id

    if not security.is_user_allowed(user_id):
        await update.message.reply_text(
            f"👋 Welcome, {update.effective_user.first_name}!\n\n"
            "🔐 You need to authenticate first.\n"
            "Use /auth command and enter the password to access all functions."
        )
        return

    await update.message.reply_text(
        f"👋 Welcome, {update.effective_user.first_name}!\n\n"
        "Use the menu buttons below to control the system.",
        reply_markup=keyboards.get_main_menu()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help."""
    help_text = """
🤖 Advanced System Control Bot

📋 Available Commands:
/start - Show main menu
/help - Show this help
/status - Show system status
/auth - Authenticate with password

🔘 All functions are available via inline buttons.
"""
    await update.message.reply_text(help_text)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /status."""
    user_id = update.effective_user.id
    
    if not security.check_access(user_id)[0]:
        await update.message.reply_text("🚫 Access Denied!")
        return
    
    report = monitor.get_full_system_report()
    await update.message.reply_text(f"```\n{report}\n```", parse_mode='Markdown')


async def auth_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /auth для аутентификации."""
    await update.message.reply_text(
        "🔐 Enter the password to authenticate:\n\n"
        "Send the password as a message."
    )
    user_states[update.effective_user.id] = {'action': 'auth_password'}


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена текущего действия."""
    user_id = update.effective_user.id
    if user_id in user_states:
        del user_states[user_id]
    
    await update.message.reply_text(
        "❌ Action cancelled.",
        reply_markup=keyboards.get_main_menu()
    )
    return ConversationHandler.END


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на inline-кнопки."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    has_access, error_msg = security.check_access(user_id)
    if not has_access:
        await query.edit_message_text(error_msg)
        return

    if data == "menu_main":
        await query.edit_message_text("📋 Main Menu", reply_markup=keyboards.get_main_menu())
    
    # Process Manager
    elif data == "menu_process":
        await query.edit_message_text("📋 Process Manager", reply_markup=keyboards.get_process_menu())
    elif data == "proc_list":
        await list_processes_callback(query, user_id)
    elif data == "proc_run":
        await query.edit_message_text(
            "▶️ Run Process\n\n"
            "Send the full file path to execute:\n"
            "Example: C:\\Windows\\System32\\notepad.exe"
        )
        user_states[user_id] = {'action': 'run_process'}
    elif data == "proc_kill":
        await query.edit_message_text(
            "❌ Kill Process\n\n"
            "Send the PID of the process to kill."
        )
        user_states[user_id] = {'action': 'kill_process'}
    elif data == "proc_restart":
        await query.edit_message_text(
            "🔄 Restart Process\n\n"
            "Send the PID of the process to restart."
        )
        user_states[user_id] = {'action': 'restart_process'}
    elif data == "proc_priority":
        await query.edit_message_text(
            "🎯 Change Priority\n\n"
            "Send PID and priority (low/normal/high/realtime):\n"
            "Example: 1234 high"
        )
        user_states[user_id] = {'action': 'change_priority'}
    elif data == "proc_watch":
        await query.edit_message_text(
            "👁️ Watch Process\n\n"
            "Send the PID to monitor."
        )
        user_states[user_id] = {'action': 'watch_process'}
    
    # File Explorer
    elif data == "menu_files":
        await show_drives(query)
    elif data == "file_root":
        await show_drives(query)
    elif data == "file_back":
        await show_drives(query)
    elif data == "file_refresh":
        current_path = security.get_user_directory(user_id)
        await browse_directory(query, current_path)
    elif data.startswith("drive_"):
        drive = data.replace("drive_", "") + ":\\"
        await browse_directory(query, drive)
    elif data.startswith("dirb_"):
        encoded_path = data.replace("dirb_", "", 1)
        dir_path = decode_path(encoded_path)
        await browse_directory(query, dir_path)
    elif data == "dir_up":
        current_path = security.get_user_directory(user_id)
        parent = file_manager.get_parent_directory(current_path)
        await browse_directory(query, parent)
    elif data.startswith("fileb_"):
        encoded_path = data.replace("fileb_", "", 1)
        file_path = decode_path(encoded_path)
        await show_file_actions(query, file_path, user_id)
    elif data.startswith("file_downloadb_"):
        encoded_path = data.replace("file_downloadb_", "", 1)
        file_path = decode_path(encoded_path)
        await download_file_callback(query, file_path)
    elif data.startswith("file_deleteb_"):
        encoded_path = data.replace("file_deleteb_", "", 1)
        file_path = decode_path(encoded_path)
        success, msg = file_manager.delete_file(file_path)
        await query.edit_message_text(msg)
    elif data.startswith("file_renameb_"):
        encoded_path = data.replace("file_renameb_", "", 1)
        file_path = decode_path(encoded_path)
        await query.edit_message_text(
            f"✏️ Rename File\n\n"
            f"Current: {file_path}\n\n"
            "Send the new name:"
        )
        user_states[user_id] = {'action': 'rename_file', 'file_path': file_path}
    elif data.startswith("file_moveb_"):
        encoded_path = data.replace("file_moveb_", "", 1)
        file_path = decode_path(encoded_path)
        await query.edit_message_text(
            f"📦 Move File\n\n"
            f"File: {file_path}\n\n"
            "Send the destination path:"
        )
        user_states[user_id] = {'action': 'move_file', 'file_path': file_path}
    elif data.startswith("file_copyb_"):
        encoded_path = data.replace("file_copyb_", "", 1)
        file_path = decode_path(encoded_path)
        await query.edit_message_text(
            f"📄 Copy File\n\n"
            f"File: {file_path}\n\n"
            "Send the destination path:"
        )
        user_states[user_id] = {'action': 'copy_file', 'file_path': file_path}
    
    # System Control
    elif data == "menu_system":
        await query.edit_message_text("⚙️ System Control", reply_markup=keyboards.get_system_menu())
    elif data == "sys_shutdown":
        await query.edit_message_text("⚠️ Confirm shutdown?")
        user_states[user_id] = {'action': 'confirm_shutdown'}
    elif data == "sys_restart":
        await query.edit_message_text("⚠️ Confirm restart?")
        user_states[user_id] = {'action': 'confirm_restart'}
    elif data == "sys_sleep":
        success, msg = system_manager.sleep_pc()
        await query.edit_message_text(msg)
    elif data == "sys_lock":
        success, msg = system_manager.lock_pc()
        await query.edit_message_text(msg)
    elif data == "sys_screenshot":
        await query.edit_message_text("📸 Taking screenshot...")
        success, msg, image_data = system_manager.take_screenshot()
        if success and image_data:
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=image_data,
                caption=msg
            )
            await query.delete_message()
        else:
            await query.edit_message_text(msg)
    elif data == "sys_webcam":
        await query.edit_message_text("📷 Capturing from webcam...")
        success, msg, image_data = system_manager.capture_webcam()
        if success and image_data:
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=image_data,
                caption=msg
            )
            await query.delete_message()
        else:
            await query.edit_message_text(msg)
    elif data == "sys_mic_record":
        await query.edit_message_text("🎤 Recording audio (10 seconds)...")
        success, msg, audio_data = system_manager.record_audio(duration=10)
        if success and audio_data:
            await context.bot.send_voice(
                chat_id=query.message.chat_id,
                voice=audio_data,
                caption=msg
            )
            await query.delete_message()
        else:
            await query.edit_message_text(msg)
    elif data == "sys_clipboard":
        success, msg, content = system_manager.get_clipboard_content()
        if success:
            if len(content) > 4000:
                content = content[:4000] + "... (truncated)"
            await query.edit_message_text(f"{msg}\n\n```\n{content}\n```", parse_mode='Markdown')
        else:
            await query.edit_message_text(msg)
    elif data == "sys_cleanup":
        await query.edit_message_text("🧹 Cleaning up temporary files...")
        success, msg, size = system_manager.clean_temp_files()
        await query.edit_message_text(msg, reply_markup=keyboards.get_system_menu())
    elif data == "sys_disk_top":
        await query.edit_message_text("📊 Analyzing disk C:\\... This may take a moment.")
        success, msg = system_manager.get_top_large_folders("C:\\")
        await query.edit_message_text(msg, reply_markup=keyboards.get_system_menu())
    elif data == "sys_monitor_off":
        success, msg = system_manager.turn_off_monitor()
        await query.edit_message_text(msg, reply_markup=keyboards.get_system_menu())
    elif data == "sys_set_timer":
        await query.edit_message_text("⏰ Select timer duration and action:", reply_markup=keyboards.get_timer_menu())
    elif data.startswith("timer_sleep_"):
        minutes = int(data.replace("timer_sleep_", ""))
        await start_timer(query, minutes, 'sleep')
    elif data.startswith("timer_shutdown_"):
        minutes = int(data.replace("timer_shutdown_", ""))
        await start_timer(query, minutes, 'shutdown')
    
    # Network Tools
    elif data == "menu_network":
        await query.edit_message_text("🌐 Network Tools", reply_markup=keyboards.get_network_menu())
    elif data == "net_show_ip":
        success, msg, ip = network_manager.get_public_ip()
        await query.edit_message_text(msg)
    elif data == "net_ping":
        await query.edit_message_text(
            "📡 Ping Host\n\n"
            "Send the hostname or IP to ping:"
        )
        user_states[user_id] = {'action': 'ping_host'}
    elif data == "net_netstat":
        success, msg = network_manager.netstat()
        if len(msg) > 4000:
            msg = msg[:4000] + "... (truncated)"
        await query.edit_message_text(msg, parse_mode='Markdown')
    elif data == "net_dns":
        await query.edit_message_text(
            "🔍 DNS Lookup\n\n"
            "Send the hostname to lookup:"
        )
        user_states[user_id] = {'action': 'dns_lookup'}
    elif data == "net_speedtest":
        await query.edit_message_text("⚡ Running speedtest... This may take a minute.")
        success, msg = network_manager.run_speedtest()
        await query.edit_message_text(msg)
    
    # Monitoring
    elif data == "menu_monitor":
        await query.edit_message_text("📊 Monitoring", reply_markup=keyboards.get_monitor_menu())
    elif data == "mon_cpu":
        cpu = monitor.get_cpu_usage(1)
        msg = monitor.format_cpu_status(cpu)
        await query.edit_message_text(msg)
    elif data == "mon_ram":
        ram = monitor.get_ram_usage()
        msg = monitor.format_ram_status(ram)
        await query.edit_message_text(msg)
    elif data == "mon_watch_dir":
        await query.edit_message_text(
            "👁️ Watch Directory\n\n"
            "Send the directory path to monitor:"
        )
        user_states[user_id] = {'action': 'watch_directory'}
    elif data == "mon_stop":
        monitor.stop_all_watchers()
        await query.edit_message_text("⏹️ All monitoring stopped.")
    
    # Extra Tools
    elif data == "menu_extra":
        await query.edit_message_text("🛠️ Extra Tools", reply_markup=keyboards.get_extra_menu())
    elif data == "extra_cmd":
        await query.edit_message_text(
            "💻 Execute CMD Command\n\n"
            "Send the command to execute:"
        )
        user_states[user_id] = {'action': 'execute_cmd'}
    elif data == "extra_keylogger":
        is_active = security.is_keylogger_active()
        security.set_keylogger_status(not is_active)
        status = "enabled" if not is_active else "disabled"
        await query.edit_message_text(f"⌨️ Keylogger {status}.")
    elif data == "extra_windows":
        windows = window_manager.get_open_windows()
        if not windows:
            await query.edit_message_text("❌ No open windows found.", reply_markup=keyboards.get_extra_menu())
        else:
            await query.edit_message_text("🪟 Select window:", reply_markup=keyboards.get_window_list_keyboard(windows))
    elif data == "extra_hotkeys":
        await query.edit_message_text("⌨️ Select Hotkey:", reply_markup=keyboards.get_hotkey_menu())
    elif data.startswith("win_action_"):
        pid = int(data.replace("win_action_", ""))
        await query.edit_message_text(f"Window PID: {pid}\nSelect action:", reply_markup=keyboards.get_window_action_keyboard(pid))
    elif data.startswith("win_close_"):
        pid = int(data.replace("win_close_", ""))
        if window_manager.close_window(pid):
            await query.edit_message_text(f"✅ Window {pid} closed.", reply_markup=keyboards.get_extra_menu())
        else:
            await query.edit_message_text(f"❌ Failed to close window {pid}.", reply_markup=keyboards.get_extra_menu())
    elif data == "hk_win_d":
        window_manager.press_hotkey(['win', 'd'])
        await query.answer("Desktop toggled")
    elif data == "hk_alt_f4":
        window_manager.press_hotkey(['alt', 'f4'])
        await query.answer("Alt+F4 pressed")
    elif data == "hk_win_e":
        window_manager.press_hotkey(['win', 'e'])
        await query.answer("Explorer opened")
    elif data == "extra_open_url":
        await query.edit_message_text(
            "🌐 Open URL\n\n"
            "Send the URL to open (e.g., google.com or https://google.com):"
        )
        user_states[user_id] = {'action': 'open_url'}
    elif data == "extra_active_window":
        active_window_title = window_manager.get_active_window()
        await query.edit_message_text(f"🪟 Active Window: {active_window_title}", reply_markup=keyboards.get_extra_menu())
    elif data == "extra_mouse":
        await query.edit_message_text("🖱️ Remote Mouse Control", reply_markup=keyboards.get_mouse_menu())
    elif data.startswith("mouse_move_"):
        _, dx_str, dy_str = data.split("_")
        dx, dy = int(dx_str), int(dy_str)
        if window_manager.move_mouse(dx, dy):
            await query.answer(f"Moved mouse by ({dx}, {dy})")
        else:
            await query.answer("❌ Failed to move mouse.")
    elif data.startswith("mouse_click_"):
        button = data.replace("mouse_click_", "")
        if window_manager.mouse_click(button):
            await query.answer(f"Clicked {button} button.")
        else:
            await query.answer("❌ Failed to click mouse.")
    elif data == "extra_clipboard_set":
        await query.edit_message_text(
            "📋 Set Clipboard\n\n"
            "Send the text to set:"
        )
        user_states[user_id] = {'action': 'set_clipboard'}
    elif data == "extra_audio":
        await query.edit_message_text("🎵 Recording audio (10 seconds)...")
        success, msg, audio_data = system_manager.record_audio(duration=10)
        if success and audio_data:
            await context.bot.send_voice(
                chat_id=query.message.chat_id,
                voice=audio_data,
                caption=msg
            )
            await query.delete_message()
        else:
            await query.edit_message_text(msg)
    elif data == "extra_startup_on":
        security.set_startup_status(True)
        await query.edit_message_text("🚀 Startup enabled.")
    elif data == "extra_startup_off":
        security.set_startup_status(False)
        await query.edit_message_text("🚫 Startup disabled.")
    
    # Settings
    elif data == "menu_settings":
        await query.edit_message_text("🔒 Settings", reply_markup=keyboards.get_settings_menu())
    elif data == "set_users":
        users = security.get_allowed_users()
        users_str = ", ".join(str(u) for u in users) if users else "None"
        await query.edit_message_text(f"👥 Allowed Users:\n\n`{users_str}`", parse_mode='Markdown')
    elif data == "set_password":
        await query.edit_message_text(
            "🔑 Change Password\n\n"
            "Send the new password:"
        )
        user_states[user_id] = {'action': 'change_password'}
    elif data == "set_status":
        report = monitor.get_full_system_report()
        await query.edit_message_text(f"```\n{report}\n```", parse_mode='Markdown')
    
    # Process actions from list
    elif data.startswith("proc_action_"):
        pid = int(data.replace("proc_action_", ""))
        await query.edit_message_text(
            f"Process PID: {pid}\n\nSelect action:",
            reply_markup=keyboards.get_process_action_keyboard(pid)
        )
    elif data.startswith("proc_kill_pid_"):
        pid = int(data.replace("proc_kill_pid_", ""))
        success, msg = process_manager.kill_process(pid)
        await query.edit_message_text(msg)
    elif data.startswith("proc_restart_pid_"):
        pid = int(data.replace("proc_restart_pid_", ""))
        success, msg = process_manager.restart_process(pid)
        await query.edit_message_text(msg)
    
    # Confirmations
    elif data.startswith("confirm_"):
        parts = data.replace("confirm_", "").split("_", 1)
        action = parts[0]
        if action == "shutdown":
            success, msg = system_manager.shutdown_pc()
            await query.edit_message_text(msg)
        elif action == "restart":
            success, msg = system_manager.restart_pc()
            await query.edit_message_text(msg)
    
    elif data == "cancel_action":
        if user_id in user_states:
            del user_states[user_id]
        await query.edit_message_text(
            "❌ Action cancelled.",
            reply_markup=keyboards.get_main_menu()
        )
    
    elif data == "cancel_input":
        if user_id in user_states:
            del user_states[user_id]
        await query.edit_message_text(
            "❌ Input cancelled.",
            reply_markup=keyboards.get_main_menu()
        )


async def list_processes_callback(query, user_id: int):
    """Callback для отображения списка процессов."""
    processes = process_manager.list_processes(limit=30)

    if not processes:
        await query.edit_message_text("❌ No processes found.")
        return

    text = "📋 Running Processes (sorted by RAM):\n\n"
    for i, proc in enumerate(processes[:20], 1):
        text += f"{i}. {proc['name']} (PID: {proc['pid']} | RAM: {proc['ram']:.1f} MB)\n"

    if len(processes) > 20:
        text += f"\n... and {len(processes) - 20} more"

    keyboard = []
    for proc in processes[:15]:
        keyboard.append([
            InlineKeyboardButton(
                f"{proc['name'][:25]} | {proc['ram']:.0f}MB",
                callback_data=f"proc_action_{proc['pid']}"
            )
        ])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_process")])
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def show_drives(query):
    """Показ списка дисков."""
    drives = file_manager.get_drives()

    if not drives:
        await query.edit_message_text("❌ No drives found.")
        return

    text = "📁 File Explorer\n\nSelect a drive:\n"
    for drive in drives:
        text += f"💿 {drive}\n"

    await query.edit_message_text(text, reply_markup=keyboards.get_drives_menu())


async def browse_directory(query, path: str):
    """Навигация по директории."""
    user_id = query.from_user.id
    security.set_user_directory(user_id, path)

    if user_id not in path_cache:
        path_cache[user_id] = {}

    items, error = file_manager.navigate_to_path(path)

    if error:
        await query.edit_message_text(f"❌ {error}")
        return

    if not items:
        if not path:
            await query.edit_message_text("❌ No drives found.")
        else:
            await query.edit_message_text("📁 Empty directory")
        return

    display_path = path if path else "Root"
    text = f"📂 {display_path}\n\n"

    folders = [i for i in items if i['is_dir']]
    files = [i for i in items if not i['is_dir']]

    if folders:
        text += f"📁 Folders ({len(folders)}):\n"
        for f in folders[:10]:
            text += f"  📁 {f['name']}\n"
        if len(folders) > 10:
            text += f"  ... and {len(folders) - 10} more\n"

    if files:
        text += f"\n📄 Files ({len(files)}):\n"
        for f in files[:10]:
            size = file_manager.format_size(f['size'])
            text += f"  📄 {f['name']} ({size})\n"
        if len(files) > 10:
            text += f"  ... and {len(files) - 10} more\n"

    keyboard = []

    if path and path != "Root":
        parent = file_manager.get_parent_directory(path)
        if parent or path != "":
            keyboard.append([InlineKeyboardButton("📁 ..", callback_data="dir_up")])

    for i, folder in enumerate(folders[:15]):
        path_id = f"dir_{user_id}_{i}"
        path_cache[user_id][path_id] = folder['path']
        keyboard.append([
            InlineKeyboardButton(f"📁 {folder['name'][:30]}", callback_data=f"dirb_{encode_path(folder['path'])}")
        ])

    for i, file in enumerate(files[:15]):
        path_id = f"file_{user_id}_{i}"
        path_cache[user_id][path_id] = file['path']
        keyboard.append([
            InlineKeyboardButton(f"📄 {file['name'][:30]}", callback_data=f"fileb_{encode_path(file['path'])}")
        ])

    nav_row = [
        InlineKeyboardButton("🔙 Back", callback_data="menu_files"),
        InlineKeyboardButton("🏠 Root", callback_data="file_root"),
        InlineKeyboardButton("🔄 Refresh", callback_data="file_refresh"),
    ]
    keyboard.append(nav_row)

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def show_file_actions(query, file_path: str, user_id: int):
    """Показ действий с файлом."""
    info = file_manager.get_file_info(file_path)
    
    if not info:
        await query.edit_message_text(f"❌ File not found: {file_path}")
        return
    
    size = file_manager.format_size(info['size'])
    text = f"""📄 File Info

Name: {info['name']}
Path: {info['path']}
Size: {size}
Type: {"Folder" if info['is_dir'] else "File" + (info.get('extension', '') or '')}
"""

    if info['is_dir']:
        await browse_directory(query, file_path)
    else:
        await query.edit_message_text(
            text,
            reply_markup=keyboards.get_file_actions_menu(file_path)
        )


async def download_file_callback(query, file_path: str):
    """Callback для скачивания файла."""
    try:
        file_size = Path(file_path).stat().st_size

        if file_size > 50 * 1024 * 1024:
            await query.edit_message_text(
                f"❌ File too large ({file_manager.format_size(file_size)}). "
                "Maximum size is 50MB."
            )
            return

        await query.edit_message_text(f"💾 Uploading file... ({file_manager.format_size(file_size)})")

        with open(file_path, 'rb') as f:
            await query.message.reply_document(
                document=f,
                filename=Path(file_path).name,
                caption=f"📄 {Path(file_path).name}"
            )

        await query.delete_message()
    except Exception as e:
        await query.edit_message_text(f"❌ Error: {e}")


async def start_timer(query, minutes: int, action: str):
    """Запуск таймера для выключения или сна."""
    user_id = query.from_user.id
    seconds = minutes * 60
    await query.edit_message_text(f"⏰ Timer set: {action} in {minutes} minutes.")

    if user_id in user_states and 'timer_task' in user_states[user_id]:
        user_states[user_id]['timer_task'].cancel()
        logger.info(f"Cancelled previous timer for user {user_id}")

    async def timer_task_func():
        await asyncio.sleep(seconds)
        if action == 'sleep':
            success, msg = system_manager.sleep_pc()
        elif action == 'shutdown':
            success, msg = system_manager.shutdown_pc()
        
        try:
            await query.message.reply_text(f"⏰ Timer finished: {msg}")
        except Exception as e:
            logger.error(f"Error sending timer finish message: {e}")
        finally:
            if user_id in user_states and 'timer_task' in user_states[user_id]:
                del user_states[user_id]['timer_task']

    timer_task = asyncio.create_task(timer_task_func())
    user_states[user_id]['timer_task'] = timer_task


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений."""
    user_id = update.effective_user.id
    text = update.message.text

    if user_id in user_states:
        state = user_states[user_id]
        action = state.get('action')

        if action == 'auth_password':
            if security.verify_password(text):
                security.add_allowed_user(user_id)
                await update.message.reply_text(
                    "✅ Authentication successful!\n"
                    "You now have access to all functions.",
                    reply_markup=keyboards.get_main_menu()
                )
            else:
                await update.message.reply_text("❌ Wrong password. Try again or /cancel")
            del user_states[user_id]
            return

    has_access, error_msg = security.check_access(user_id)
    if not has_access:
        await update.message.reply_text(error_msg)
        return

    if user_id not in user_states:
        await update.message.reply_text(
            "Use the menu buttons to interact.",
            reply_markup=keyboards.get_main_menu()
        )
        return

    state = user_states[user_id]
    action = state.get('action')

    # Обработка действий
    if action == 'run_process':
        success, msg = process_manager.run_process(text)
        await update.message.reply_text(msg)
        del user_states[user_id]
    
    elif action == 'kill_process':
        try:
            pid = int(text)
            success, msg = process_manager.kill_process(pid)
            await update.message.reply_text(msg)
        except ValueError:
            await update.message.reply_text("❌ Please send a valid PID number.")
        del user_states[user_id]
    
    elif action == 'restart_process':
        try:
            pid = int(text)
            success, msg = process_manager.restart_process(pid)
            await update.message.reply_text(msg)
        except ValueError:
            await update.message.reply_text("❌ Please send a valid PID number.")
        del user_states[user_id]
    
    elif action == 'change_priority':
        parts = text.split()
        if len(parts) != 2:
            await update.message.reply_text("❌ Format: PID priority (e.g., 1234 high)")
            return
        try:
            pid = int(parts[0])
            priority = parts[1].lower()
            success, msg = process_manager.change_priority(pid, priority)
            await update.message.reply_text(msg)
        except ValueError:
            await update.message.reply_text("❌ Invalid format. Use: PID priority")
        del user_states[user_id]
    
    elif action == 'watch_process':
        try:
            pid = int(text)
            info = process_manager.watch_process(pid)
            if info:
                msg = f"""👁️ Process Info

Name: {info['name']}
PID: {info['pid']}
Status: {info['status']}
RAM: {info['ram']:.1f} MB
CPU: {info['cpu']:.1f}%
User: {info['username']}
"""
                await update.message.reply_text(msg)
            else:
                await update.message.reply_text(f"❌ Process {pid} not found.")
        except ValueError:
            await update.message.reply_text("❌ Please send a valid PID number.")
        del user_states[user_id]
    
    elif action == 'ping_host':
        success, msg = network_manager.ping_host(text)
        await update.message.reply_text(msg, parse_mode='Markdown')
        del user_states[user_id]
    
    elif action == 'dns_lookup':
        success, msg = network_manager.dns_lookup(text)
        await update.message.reply_text(msg, parse_mode='Markdown')
        del user_states[user_id]
    
    elif action == 'execute_cmd':
        try:
            result = subprocess.run(text, shell=True, capture_output=True, text=True, timeout=30)
            output = result.stdout + result.stderr
            if len(output) > 4000:
                output = output[:4000] + "... (truncated)"
            msg = f"💻 CMD Output:\n\n```\n{output}\n```"
            await update.message.reply_text(msg, parse_mode='Markdown')
        except subprocess.TimeoutExpired:
            await update.message.reply_text("❌ Command timeout (30s)")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
        del user_states[user_id]
    
    elif action == 'set_clipboard':
        success, msg = system_manager.set_clipboard_content(text)
        await update.message.reply_text(msg)
        del user_states[user_id]
    elif action == 'open_url':
        success, msg = system_manager.open_url(text)
        await update.message.reply_text(msg)
        del user_states[user_id]
    
    elif action == 'change_password':
        success = security.change_password(text)
        if success:
            await update.message.reply_text("✅ Password changed successfully.")
        else:
            await update.message.reply_text("❌ Failed to change password.")
        del user_states[user_id]
    
    elif action == 'rename_file':
        file_path = state.get('file_path')
        success, msg = file_manager.rename_file(file_path, text)
        await update.message.reply_text(msg)
        del user_states[user_id]
    
    elif action == 'move_file':
        file_path = state.get('file_path')
        success, msg = file_manager.move_file(file_path, text)
        await update.message.reply_text(msg)
        del user_states[user_id]
    
    elif action == 'copy_file':
        file_path = state.get('file_path')
        success, msg = file_manager.copy_file(file_path, text)
        await update.message.reply_text(msg)
        del user_states[user_id]
    
    elif action == 'watch_directory':
        def on_change(event_type, path, dest_path=None):
            dest_info = f" -> {dest_path}" if dest_path else ""
            msg = f"👁️ Directory Change: {event_type} {path}{dest_info}"
            # Отправляем уведомление
            try:
                context.bot.send_message(chat_id=user_id, text=msg)
            except Exception:
                pass
        
        if start_directory_watch(text, lambda e, p, d=None: on_change(e, p, d)):
            await update.message.reply_text(f"✅ Started watching: {text}")
        else:
            await update.message.reply_text(f"❌ Failed to watch: {text}")
        del user_states[user_id]
    
    elif action == 'confirm_shutdown':
        if text.lower() in ['yes', 'confirm', 'да']:
            success, msg = system_manager.shutdown_pc()
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text("❌ Shutdown cancelled.")
        del user_states[user_id]
    
    elif action == 'confirm_restart':
        if text.lower() in ['yes', 'confirm', 'да']:
            success, msg = system_manager.restart_pc()
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text("❌ Restart cancelled.")
        del user_states[user_id]
    
    else:
        await update.message.reply_text("Unknown action. Use /cancel to reset.")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик загруженных файлов."""
    user_id = update.effective_user.id

    has_access, error_msg = security.check_access(user_id)
    if not has_access:
        await update.message.reply_text(error_msg)
        return

    current_dir = security.get_user_directory(user_id)

    if not current_dir:
        await update.message.reply_text(
            "❌ Please open a directory first using File Explorer."
        )
        return

    file = await update.message.document.get_file()
    file_name = update.message.document.file_name

    save_path = Path(current_dir) / file_name

    try:
        await file.download_to_drive(str(save_path))
        await update.message.reply_text(f"✅ File saved: {save_path}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error saving file: {e}")


def create_application(token: str) -> Application:
    """
    Создание и настройка приложения.

    Args:
        token: Токен бота

    Returns:
        Настроенное приложение
    """
    application = Application.builder().token(token).build()

    # Обработчик команды /start
    application.add_handler(CommandHandler("start", start_command))

    # Обработчик команды /help
    application.add_handler(CommandHandler("help", help_command))

    # Обработчик команды /status
    application.add_handler(CommandHandler("status", status_command))

    # Обработчик команды /auth
    application.add_handler(CommandHandler("auth", auth_command))

    # Обработчик команды /cancel
    application.add_handler(CommandHandler("cancel", cancel_command))

    # Обработчик callback-запросов (кнопки)
    application.add_handler(CallbackQueryHandler(button_handler))

    # Обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Обработчик файлов
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    return application


# Импорт subprocess для execute_cmd
import subprocess
