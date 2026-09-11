import os
import sys
import json
import math
import urllib.request
import tempfile
import subprocess

# --- ФИКС ПЛАГИНОВ PYQT5 ---
try:
    import PyQt5
    pyqt_path = os.path.dirname(PyQt5.__file__)
    plugin_path = os.path.join(pyqt_path, 'Qt5', 'plugins', 'platforms')
    if os.path.exists(plugin_path):
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
except ImportError:
    pass

import ctypes
import ctypes.wintypes
from datetime import datetime, timedelta
import psutil
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QDialog, QComboBox, QSlider, QColorDialog,
    QCheckBox, QFormLayout, QDialogButtonBox, QSpinBox,
    QSystemTrayIcon, QMenu, QAction, QTabWidget, QSizePolicy,
    QStackedWidget, QLineEdit, QScrollArea, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRectF
from PyQt5.QtGui import (
    QFont, QColor, QPainter, QBrush, QLinearGradient,
    QIcon, QPixmap, QPainterPath, QPen, QFontMetrics
)

# ============================================================
# ВЕРСИЯ ПРОГРАММЫ
# ============================================================
CURRENT_VERSION = "1.2"
GITHUB_REPO = "xR-leo/schedule-desktop"  # ← ЗАМЕНИ НА СВОЙ НИК!

# ============================================================
# ПУТИ
# ============================================================
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, 'data')
DESIGN_FILE = os.path.join(DATA_DIR, 'design.json')
POSITION_FILE = os.path.join(DATA_DIR, 'position.json')
MEMORY_FILE = os.path.join(DATA_DIR, 'memory.json')
BELLS_FILE = os.path.join(DATA_DIR, 'bells.json')

os.makedirs(DATA_DIR, exist_ok=True)

# ============================================================
# ПРЕСЕТЫ ТЕМ
# ============================================================
THEMES = {
    'custom': {'name': '🎨 Своя тема'},
    'dark': {
        'name': '🌑 Тёмная',
        'bg_fill_mode': 'gradient', 'color1': '#1a1f2e', 'color2': '#283c64',
        'alpha': 90, 'time_mode': 'solid', 'time_color': '#ffffff',
        'info_color': '#8892b0', 'date_color': '#8892b0',
        'time_shadow': False, 'time_outline': False, 'time_pulse': False,
    },
    'neon': {
        'name': '💜 Неон',
        'bg_fill_mode': 'solid', 'color1': '#0a0014', 'color2': '#0a0014',
        'alpha': 85, 'time_mode': 'solid', 'time_color': '#ff00ff',
        'info_color': '#ff88ff', 'date_color': '#00ffff',
        'time_shadow': True, 'time_outline': False, 'time_pulse': True,
    },
    'retro': {
        'name': '🕹️ Ретро',
        'bg_fill_mode': 'gradient', 'color1': '#2b1810', 'color2': '#4a2c1a',
        'alpha': 95, 'time_mode': 'solid', 'time_color': '#ffb000',
        'info_color': '#d4a574', 'date_color': '#ffb000',
        'time_shadow': True, 'time_outline': False, 'time_pulse': False,
    },
    'minimal': {
        'name': '⬜ Минимал',
        'bg_fill_mode': 'transparent', 'color1': '#000000', 'color2': '#000000',
        'alpha': 0, 'time_mode': 'solid', 'time_color': '#ffffff',
        'info_color': '#777777', 'date_color': '#777777',
        'time_shadow': False, 'time_outline': False, 'time_pulse': False,
    },
    'rainbow': {
        'name': '🌈 Радуга',
        'bg_fill_mode': 'gradient', 'color1': '#1a0033', 'color2': '#003366',
        'alpha': 80, 'time_mode': 'rainbow', 'time_color': '#ffffff',
        'info_color': '#ff88ff', 'date_color': '#00ffff',
        'time_shadow': True, 'time_outline': False, 'time_pulse': False,
    },
}

# ============================================================
# НАСТРОЙКИ ПО УМОЛЧАНИЮ
# ============================================================
DEFAULT_SETTINGS = {
    'bg_fill_mode': 'gradient',
    'color1': '#1a1f2e',
    'color2': '#283c64',
    'alpha': 90,
    'corner_radius': 8,
    'time_mode': 'solid',
    'time_color': '#ffffff',
    'time_gradient_color1': '#ff6b9d',
    'time_gradient_color2': '#4ecdc4',
    'time_rainbow_speed': 5,
    'time_rainbow_mode': 'line',
    'time_font_size': 36,
    'info_color': '#8892b0',
    'date_color': '#8892b0',
    'time_shadow': False,
    'time_shadow_color': '#000000',
    'time_outline': False,
    'time_outline_color': '#ffffff',
    'time_pulse': False,
    'show_date': True,
    'date_format': 'day_month_year',
    'auto_hide_fullscreen': True,
    'smart_load': True,
    'window_width': 280,
    'window_height': 200,
    'pos_x': 50,
    'pos_y': 50,
    'theme': 'custom',
    'schedule_days': 6,
    'sunday_enabled': False,
}

# ============================================================
# ЗВОНКИ ПО УМОЛЧАНИЮ
# ============================================================
DEFAULT_BELLS_MONDAY = [
    ['08:00', '08:45'],
    ['09:00', '10:30'],
    ['10:40', '12:10'],
    ['12:30', '14:00'],
    ['14:10', '15:40'],
]

DEFAULT_BELLS_OTHER = [
    ['08:00', '09:30'],
    ['09:40', '11:10'],
    ['11:30', '13:00'],
    ['13:10', '14:40'],
    ['14:50', '16:20'],
]

# ============================================================
# ЗВОНКИ — ЗАГРУЗКА/СОХРАНЕНИЕ
# ============================================================
def load_bells():
    default = {
        'monday': [list(b) for b in DEFAULT_BELLS_MONDAY],
        'other': [list(b) for b in DEFAULT_BELLS_OTHER],
    }
    if os.path.exists(BELLS_FILE):
        try:
            with open(BELLS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict):
                for k, v in default.items():
                    if k not in data:
                        data[k] = v
                return data
        except Exception as e:
            print('[Bells] Ошибка загрузки:', e)
    save_bells(default)
    print('[Bells] Создан bells.json')
    return default

def save_bells(bells):
    try:
        with open(BELLS_FILE, 'w', encoding='utf-8') as f:
            json.dump(bells, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print('[Bells] Ошибка сохранения:', e)

bells_monday = []
bells_other = []

def apply_bells_from_file():
    global bells_monday, bells_other
    data = load_bells()
    bells_monday = data.get('monday', [])
    bells_other = data.get('other', [])
    print(f'[Bells] Пн: {len(bells_monday)}, Вт-Сб: {len(bells_other)}')

# ============================================================
# ОФОРМЛЕНИЕ
# ============================================================
def load_design():
    if os.path.exists(DESIGN_FILE):
        try:
            with open(DESIGN_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            s = {k: v for k, v in DEFAULT_SETTINGS.items() if k not in ('pos_x', 'pos_y')}
            s.update({k: v for k, v in data.items() if k not in ('pos_x', 'pos_y')})
            return s
        except Exception as e:
            print('[Design] Ошибка загрузки:', e)
    result = {k: v for k, v in DEFAULT_SETTINGS.items() if k not in ('pos_x', 'pos_y')}
    save_design(result)
    print('[Design] Создан design.json')
    return result

def save_design(s):
    try:
        data = {k: v for k, v in s.items() if k not in ('pos_x', 'pos_y')}
        with open(DESIGN_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print('[Design] Ошибка сохранения:', e)

def reset_design():
    try:
        if os.path.exists(DESIGN_FILE):
            os.remove(DESIGN_FILE)
            print('[Design] design.json удалён')
    except Exception as e:
        print('[Design] Ошибка удаления:', e)

def load_position():
    default = {'pos_x': DEFAULT_SETTINGS['pos_x'], 'pos_y': DEFAULT_SETTINGS['pos_y']}
    if os.path.exists(POSITION_FILE):
        try:
            with open(POSITION_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return {
                'pos_x': data.get('pos_x', default['pos_x']),
                'pos_y': data.get('pos_y', default['pos_y']),
            }
        except Exception as e:
            print('[Position] Ошибка загрузки:', e)
    save_position(default['pos_x'], default['pos_y'])
    return default

def save_position(x, y):
    try:
        with open(POSITION_FILE, 'w', encoding='utf-8') as f:
            json.dump({'pos_x': x, 'pos_y': y}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print('[Position] Ошибка сохранения:', e)

def load_memory():
    default = {
        'session_started': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'restart_count': 0,
        'last_theme': 'custom',
    }
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            default.update(data)
            default['restart_count'] = default.get('restart_count', 0) + 1
            return default
        except Exception as e:
            print('[Memory] Ошибка загрузки:', e)
    return default

def save_memory(m):
    try:
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(m, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print('[Memory] Ошибка сохранения:', e)

def reset_memory():
    try:
        if os.path.exists(MEMORY_FILE):
            os.remove(MEMORY_FILE)
            print('[Memory] memory.json удалён')
    except Exception as e:
        print('[Memory] Ошибка удаления:', e)

def load_settings():
    design = load_design()
    position = load_position()
    memory = load_memory()
    s = DEFAULT_SETTINGS.copy()
    s.update(design)
    s.update(position)
    s['_memory'] = memory
    return s

def save_settings(s):
    save_design(s)
    save_position(s.get('pos_x', 50), s.get('pos_y', 50))

SETTINGS = load_settings()
MEMORY = SETTINGS.get('_memory', {})

# ============================================================
# ХЕЛПЕРЫ ЦВЕТА
# ============================================================
def hex_to_qcolor(hex_str, alpha=255):
    hex_str = hex_str.lstrip('#')
    r = int(hex_str[0:2], 16)
    g = int(hex_str[2:4], 16)
    b = int(hex_str[4:6], 16)
    return QColor(r, g, b, alpha)

def qcolor_to_hex(c):
    return '#{:02x}{:02x}{:02x}'.format(c.red(), c.green(), c.blue())

# ============================================================
# КАСТОМНЫЙ QLabel
# ============================================================
class OutlinedLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._outline_enabled = False
        self._outline_color = QColor('#ffffff')
        self._shadow_enabled = False
        self._shadow_color = QColor('#000000')
        self._shadow_offset = 2
        self._text_color = QColor('#ffffff')
        self._char_colors = []

    def set_outline(self, enabled, color):
        self._outline_enabled = enabled
        self._outline_color = hex_to_qcolor(color)
        self.update()

    def set_shadow(self, enabled, color):
        self._shadow_enabled = enabled
        self._shadow_color = hex_to_qcolor(color)
        self.update()

    def set_text_color(self, color):
        self._text_color = hex_to_qcolor(color)
        self.update()

    def set_char_colors(self, colors):
        self._char_colors = colors
        self.update()

    def paintEvent(self, event):
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.TextAntialiasing)

            font = self.font()
            metrics = QFontMetrics(font)
            text = self.text()

            if not text:
                return

            text_rect = self.rect()
            total_width = metrics.horizontalAdvance(text)
            start_x = (text_rect.width() - total_width) // 2
            base_y = (text_rect.height() + metrics.ascent() - metrics.descent()) // 2

            x = start_x
            for i, ch in enumerate(text):
                ch_width = metrics.horizontalAdvance(ch)
                if self._char_colors and i < len(self._char_colors):
                    color = self._char_colors[i]
                else:
                    color = self._text_color

                if self._shadow_enabled:
                    painter.setPen(QPen(self._shadow_color, 0))
                    painter.drawText(x + self._shadow_offset,
                                     base_y + self._shadow_offset, ch)

                if self._outline_enabled:
                    path = QPainterPath()
                    path.addText(x, base_y, font, ch)
                    painter.setPen(QPen(self._outline_color, 2))
                    painter.setBrush(Qt.NoBrush)
                    painter.drawPath(path)

                painter.setPen(QPen(color, 0))
                painter.drawText(x, base_y, ch)
                x += ch_width
        except Exception as e:
            print('Ошибка в OutlinedLabel.paintEvent:', e)

# ============================================================
# ИКОНКА ТРЕЯ
# ============================================================
def create_tray_icon():
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    gradient = QLinearGradient(0, 0, 64, 64)
    gradient.setColorAt(0, QColor(40, 60, 100))
    gradient.setColorAt(1, QColor(26, 31, 46))
    painter.setBrush(QBrush(gradient))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(0, 0, 64, 64, 14, 14)
    painter.setBrush(Qt.NoBrush)
    pen = painter.pen()
    pen.setColor(QColor(183, 201, 255))
    pen.setWidth(3)
    painter.setPen(pen)
    painter.drawEllipse(12, 12, 40, 40)
    painter.drawLine(32, 32, 32, 20)
    painter.drawLine(32, 32, 42, 36)
    painter.end()
    return QIcon(pixmap)

# ============================================================
# УМНЫЙ РЕЖИМ
# ============================================================
CPU_HIGH_THRESHOLD = 60
CPU_CRITICAL_THRESHOLD = 85
RAM_HIGH_THRESHOLD = 80

FADE_IN_DURATION = 1500
FADE_START_DELAY = 500
STARTUP_LOAD_CHECKS = 3
STARTUP_CHECK_INTERVAL = 500

# ============================================================
# ЛОГИКА
# ============================================================
def to_minutes(t):
    h, m = map(int, t.split(':'))
    return h * 60 + m

def format_remain(mins):
    if mins <= 0:
        return '0 мин'
    h = mins // 60
    m = mins % 60
    return f'{h} ч {m} мин' if h else f'{m} мин'

def get_status_by_bells():
    global bells_monday, bells_other

    now = datetime.now()
    weekday = now.weekday()
    current = now.hour * 60 + now.minute

    schedule_days = SETTINGS.get('schedule_days', 6)
    sunday_enabled = SETTINGS.get('sunday_enabled', False)

    if weekday == 6:
        if not sunday_enabled:
            return 'Выходной', ''
        bells = bells_other
    elif weekday == 5:
        if schedule_days < 6:
            return 'Выходной', ''
        bells = bells_other
    elif weekday == 0:
        bells = bells_monday
    else:
        bells = bells_other

    if not bells:
        return 'Нет звонков', ''

    pairs = [(i, to_minutes(b[0]), to_minutes(b[1]))
             for i, b in enumerate(bells) if len(b) >= 2]

    if not pairs:
        return 'Нет звонков', ''

    first_start = pairs[0][1]
    last_end = pairs[-1][2]

    if current < first_start:
        wait = first_start - current
        return 'Скоро начало', f'через {format_remain(wait)}'

    if current >= last_end:
        return 'Занятия закончились', ''

    for i, sm, em in pairs:
        if sm <= current < em:
            remain = em - current
            return f'Идёт {i+1}-я пара', f'до конца {format_remain(remain)}'

    for i, sm, em in pairs:
        if current < sm:
            wait = sm - current
            return 'Перемена', f'через {format_remain(wait)}'

    return 'Нет данных', ''

# ============================================================
# WINAPI
# ============================================================
user32 = ctypes.windll.user32

class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.wintypes.DWORD),
        ("rcMonitor", ctypes.wintypes.RECT),
        ("rcWork", ctypes.wintypes.RECT),
        ("dwFlags", ctypes.wintypes.DWORD),
    ]

def get_window_class(hwnd):
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf, 256)
    return buf.value

def get_active_window_rect():
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None, None
    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return hwnd, (rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top)

def get_monitor_for_window(hwnd):
    hmon = user32.MonitorFromWindow(hwnd, 2)
    mi = MONITORINFO()
    mi.cbSize = ctypes.sizeof(MONITORINFO)
    user32.GetMonitorInfoW(hmon, ctypes.byref(mi))
    r = mi.rcMonitor
    return (r.left, r.top, r.right - r.left, r.bottom - r.top)

def get_monitor_for_point(x, y):
    point = ctypes.wintypes.POINT(x, y)
    hmon = user32.MonitorFromPoint(point, 2)
    mi = MONITORINFO()
    mi.cbSize = ctypes.sizeof(MONITORINFO)
    user32.GetMonitorInfoW(hmon, ctypes.byref(mi))
    r = mi.rcMonitor
    return (r.left, r.top, r.right - r.left, r.bottom - r.top)

def is_fullscreen_on_monitor(widget_monitor):
    hwnd, rect = get_active_window_rect()
    if not hwnd or not rect:
        return False
    cls = get_window_class(hwnd)
    if cls in ('Progman', 'WorkerW', 'Shell_TrayWnd'):
        return False
    x, y, w, h = rect
    win_monitor = get_monitor_for_window(hwnd)
    if widget_monitor != win_monitor:
        return False
    mx, my, mw, mh = win_monitor
    return (x <= mx + 5 and y <= my + 5 and w >= mw - 10 and h >= mh - 10)

def get_system_load():
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory().percent
    return cpu, ram

# ============================================================
# АВТО-ОБНОВЛЕНИЕ
# ============================================================
def parse_version(v):
    try:
        parts = v.strip().lstrip('v').split('.')
        return tuple(int(p) for p in parts[:2])
    except Exception:
        return (0, 0)

def check_for_updates():
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        req = urllib.request.Request(url, headers={'User-Agent': 'Schedule'})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())

        latest_version = data.get('tag_name', '').lstrip('v')
        if not latest_version:
            return

        cur_v = parse_version(CURRENT_VERSION)
        new_v = parse_version(latest_version)

        if new_v <= cur_v:
            return
        if not (parse_version("1.3") <= new_v <= parse_version("10.0")):
            return

        assets = data.get('assets', [])
        exe_url = None
        for a in assets:
            if a['name'].lower().endswith('.exe'):
                exe_url = a['browser_download_url']
                break

        if not exe_url:
            return

        ask_and_update(latest_version, exe_url)
    except Exception as e:
        print(f'[Update] Ошибка: {e}')

def ask_and_update(new_version, exe_url):
    try:
        reply = QMessageBox.question(
            None, 'Доступно обновление',
            f'Вышла новая версия v{new_version}!\n\n'
            f'Обновить сейчас?\n'
            f'(Программа перезапустится)',
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        temp_dir = tempfile.gettempdir()
        new_exe = os.path.join(temp_dir, 'Schedule_new.exe')

        print(f'[Update] Скачиваю...')
        req = urllib.request.Request(exe_url, headers={'User-Agent': 'Schedule'})
        with urllib.request.urlopen(req, timeout=120) as r:
            with open(new_exe, 'wb') as f:
                f.write(r.read())

        current_exe = sys.executable
        bat_path = os.path.join(temp_dir, 'update_schedule.bat')

        with open(bat_path, 'w', encoding='cp866') as f:
            f.write(f'''@echo off
timeout /t 2 /nobreak >nul
del "{current_exe}"
move /y "{new_exe}" "{current_exe}"
start "" "{current_exe}"
del "%~f0"
''')

        subprocess.Popen(
            ['cmd', '/c', bat_path],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        sys.exit(0)
    except Exception as e:
        try:
            QMessageBox.warning(None, 'Ошибка', f'Не удалось обновить: {e}')
        except Exception:
            print(f'[Update] Ошибка: {e}')

# ============================================================
# ДИАЛОГ НАСТРОЕК
# ============================================================
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f'Настройки v{CURRENT_VERSION}')
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.WindowCloseButtonHint)
        self.setMinimumWidth(480)
        self.setMinimumHeight(600)
        self.setStyleSheet("""
            QDialog { background: #1a1f2e; color: #e8edf5; }
            QLabel { color: #e8edf5; }
            QComboBox, QSpinBox, QLineEdit {
                background: #121725; color: #e8edf5;
                border: 1px solid #2e354a; border-radius: 6px; padding: 4px;
                min-height: 22px;
            }
            QComboBox::drop-down { border: none; width: 20px; }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 7px solid #b7c9ff;
                margin-right: 6px;
            }
            QComboBox QAbstractItemView {
                background: #121725; color: #e8edf5;
                selection-background-color: #2a3045;
            }
            QPushButton {
                background: #2a3045; color: #b7c9ff;
                border: none; border-radius: 6px; padding: 6px 12px;
            }
            QPushButton:hover { background: #3a4058; }
            QCheckBox { color: #e8edf5; spacing: 8px; padding: 4px 0; }
            QCheckBox::indicator {
                width: 20px; height: 20px;
                border: 2px solid #4a5270;
                border-radius: 5px;
                background: #121725;
            }
            QCheckBox::indicator:checked {
                background: #7ae0b0; border-color: #7ae0b0;
            }
            QSlider::groove:horizontal {
                height: 6px; background: #2e354a; border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #7a9cff; width: 16px;
                margin: -5px 0; border-radius: 8px;
            }
            QSlider::sub-page:horizontal {
                background: #7ae0b0; border-radius: 3px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background: #e8edf5; border: none; width: 20px;
            }
            QSpinBox::up-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-bottom: 7px solid #000000;
            }
            QSpinBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 7px solid #000000;
            }
            QTabWidget::pane {
                border: 1px solid #2e354a; border-radius: 8px;
                background: #121725; top: -1px;
            }
            QTabBar::tab {
                background: #1a1f2e; color: #8892b0;
                padding: 8px 14px;
                border: 1px solid #2e354a; border-bottom: none;
                border-top-left-radius: 8px; border-top-right-radius: 8px;
                margin-right: 2px; font-size: 11px; font-weight: 600;
            }
            QTabBar::tab:hover { background: #2a3045; color: #b7c9ff; }
            QTabBar::tab:selected {
                background: #2a3045; color: #7ae0b0;
                border-bottom: 2px solid #7ae0b0;
            }
            QScrollArea { border: none; background: transparent; }
        """)

        self.temp = SETTINGS.copy()
        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # ================= ФОН =================
        bg_widget = QWidget()
        bg_form = QFormLayout(bg_widget)
        bg_form.setContentsMargins(16, 16, 16, 16)

        self.bg_fill_combo = QComboBox()
        self.bg_fill_combo.addItems(['Градиент', 'Один цвет', 'Прозрачный'])
        bg_map = {'gradient': 0, 'solid': 1, 'transparent': 2}
        self.bg_fill_combo.setCurrentIndex(bg_map.get(self.temp.get('bg_fill_mode', 'gradient'), 0))
        self.bg_fill_combo.currentIndexChanged.connect(self.on_bg_fill_changed)
        bg_form.addRow('Режим заливки:', self.bg_fill_combo)

        self.lbl_bg_c1 = QLabel('Цвет 1:')
        self.btn_color1 = QPushButton(self.temp['color1'])
        self._style_color_button(self.btn_color1, self.temp['color1'])
        self.btn_color1.clicked.connect(lambda: self.pick_color('color1', self.btn_color1))
        bg_form.addRow(self.lbl_bg_c1, self.btn_color1)

        self.lbl_bg_c2 = QLabel('Цвет 2:')
        self.btn_color2 = QPushButton(self.temp['color2'])
        self._style_color_button(self.btn_color2, self.temp['color2'])
        self.btn_color2.clicked.connect(lambda: self.pick_color('color2', self.btn_color2))
        bg_form.addRow(self.lbl_bg_c2, self.btn_color2)

        self.lbl_alpha = QLabel('Прозрачность:')
        self.slider_alpha = QSlider(Qt.Horizontal)
        self.slider_alpha.setRange(0, 100)
        self.slider_alpha.setValue(self.temp['alpha'])
        self.lbl_alpha_val = QLabel(f"{self.temp['alpha']}%")
        self.slider_alpha.valueChanged.connect(lambda v: self.lbl_alpha_val.setText(f'{v}%'))
        h = QHBoxLayout(); h.addWidget(self.slider_alpha); h.addWidget(self.lbl_alpha_val)
        bg_form.addRow(self.lbl_alpha, h)

        self.spin_radius = QSpinBox()
        self.spin_radius.setRange(0, 40)
        self.spin_radius.setValue(self.temp['corner_radius'])
        bg_form.addRow('Скругление углов:', self.spin_radius)

        self.tabs.addTab(bg_widget, '🎨 Фон')

        # ================= ВРЕМЯ =================
        time_widget = QWidget()
        time_form = QFormLayout(time_widget)
        time_form.setContentsMargins(16, 16, 16, 16)

        self.spin_font = QSpinBox()
        self.spin_font.setRange(16, 80)
        self.spin_font.setValue(self.temp['time_font_size'])
        time_form.addRow('Размер шрифта:', self.spin_font)

        self.time_mode_combo = QComboBox()
        self.time_mode_combo.addItems(['Один цвет', 'Градиент', 'Радуга'])
        time_map = {'solid': 0, 'gradient': 1, 'rainbow': 2}
        self.time_mode_combo.setCurrentIndex(time_map.get(self.temp.get('time_mode', 'solid'), 0))
        self.time_mode_combo.currentIndexChanged.connect(self.on_time_mode_changed)
        time_form.addRow('Режим времени:', self.time_mode_combo)

        self.time_stack = QStackedWidget()

        solid_widget = QWidget()
        solid_form = QFormLayout(solid_widget)
        solid_form.setContentsMargins(0, 0, 0, 0)
        self.btn_time_color = QPushButton(self.temp['time_color'])
        self._style_color_button(self.btn_time_color, self.temp['time_color'])
        self.btn_time_color.clicked.connect(lambda: self.pick_color('time_color', self.btn_time_color))
        solid_form.addRow('Цвет времени:', self.btn_time_color)
        self.time_stack.addWidget(solid_widget)

        grad_widget = QWidget()
        grad_form = QFormLayout(grad_widget)
        grad_form.setContentsMargins(0, 0, 0, 0)
        self.btn_tg1 = QPushButton(self.temp.get('time_gradient_color1', '#ff6b9d'))
        self._style_color_button(self.btn_tg1, self.temp.get('time_gradient_color1', '#ff6b9d'))
        self.btn_tg1.clicked.connect(lambda: self.pick_color('time_gradient_color1', self.btn_tg1))
        grad_form.addRow('Цвет 1:', self.btn_tg1)
        self.btn_tg2 = QPushButton(self.temp.get('time_gradient_color2', '#4ecdc4'))
        self._style_color_button(self.btn_tg2, self.temp.get('time_gradient_color2', '#4ecdc4'))
        self.btn_tg2.clicked.connect(lambda: self.pick_color('time_gradient_color2', self.btn_tg2))
        grad_form.addRow('Цвет 2:', self.btn_tg2)
        self.time_stack.addWidget(grad_widget)

        rainbow_widget = QWidget()
        rainbow_form = QFormLayout(rainbow_widget)
        rainbow_form.setContentsMargins(0, 0, 0, 0)

        self.slider_rainbow_speed = QSlider(Qt.Horizontal)
        self.slider_rainbow_speed.setRange(1, 10)
        self.slider_rainbow_speed.setValue(self.temp.get('time_rainbow_speed', 5))
        self.lbl_rainbow_speed = QLabel(str(self.temp.get('time_rainbow_speed', 5)))
        self.slider_rainbow_speed.valueChanged.connect(lambda v: self.lbl_rainbow_speed.setText(str(v)))
        h2 = QHBoxLayout(); h2.addWidget(self.slider_rainbow_speed); h2.addWidget(self.lbl_rainbow_speed)
        rainbow_form.addRow('Скорость (1-10):', h2)

        self.rainbow_mode_combo = QComboBox()
        self.rainbow_mode_combo.addItems(['Линия (поток)', 'Цифры (каждая своя)'])
        rb_map = {'line': 0, 'digits': 1}
        self.rainbow_mode_combo.setCurrentIndex(rb_map.get(self.temp.get('time_rainbow_mode', 'line'), 0))
        rainbow_form.addRow('Режим радуги:', self.rainbow_mode_combo)

        self.time_stack.addWidget(rainbow_widget)
        time_form.addRow(self.time_stack)

        self.btn_info_color = QPushButton(self.temp['info_color'])
        self._style_color_button(self.btn_info_color, self.temp['info_color'])
        self.btn_info_color.clicked.connect(lambda: self.pick_color('info_color', self.btn_info_color))
        time_form.addRow('Цвет доп. текста:', self.btn_info_color)

        self.chk_show_date = QCheckBox('Показывать дату')
        self.chk_show_date.setChecked(self.temp.get('show_date', True))
        time_form.addRow(self.chk_show_date)

        self.btn_date_color = QPushButton(self.temp.get('date_color', '#8892b0'))
        self._style_color_button(self.btn_date_color, self.temp.get('date_color', '#8892b0'))
        self.btn_date_color.clicked.connect(lambda: self.pick_color('date_color', self.btn_date_color))
        time_form.addRow('Цвет даты:', self.btn_date_color)

        self.tabs.addTab(time_widget, '✏️ Время')

        # ================= ЭФФЕКТЫ =================
        fx_widget = QWidget()
        fx_form = QFormLayout(fx_widget)
        fx_form.setContentsMargins(16, 16, 16, 16)

        self.chk_shadow = QCheckBox('Тень времени')
        self.chk_shadow.setChecked(self.temp.get('time_shadow', False))
        fx_form.addRow(self.chk_shadow)

        self.btn_shadow_color = QPushButton(self.temp.get('time_shadow_color', '#000000'))
        self._style_color_button(self.btn_shadow_color, self.temp.get('time_shadow_color', '#000000'))
        self.btn_shadow_color.clicked.connect(lambda: self.pick_color('time_shadow_color', self.btn_shadow_color))
        fx_form.addRow('Цвет тени:', self.btn_shadow_color)

        self.chk_outline = QCheckBox('Обводка времени')
        self.chk_outline.setChecked(self.temp.get('time_outline', False))
        fx_form.addRow(self.chk_outline)

        self.btn_outline_color = QPushButton(self.temp.get('time_outline_color', '#ffffff'))
        self._style_color_button(self.btn_outline_color, self.temp.get('time_outline_color', '#ffffff'))
        self.btn_outline_color.clicked.connect(lambda: self.pick_color('time_outline_color', self.btn_outline_color))
        fx_form.addRow('Цвет обводки:', self.btn_outline_color)

        self.chk_pulse = QCheckBox('💓 Пульсация времени')
        self.chk_pulse.setChecked(self.temp.get('time_pulse', False))
        fx_form.addRow(self.chk_pulse)

        self.theme_combo = QComboBox()
        for key, theme in THEMES.items():
            self.theme_combo.addItem(theme['name'], key)
        for idx in range(self.theme_combo.count()):
            if self.theme_combo.itemData(idx) == self.temp.get('theme', 'custom'):
                self.theme_combo.setCurrentIndex(idx)
                break
        self.theme_combo.currentIndexChanged.connect(self.on_theme_changed)
        fx_form.addRow('Пресет темы:', self.theme_combo)

        self.tabs.addTab(fx_widget, '✨ Эффекты')

        # ================= ЗВОНКИ =================
        bells_scroll = QScrollArea()
        bells_scroll.setWidgetResizable(True)
        bells_widget = QWidget()
        bells_layout = QVBoxLayout(bells_widget)
        bells_layout.setContentsMargins(16, 16, 16, 16)

        days_row = QHBoxLayout()
        days_row.addWidget(QLabel('Учебных дней:'))
        self.schedule_days_combo = QComboBox()
        self.schedule_days_combo.addItems(['5 дней (Пн-Пт)', '6 дней (Пн-Сб)'])
        if SETTINGS.get('schedule_days', 6) == 5:
            self.schedule_days_combo.setCurrentIndex(0)
        else:
            self.schedule_days_combo.setCurrentIndex(1)
        days_row.addWidget(self.schedule_days_combo)
        days_row.addStretch()
        bells_layout.addLayout(days_row)

        self.chk_sunday = QCheckBox('Воскресенье — учебный день')
        self.chk_sunday.setChecked(SETTINGS.get('sunday_enabled', False))
        bells_layout.addWidget(self.chk_sunday)

        lbl_mon = QLabel('——— Понедельник ———')
        lbl_mon.setStyleSheet('color: #b7c9ff; font-weight: bold; padding-top: 10px;')
        bells_layout.addWidget(lbl_mon)

        hint = QLabel('Формат: 08:00-08:45 (пусто — нет пары)')
        hint.setStyleSheet('color: #8892b0; font-size: 11px;')
        bells_layout.addWidget(hint)

        self.bell_fields_monday = []
        for i in range(7):
            row = QHBoxLayout()
            lbl = QLabel(f'{i+1}:')
            lbl.setFixedWidth(30)
            row.addWidget(lbl)
            le = QLineEdit()
            le.setPlaceholderText('08:00-08:45')
            row.addWidget(le)
            self.bell_fields_monday.append(le)
            bells_layout.addLayout(row)

        lbl_other = QLabel('——— Вторник-Суббота ———')
        lbl_other.setStyleSheet('color: #b7c9ff; font-weight: bold; padding-top: 10px;')
        bells_layout.addWidget(lbl_other)

        self.bell_fields_other = []
        for i in range(7):
            row = QHBoxLayout()
            lbl = QLabel(f'{i+1}:')
            lbl.setFixedWidth(30)
            row.addWidget(lbl)
            le = QLineEdit()
            le.setPlaceholderText('08:00-09:30')
            row.addWidget(le)
            self.bell_fields_other.append(le)
            bells_layout.addLayout(row)

        self.btn_save_bells = QPushButton('💾 Сохранить звонки')
        self.btn_save_bells.setStyleSheet("""
            QPushButton {
                background: #2a6045; color: #b7ffd9;
                border: none; border-radius: 6px; padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background: #3a8060; }
        """)
        self.btn_save_bells.clicked.connect(self._save_bells)
        bells_layout.addWidget(self.btn_save_bells)
        bells_layout.addStretch()

        bells_scroll.setWidget(bells_widget)
        self.tabs.addTab(bells_scroll, '🔔 Звонки')

        # ================= ПОВЕДЕНИЕ =================
        behavior_box = QWidget()
        behavior_layout = QVBoxLayout(behavior_box)
        behavior_layout.setContentsMargins(0, 8, 0, 0)

        self.chk_fullscreen = QCheckBox('Скрывать при фуллскрине')
        self.chk_fullscreen.setChecked(self.temp['auto_hide_fullscreen'])
        behavior_layout.addWidget(self.chk_fullscreen)

        self.chk_smart = QCheckBox('Умный режим')
        self.chk_smart.setChecked(self.temp['smart_load'])
        behavior_layout.addWidget(self.chk_smart)

        # Информация о версии
        version_label = QLabel(f'Версия: v{CURRENT_VERSION}')
        version_label.setStyleSheet('color: #5a6488; font-size: 11px; padding-top: 6px;')
        behavior_layout.addWidget(version_label)

        main_layout.addWidget(behavior_box)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText('Применить')
        btns.button(QDialogButtonBox.Cancel).setText('Отмена')
        btns.accepted.connect(self.apply)
        btns.rejected.connect(self.reject)
        main_layout.addWidget(btns)

        self.on_bg_fill_changed(self.bg_fill_combo.currentIndex())
        self.on_time_mode_changed(self.time_mode_combo.currentIndex())
        self._load_bells()

    def _load_bells(self):
        try:
            data = load_bells()
            mon = data.get('monday', [])
            for i in range(7):
                if i < len(mon) and isinstance(mon[i], (list, tuple)) and len(mon[i]) >= 2:
                    self.bell_fields_monday[i].setText(f'{mon[i][0]}-{mon[i][1]}')
                else:
                    self.bell_fields_monday[i].setText('')
            other = data.get('other', [])
            for i in range(7):
                if i < len(other) and isinstance(other[i], (list, tuple)) and len(other[i]) >= 2:
                    self.bell_fields_other[i].setText(f'{other[i][0]}-{other[i][1]}')
                else:
                    self.bell_fields_other[i].setText('')
        except Exception as e:
            print('Ошибка _load_bells:', e)

    def _save_bells(self):
        try:
            new_monday = []
            for le in self.bell_fields_monday:
                text = le.text().strip()
                if not text:
                    continue
                if '-' in text:
                    s, e = text.split('-', 1)
                    if s.strip() and e.strip():
                        new_monday.append([s.strip(), e.strip()])
            new_other = []
            for le in self.bell_fields_other:
                text = le.text().strip()
                if not text:
                    continue
                if '-' in text:
                    s, e = text.split('-', 1)
                    if s.strip() and e.strip():
                        new_other.append([s.strip(), e.strip()])

            save_bells({'monday': new_monday, 'other': new_other})

            SETTINGS['schedule_days'] = 5 if self.schedule_days_combo.currentIndex() == 0 else 6
            SETTINGS['sunday_enabled'] = self.chk_sunday.isChecked()
            save_design(SETTINGS)

            apply_bells_from_file()
            if self.parent() and hasattr(self.parent(), 'update_all'):
                self.parent().update_all()
            print(f'[Bells] Пн: {len(new_monday)}, Вт-Сб: {len(new_other)}')
        except Exception as e:
            print('Ошибка _save_bells:', e)

    def on_bg_fill_changed(self, idx):
        if idx == 0:
            self.lbl_bg_c1.show(); self.btn_color1.show()
            self.lbl_bg_c2.show(); self.btn_color2.show()
            self.lbl_alpha.show(); self.slider_alpha.show()
        elif idx == 1:
            self.lbl_bg_c1.show(); self.btn_color1.show()
            self.lbl_bg_c2.hide(); self.btn_color2.hide()
            self.lbl_alpha.show(); self.slider_alpha.show()
        else:
            self.lbl_bg_c1.hide(); self.btn_color1.hide()
            self.lbl_bg_c2.hide(); self.btn_color2.hide()
            self.lbl_alpha.hide(); self.slider_alpha.hide()

    def on_time_mode_changed(self, idx):
        self.time_stack.setCurrentIndex(idx)

    def on_theme_changed(self, idx):
        key = self.theme_combo.itemData(idx)
        self.temp['theme'] = key
        if key == 'custom':
            return
        theme = THEMES.get(key, {})
        for k, v in theme.items():
            if k == 'name':
                continue
            self.temp[k] = v

    def _style_color_button(self, btn, hex_color):
        btn.setStyleSheet(
            f"background: {hex_color}; color: white; padding: 6px; "
            f"border-radius: 6px; border: 1px solid #2e354a;"
        )

    def pick_color(self, key, btn):
        current = hex_to_qcolor(self.temp[key])
        color = QColorDialog.getColor(current, self, 'Выберите цвет')
        if color.isValid():
            hex_color = qcolor_to_hex(color)
            self.temp[key] = hex_color
            self._style_color_button(btn, hex_color)
            btn.setText(hex_color)

    def apply(self):
        bg_map = {0: 'gradient', 1: 'solid', 2: 'transparent'}
        self.temp['bg_fill_mode'] = bg_map[self.bg_fill_combo.currentIndex()]
        time_map = {0: 'solid', 1: 'gradient', 2: 'rainbow'}
        self.temp['time_mode'] = time_map[self.time_mode_combo.currentIndex()]
        rb_map = {0: 'line', 1: 'digits'}
        self.temp['time_rainbow_mode'] = rb_map[self.rainbow_mode_combo.currentIndex()]
        self.temp['time_rainbow_speed'] = self.slider_rainbow_speed.value()
        self.temp['alpha'] = self.slider_alpha.value()
        self.temp['corner_radius'] = self.spin_radius.value()
        self.temp['time_font_size'] = self.spin_font.value()
        self.temp['auto_hide_fullscreen'] = self.chk_fullscreen.isChecked()
        self.temp['smart_load'] = self.chk_smart.isChecked()
        self.temp['show_date'] = self.chk_show_date.isChecked()
        self.temp['time_shadow'] = self.chk_shadow.isChecked()
        self.temp['time_outline'] = self.chk_outline.isChecked()
        self.temp['time_pulse'] = self.chk_pulse.isChecked()

        SETTINGS.update(self.temp)
        save_design(SETTINGS)

        if self.parent() and hasattr(self.parent(), 'apply_settings'):
            self.parent().apply_settings()
        self.accept()

# ============================================================
# ЗАСТАВКА (SPLASH SCREEN)
# ============================================================
class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAutoFillBackground(False)
        self.setFixedSize(320, 220)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignCenter)

        # Иконка (большая)
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap(120, 120)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        gradient = QLinearGradient(0, 0, 120, 120)
        gradient.setColorAt(0, QColor(40, 60, 100))
        gradient.setColorAt(1, QColor(26, 31, 46))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, 120, 120, 26, 26)
        pen = painter.pen()
        pen.setColor(QColor(183, 201, 255))
        pen.setWidth(6)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(24, 24, 72, 72)
        painter.drawLine(60, 60, 60, 38)
        painter.drawLine(60, 60, 82, 68)
        painter.end()
        self.icon_label.setPixmap(pixmap)

        # Название
        self.title_label = QLabel('📅 Расписание')
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet(
            'color: #ffffff; font-size: 22px; font-weight: bold;'
        )

        # Версия
        self.version_label = QLabel(f'Версия {CURRENT_VERSION}')
        self.version_label.setAlignment(Qt.AlignCenter)
        self.version_label.setStyleSheet(
            'color: #8892b0; font-size: 13px;'
        )

        layout.addWidget(self.icon_label)
        layout.addWidget(self.title_label)
        layout.addWidget(self.version_label)
        self.setLayout(layout)

        # Прозрачность — начнём с 0
        self.setWindowOpacity(0.0)

        # Центрирование на экране
        self._center_on_screen()

    def _center_on_screen(self):
        """Центрирует заставку на основном экране."""
        try:
            screen = QApplication.primaryScreen()
            if screen:
                geo = screen.geometry()
                x = (geo.width() - self.width()) // 2
                y = (geo.height() - self.height()) // 2
                self.move(x, y)
        except Exception:
            self.move(500, 300)

    def paintEvent(self, event):
        """Рисует полупрозрачный фон с размытием."""
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            # Полупрозрачный фон
            path = QPainterPath()
            r = 20
            path.addRoundedRect(QRectF(self.rect()), r, r)
            painter.setClipPath(path)

            # Градиент
            gradient = QLinearGradient(0, 0, self.width(), self.height())
            gradient.setColorAt(0, QColor(26, 31, 46, 240))
            gradient.setColorAt(1, QColor(40, 60, 100, 240))
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(self.rect(), r, r)
        except Exception as e:
            print('Ошибка в SplashScreen.paintEvent:', e)

    def show_animated(self, on_finish):
        """Показывает заставку с анимацией."""
        self.show()

        # Появление (0.5 сек)
        self.anim_in = QPropertyAnimation(self, b'windowOpacity')
        self.anim_in.setDuration(500)
        self.anim_in.setStartValue(0.0)
        self.anim_in.setEndValue(1.0)
        self.anim_in.setEasingCurve(QEasingCurve.InOutQuad)
        self.anim_in.start()
        self._anim_in = self.anim_in

        # Через 1.5 сек — исчезновение
        QTimer.singleShot(1500, lambda: self._fade_out(on_finish))

    def _fade_out(self, callback):
        self.anim_out = QPropertyAnimation(self, b'windowOpacity')
        self.anim_out.setDuration(500)
        self.anim_out.setStartValue(1.0)
        self.anim_out.setEndValue(0.0)
        self.anim_out.setEasingCurve(QEasingCurve.InOutQuad)
        self.anim_out.finished.connect(self.close)
        if callback:
            self.anim_out.finished.connect(callback)
        self.anim_out.start()
        self._anim_out = self.anim_out

# ============================================================
# ОВЕРЛЕЙ
# ============================================================
class Overlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAutoFillBackground(False)
        self.old_pos = None
        self.drag_started = False
        self.current_mode = 'starting'
        self.user_hidden = False
        self._pulse_phase = 0

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(2)

        self.date_label = QLabel()
        self.date_label.setAlignment(Qt.AlignCenter)
        self.date_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.time_label = OutlinedLabel()
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.remain_label = QLabel()
        self.remain_label.setAlignment(Qt.AlignCenter)
        self.remain_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout.addWidget(self.date_label)
        layout.addWidget(self.time_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.remain_label)
        layout.addStretch()
        self.setLayout(layout)

        self.apply_settings()
        self._safe_move(SETTINGS['pos_x'], SETTINGS['pos_y'])
        self.setWindowOpacity(0.0)
        self.update_all()

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._tick)
        self.update_timer.start(2000)

        self.rainbow_timer = QTimer()
        self.rainbow_timer.timeout.connect(self._update_rainbow)
        self.rainbow_timer.start(100)

        self.visibility_timer = QTimer()
        self.visibility_timer.timeout.connect(self._check_visibility_safe)
        self.visibility_timer.start(500)

        self.load_timer = QTimer()
        self.load_timer.timeout.connect(self._check_load_safe)
        self.load_timer.start(5000)

        self.raise_timer = QTimer()
        self.raise_timer.timeout.connect(self._keep_on_top)
        self.raise_timer.start(500)

        self.watchdog_timer = QTimer()
        self.watchdog_timer.timeout.connect(self._watchdog_check)
        self.watchdog_timer.start(10000)

        self.startup_checks_left = STARTUP_LOAD_CHECKS
        self.startup_timer = QTimer()
        self.startup_timer.timeout.connect(self.startup_load_check)
        self.startup_timer.start(STARTUP_CHECK_INTERVAL)

    def _watchdog_check(self):
        try:
            now = datetime.now()
            real_time = now.hour * 60 + now.minute
            shown = getattr(self, '_last_shown_time', None)
            if shown is not None and real_time - shown > 1:
                self.update_timer.stop()
                self.update_timer.start(2000)
                self.update_all()
        except Exception as e:
            print('Ошибка в watchdog:', e)

    def _safe_move(self, x, y):
        try:
            monitor = get_monitor_for_point(x + self.width() // 2, y + self.height() // 2)
            mx, my, mw, mh = monitor
            x = max(mx, min(x, mx + mw - self.width()))
            y = max(my, min(y, my + mh - self.height()))
        except Exception:
            x, y = 50, 50
        self.move(x, y)

    def _fit_height(self):
        try:
            self.layout().activate()
            hint = self.layout().sizeHint()
            new_height = max(60, hint.height() + 16)
            if new_height != self.height():
                self.setFixedHeight(new_height)
                self._safe_move(self.x(), self.y())
        except Exception as e:
            print('Ошибка в _fit_height:', e)

    def _tick(self):
        try:
            self.update_all()
        except Exception as e:
            print('Ошибка в update_all:', e)

    def _update_rainbow(self):
        try:
            if SETTINGS.get('time_mode', 'solid') != 'rainbow' and not SETTINGS.get('time_pulse', False):
                return
            if not self.isVisible():
                return
            self._render_time()
        except Exception as e:
            print('Ошибка в _update_rainbow:', e)

    def _check_visibility_safe(self):
        try:
            self.check_visibility()
        except Exception as e:
            print('Ошибка в check_visibility:', e)

    def _check_load_safe(self):
        try:
            self.check_load()
        except Exception as e:
            print('Ошибка в check_load:', e)

    def _keep_on_top(self):
        try:
            if self.isVisible():
                self.raise_()
        except Exception:
            pass

    def _render_time(self):
        try:
            now = datetime.now()
            time_text = now.strftime('%H:%M')

            base_size = SETTINGS.get('time_font_size', 36)
            if SETTINGS.get('time_pulse', False):
                self._pulse_phase = (self._pulse_phase + 1) % 60
                pulse_scale = 1.0 + 0.06 * math.sin(self._pulse_phase / 60 * 2 * math.pi)
                new_size = max(16, int(base_size * pulse_scale))
                self.time_label.setFont(QFont('Segoe UI', new_size, QFont.Bold))
            else:
                self.time_label.setFont(QFont('Segoe UI', base_size, QFont.Bold))

            mode = SETTINGS.get('time_mode', 'solid')
            char_colors = []

            if mode == 'rainbow':
                speed = SETTINGS.get('time_rainbow_speed', 5)
                rb_mode = SETTINGS.get('time_rainbow_mode', 'line')
                total_seconds = (now.hour * 3600 + now.minute * 60 + now.second
                                 + now.microsecond / 1000000.0)
                hue_shift = (total_seconds * speed * 10) % 360
                for idx, ch in enumerate(time_text):
                    if ch == ':':
                        char_colors.append(QColor('#8892b0'))
                    else:
                        if rb_mode == 'line':
                            hue = int((hue_shift + idx * 25) % 360)
                        else:
                            hue = int((hue_shift + idx * 90) % 360)
                        hue = max(0, min(359, hue))
                        char_colors.append(QColor.fromHsv(hue, 220, 255))
            elif mode == 'gradient':
                c1 = hex_to_qcolor(SETTINGS.get('time_gradient_color1', '#ff6b9d'))
                c2 = hex_to_qcolor(SETTINGS.get('time_gradient_color2', '#4ecdc4'))
                for idx, ch in enumerate(time_text):
                    if ch == ':':
                        char_colors.append(c2)
                    else:
                        char_colors.append(c1)

            self.time_label.set_text_color(SETTINGS.get('time_color', '#ffffff'))
            self.time_label.set_shadow(
                SETTINGS.get('time_shadow', False),
                SETTINGS.get('time_shadow_color', '#000000')
            )
            self.time_label.set_outline(
                SETTINGS.get('time_outline', False),
                SETTINGS.get('time_outline_color', '#ffffff')
            )
            self.time_label.set_char_colors(char_colors if char_colors else [])
            self.time_label.setText(time_text)
            self.time_label.update()
        except Exception as e:
            print('Ошибка в _render_time:', e)

    def apply_settings(self):
        try:
            self.setFixedWidth(SETTINGS['window_width'])
            self.setMinimumHeight(60)
            self.setMaximumHeight(500)

            self.time_label.setStyleSheet("")
            self.date_label.setFont(QFont('Segoe UI', 10))
            self.date_label.setStyleSheet(f"color: {SETTINGS['date_color']};")

            self.status_label.setFont(QFont('Segoe UI', 14, QFont.Bold))
            self.status_label.setStyleSheet(f"color: {SETTINGS['info_color']};")

            self.remain_label.setFont(QFont('Segoe UI', 11))
            self.remain_label.setStyleSheet(f"color: {SETTINGS['info_color']};")

            self.update()
            QTimer.singleShot(50, self._fit_height)
        except Exception as e:
            print('Ошибка в apply_settings:', e)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background: #1a1f2e; color: #e8edf5; border: 1px solid #2e354a; }
            QMenu::item:selected { background: #2a3045; }
        """)
        act_settings = QAction('⚙️ Настройки', self)
        act_settings.triggered.connect(self.open_settings)
        menu.addAction(act_settings)

        act_update = QAction('🔄 Проверить обновления', self)
        act_update.triggered.connect(check_for_updates)
        menu.addAction(act_update)

        menu.addSeparator()
        act_hide = QAction('👁️ Скрыть виджет', self)
        act_hide.triggered.connect(self.hide_widget)
        menu.addAction(act_hide)
        act_exit = QAction('❌ Выход', self)
        act_exit.triggered.connect(self.exit_app)
        menu.addAction(act_exit)
        menu.exec_(event.globalPos())

    def open_settings(self):
        try:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
            self.show()
        except Exception as e:
            print('Ошибка снятия флага:', e)

        dlg = SettingsDialog(self)
        dlg.exec_()

        try:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
            self.show()
        except Exception as e:
            print('Ошибка возврата флага:', e)

    def hide_widget(self):
        self.user_hidden = True
        self.fade_out(callback=self.hide)

    def exit_app(self):
        QApplication.quit()

    def startup_load_check(self):
        try:
            cpu, ram = get_system_load()
            if cpu >= CPU_CRITICAL_THRESHOLD:
                return
            self.startup_checks_left -= 1
            if self.startup_checks_left <= 0:
                self.startup_timer.stop()
                if cpu >= CPU_HIGH_THRESHOLD or ram >= RAM_HIGH_THRESHOLD:
                    self.current_mode = 'slow'
                else:
                    self.current_mode = 'normal'
                QTimer.singleShot(FADE_START_DELAY, self.fade_in)
        except Exception as e:
            print('Ошибка в startup_load_check:', e)

    def fade_in(self):
        try:
            cpu, ram = get_system_load()
            if cpu >= CPU_CRITICAL_THRESHOLD:
                QTimer.singleShot(2000, self.fade_in)
                return
            self.show()
            self.anim = QPropertyAnimation(self, b'windowOpacity')
            self.anim.setDuration(FADE_IN_DURATION)
            self.anim.setStartValue(0.0)
            self.anim.setEndValue(1.0)
            self.anim.setEasingCurve(QEasingCurve.InOutQuad)
            self.anim.start()
            self._fade_anim = self.anim
        except Exception as e:
            print('Ошибка в fade_in:', e)
            self.show()

    def fade_out(self, callback=None):
        try:
            self.anim_out = QPropertyAnimation(self, b'windowOpacity')
            self.anim_out.setDuration(800)
            self.anim_out.setStartValue(self.windowOpacity())
            self.anim_out.setEndValue(0.0)
            self.anim_out.setEasingCurve(QEasingCurve.InOutQuad)
            if callback:
                self.anim_out.finished.connect(callback)
            self.anim_out.start()
            self._fade_out_anim = self.anim_out
        except Exception:
            if callback:
                callback()

    def paintEvent(self, event):
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            r = SETTINGS['corner_radius']

            path = QPainterPath()
            path.addRoundedRect(QRectF(self.rect()), r, r)
            painter.setClipPath(path)

            mode = SETTINGS.get('bg_fill_mode', 'gradient')
            if mode == 'transparent':
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor(0, 0, 0, 0)))
                painter.drawRoundedRect(self.rect(), r, r)
                return

            alpha = int(255 * SETTINGS['alpha'] / 100)
            if mode == 'gradient':
                c1 = hex_to_qcolor(SETTINGS['color1'], alpha)
                c2 = hex_to_qcolor(SETTINGS['color2'], alpha)
                gradient = QLinearGradient(0, 0, self.width(), self.height())
                gradient.setColorAt(0, c1)
                gradient.setColorAt(1, c2)
                painter.setBrush(QBrush(gradient))
            else:
                c1 = hex_to_qcolor(SETTINGS['color1'], alpha)
                painter.setBrush(QBrush(c1))

            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(self.rect(), r, r)
        except Exception as e:
            print('Ошибка в paintEvent:', e)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()
            self.drag_started = False

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = event.globalPos() - self.old_pos
            if abs(delta.x()) > 3 or abs(delta.y()) > 3:
                self.drag_started = True
            self.move(self.pos() + delta)
            self.old_pos = event.globalPos()
            self.update_all()
            self.check_visibility()

    def mouseReleaseEvent(self, event):
        self.old_pos = None
        self.drag_started = False
        self.update_all()
        SETTINGS['pos_x'] = self.x()
        SETTINGS['pos_y'] = self.y()
        save_position(self.x(), self.y())

    def get_widget_monitor(self):
        center_x = self.x() + self.width() // 2
        center_y = self.y() + self.height() // 2
        return get_monitor_for_point(center_x, center_y)

    def check_visibility(self):
        if self.user_hidden:
            return
        if not SETTINGS['auto_hide_fullscreen']:
            return
        if self.current_mode == 'hidden':
            return
        widget_monitor = self.get_widget_monitor()
        if is_fullscreen_on_monitor(widget_monitor):
            if self.isVisible():
                self.fade_out(callback=self.hide)
        else:
            if not self.isVisible() and self.current_mode != 'hidden':
                self.fade_in()

    def check_load(self):
        if not SETTINGS['smart_load']:
            if self.current_mode in ('slow', 'hidden'):
                self.current_mode = 'normal'
                if not self.user_hidden and not self.isVisible():
                    self.fade_in()
            return
        cpu, ram = get_system_load()
        new_mode = 'normal'
        if cpu >= CPU_CRITICAL_THRESHOLD:
            new_mode = 'hidden'
        elif cpu >= CPU_HIGH_THRESHOLD or ram >= RAM_HIGH_THRESHOLD:
            new_mode = 'slow'
        if new_mode == self.current_mode:
            return
        old_mode = self.current_mode
        self.current_mode = new_mode
        if new_mode == 'hidden' and self.isVisible():
            self.fade_out(callback=self.hide)
        elif new_mode != 'hidden' and old_mode == 'hidden' and not self.user_hidden:
            self.fade_in()

    def update_all(self):
        try:
            now = datetime.now()
            current = now.hour * 60 + now.minute
            self._last_shown_time = current

            self._render_time()

            if SETTINGS.get('show_date', True):
                fmt = SETTINGS.get('date_format', 'day_month_year')
                months_ru = ['янв', 'фев', 'мар', 'апр', 'мая', 'июн',
                             'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']
                weekdays_ru = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
                if fmt == 'day_month_year':
                    text = f'{now.day:02d}.{now.month:02d}.{now.year}'
                elif fmt == 'day_month':
                    text = f'{now.day} {months_ru[now.month - 1]}'
                else:
                    text = f'{weekdays_ru[now.weekday()]}, {now.day} {months_ru[now.month - 1]}'
                self.date_label.setText(text)
                self.date_label.show()
            else:
                self.date_label.hide()

            status, remain = get_status_by_bells()
            self.status_label.setText(status)
            self.remain_label.setText(remain)

            QTimer.singleShot(30, self._fit_height)
        except Exception as e:
            print('Ошибка в update_all:', e)

# ============================================================
# ТРЕЙ
# ============================================================
class TrayApp:
    def __init__(self, app, overlay):
        self.app = app
        self.overlay = overlay

        self.tray = QSystemTrayIcon(create_tray_icon(), app)
        self.tray.setToolTip(f'Расписание v{CURRENT_VERSION}')

        self.menu = QMenu()
        self.menu.setStyleSheet("""
            QMenu { background: #1a1f2e; color: #e8edf5; border: 1px solid #2e354a; padding: 4px; }
            QMenu::item { padding: 6px 20px; border-radius: 4px; }
            QMenu::item:selected { background: #2a3045; }
        """)

        self.act_toggle = QAction('👁️ Скрыть виджет', self.menu)
        self.act_toggle.triggered.connect(self.toggle_widget)
        self.menu.addAction(self.act_toggle)

        self.menu.addSeparator()

        self.act_settings = QAction('⚙️ Настройки', self.menu)
        self.act_settings.triggered.connect(self.open_settings)
        self.menu.addAction(self.act_settings)

        self.act_update = QAction('🔄 Проверить обновления', self.menu)
        self.act_update.triggered.connect(check_for_updates)
        self.menu.addAction(self.act_update)

        self.act_reset = QAction('🗑️ Сбросить оформление', self.menu)
        self.act_reset.triggered.connect(self.reset_settings)
        self.menu.addAction(self.act_reset)

        self.act_restart = QAction('🔄 Перезапуск', self.menu)
        self.act_restart.triggered.connect(self.restart_widget)
        self.menu.addAction(self.act_restart)

        self.menu.addSeparator()

        self.act_exit = QAction('❌ Выход', self.menu)
        self.act_exit.triggered.connect(self.exit_app)
        self.menu.addAction(self.act_exit)

        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_toggle_text)
        self.timer.start(1000)

    def update_toggle_text(self):
        if self.overlay.user_hidden:
            self.act_toggle.setText('👁️ Показать виджет')
        else:
            self.act_toggle.setText('👁️ Скрыть виджет')

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.toggle_widget()

    def toggle_widget(self):
        if self.overlay.user_hidden:
            self.overlay.user_hidden = False
            self.overlay.fade_in()
        else:
            self.overlay.user_hidden = True
            self.overlay.fade_out(callback=self.overlay.hide)

    def open_settings(self):
        try:
            self.overlay.setWindowFlag(Qt.WindowStaysOnTopHint, False)
            self.overlay.show()
        except Exception:
            pass
        dlg = SettingsDialog(self.overlay)
        dlg.exec_()
        try:
            self.overlay.setWindowFlag(Qt.WindowStaysOnTopHint, True)
            self.overlay.show()
        except Exception:
            pass

    def reset_settings(self):
        global SETTINGS
        cur_x = self.overlay.x()
        cur_y = self.overlay.y()
        reset_design()
        SETTINGS = load_settings()
        SETTINGS['pos_x'] = cur_x
        SETTINGS['pos_y'] = cur_y
        save_design(SETTINGS)
        save_position(cur_x, cur_y)
        self.overlay.apply_settings()
        self.overlay.update_all()

    def restart_widget(self):
        try:
            save_position(self.overlay.x(), self.overlay.y())
        except Exception:
            pass
        reset_memory()
        try:
            self.tray.hide()
        except Exception:
            pass
        python = sys.executable
        os.execv(python, [python] + sys.argv)

    def exit_app(self):
        try:
            MEMORY['last_theme'] = SETTINGS.get('theme', 'custom')
            save_memory(MEMORY)
        except Exception:
            pass
        self.tray.hide()
        self.app.quit()

# ============================================================
# ЗАПУСК
# ============================================================
if __name__ == '__main__':
    apply_bells_from_file()

    QApplication.setQuitOnLastWindowClosed(False)
    app = QApplication(sys.argv)
    app.setApplicationName('Расписание')

    # Заставка
    splash = SplashScreen()

    # Создаём виджет (он пока невидимый)
    overlay = Overlay()
    tray = TrayApp(app, overlay)

    def on_splash_finish():
        """Когда заставка исчезла — проверяем обновления."""
        QTimer.singleShot(500, check_for_updates)

    splash.show_animated(on_splash_finish)

    sys.exit(app.exec_())
