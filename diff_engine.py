# Part 1 of diff_viewer_final.py
import pygame
import sys
import os
import json
import ctypes
import time
import pyperclip
import re
import traceback
import difflib
from ctypes import wintypes
import threading
import winreg
import locale
import platform
version = "v2.66"

def __init__(self, parent_pid=None, monitors=None, pos_x=None, pos_y=None, height=None, font_name=None, font_size=None, is_pro=False):
    os.environ['SDL_HINT_RENDER_BATCHING'] = '1'
    os.environ['SDL_MOUSE_FOCUS_CLICKTHROUGH'] = "1"
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
    os.environ['SDL_WINDOWS_DPI_AWARENESS'] = 'permonitorv2'

    if 'SDL_RENDER_DRIVER' in os.environ:
        del os.environ['SDL_RENDER_DRIVER']

    try:
        def _pre_log(m):
            try:
                appdata = os.environ.get('APPDATA', '')
                if appdata:
                    pre_dir = os.path.join(appdata, "CodeStitcher")
                    os.makedirs(pre_dir, exist_ok=True)
                else:
                    if getattr(sys, "frozen", False) or "__compiled__" in globals():
                        pre_dir = os.path.dirname(os.path.abspath(sys.executable))
                    else:
                        pre_dir = os.path.dirname(os.path.abspath(__file__))

                with open(os.path.join(pre_dir, "stitch_viewer_debug.log"), "a", encoding="utf-8") as f:
                    f.write(f"[{time.strftime('%H:%M:%S')}] [PRE-INIT] {m}\n")
            except:
                pass

        _pre_log(f"__init__ started with parent_pid={parent_pid}, is_pro={is_pro}")

        
        if os.name == 'nt':
            try:
                kernel32 = ctypes.windll.kernel32
                user32 = ctypes.windll.user32
                shell32 = ctypes.windll.shell32

                kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
                kernel32.CreateMutexW.restype = wintypes.HANDLE

                shell32.SetCurrentProcessExplicitAppUserModelID.argtypes = [wintypes.LPCWSTR]
                shell32.SetCurrentProcessExplicitAppUserModelID.restype = ctypes.c_long

                kernel32.GetLongPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
                kernel32.GetLongPathNameW.restype = wintypes.DWORD

                user32.LoadImageW.argtypes = [wintypes.HINSTANCE, wintypes.LPCWSTR, wintypes.UINT, ctypes.c_int, ctypes.c_int, wintypes.UINT]
                user32.LoadImageW.restype = wintypes.HANDLE

                user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
                user32.SendMessageW.restype = wintypes.LPARAM

                
                if platform.architecture()[0] == '64bit':
                    user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
                    user32.GetWindowLongPtrW.restype = ctypes.c_void_p

                    user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_void_p]
                    user32.SetWindowLongPtrW.restype = ctypes.c_void_p
                    self._GetWindowLong = user32.GetWindowLongPtrW
                    self._SetWindowLong = user32.SetWindowLongPtrW
                else:
                    user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
                    user32.GetWindowLongW.restype = ctypes.c_long

                    user32.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_long]
                    user32.SetWindowLongW.restype = ctypes.c_long
                    self._GetWindowLong = user32.GetWindowLongW
                    self._SetWindowLong = user32.SetWindowLongW

                user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
                user32.SetWindowPos.restype = wintypes.BOOL

                user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
                user32.ShowWindow.restype = wintypes.BOOL

                user32.SetForegroundWindow.argtypes = [wintypes.HWND]
                user32.SetForegroundWindow.restype = wintypes.BOOL

                user32.SetLayeredWindowAttributes.argtypes = [wintypes.HWND, wintypes.COLORREF, ctypes.c_byte, wintypes.DWORD]
                user32.SetLayeredWindowAttributes.restype = wintypes.BOOL

                user32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
                user32.GetCursorPos.restype = wintypes.BOOL

                user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
                user32.GetWindowRect.restype = wintypes.BOOL

            except Exception as e:
                _pre_log(f"Warning: Failed to setup strict ctypes argtypes: {e}")

        if os.name == 'nt':
            try:
                self.mutex_name = "Global\\CodeStitcherCodeStitcher_MUTEX"
                self.mutex = ctypes.windll.kernel32.CreateMutexW(None, False, self.mutex_name)

                if ctypes.windll.kernel32.GetLastError() == 183:
                    _pre_log("FATAL: Another Stitcher Viewer instance is already running. Enforcing single instance.")
                    sys.exit(0)
            except Exception as e:
                _pre_log(f"Warning: Failed to create Mutex lock: {e}")

        self.parent_pid = parent_pid
        self.is_pro = is_pro

        if os.name == 'nt':
            try:
                myappid = 'uep.codestitcher.version.1.0'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            except Exception as e:
                _pre_log(f"Warning: SetCurrentProcessExplicitAppUserModelID failed: {e}")

        try:
            pygame.init()
            pygame.font.init()
            pygame.key.set_repeat(400, 60)
            _pre_log("Pygame initialized successfully with key repeat enabled.")
        except Exception as e:
            _pre_log(f"FATAL: Pygame init failed: {e}")

        self.width = 1260
        self.height = 750
        self.title_bar_height = 19
        self.GAP_WIDTH = 50
        self.minimap_width = 24

        if getattr(sys, "frozen", False) or "__compiled__" in globals():
            self.script_dir = os.path.dirname(os.path.abspath(sys.executable))
            if hasattr(sys, "_MEIPASS"):
                self.asset_dir = sys._MEIPASS
            else:
                self.asset_dir = os.path.dirname(os.path.abspath(__file__))
        else:
            self.script_dir = os.path.dirname(os.path.abspath(__file__))
            self.asset_dir = self.script_dir

        if os.name == 'nt':
            try:
                buf = ctypes.create_unicode_buffer(1024)
                if ctypes.windll.kernel32.GetLongPathNameW(self.script_dir, buf, 1024):
                    self.script_dir = buf.value
                if ctypes.windll.kernel32.GetLongPathNameW(self.asset_dir, buf, 1024):
                    self.asset_dir = buf.value
            except Exception as e:
                _pre_log(f"Warning: Failed to expand short path: {e}")

        self._log = self._log
        self._log(f"Path verification -> script_dir: {self.script_dir} | asset_dir: {self.asset_dir}")

        self.config = {
            "search_dirs": monitors if monitors else [self.script_dir],
            "CONF_WINDOW_HEIGHT": height if height else 750,
            "CONF_FONT_NAME": font_name if font_name else 'consolas',
            "CONF_FONT_SIZE": font_size if font_size else 13,
            "CONF_REMEMBER_WINDOW_POS": True,
            "CONF_VIEWER_ALWAYS_ON_TOP": True,
            "CONF_VIEWER_WIDTH": 1260,
        }

        
        appdata = os.environ.get('APPDATA', '')
        conf_dir = os.path.join(appdata, "CodeStitcher") if appdata else self.script_dir
        ini_path = os.path.join(conf_dir, "cs_settings.ini")

        ini_found_topmost = False
        if os.path.exists(ini_path):
            try:
                with open(ini_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line_stripped = line.strip()
                        if line_stripped.startswith('CONF_VIEWER_ALWAYS_ON_TOP'):
                            val = line.split('=', 1)[1].strip().strip('"\'').lower()
                            self.config['CONF_VIEWER_ALWAYS_ON_TOP'] = (val == 'true')
                            ini_found_topmost = True
                        elif line_stripped.startswith('CONF_VIEWER_WIDTH'):
                            val = line.split('=', 1)[1].strip().strip('"\'')
                            try:
                                self.config['CONF_VIEWER_WIDTH'] = int(float(val))
                            except: pass
            except: pass

        if not ini_found_topmost:
            self._update_ini_setting('CONF_VIEWER_ALWAYS_ON_TOP', 'True')

        try:
            self.width = max(800, int(float(self.config.get("CONF_VIEWER_WIDTH", 1260))))
        except (ValueError, TypeError):
            self.width = 1260

        try:
            conf_h = int(float(self.config.get('CONF_WINDOW_HEIGHT', 750))) - 1
            self.height = max(500, conf_h)
            self._log(f"Applied CONF_WINDOW_HEIGHT (with -1 offset): {self.height}")
        except (ValueError, TypeError):
            pass

        self.tree_data = {}

        self.render_list = []
        self.active_entry_id = None
        self._load_history()

        pos_valid = False

        parent_rect = self._get_parent_window_rect()
        if parent_rect:
            try:
                lx = int(parent_rect[0]) - self.width - 10
                ly = int(parent_rect[1])
                if -4000 < lx < 12000 and -4000 < ly < 12000:
                    os.environ['SDL_VIDEO_WINDOW_POS'] = f"{lx},{ly}"
                    pos_valid = True
                    self._log(f"Spawning window on left hand side of parent: {lx},{ly}")
            except (ValueError, TypeError):
                pass

        if not pos_valid:
            os.environ['SDL_VIDEO_WINDOW_POS'] = "100,100"
            self._log("Spawning window at default pos 100, 100")

        self._log("Creating Pygame display surface...")

        flags = pygame.NOFRAME | pygame.DOUBLEBUF
        if hasattr(pygame, 'HIDDEN'):
            flags |= getattr(pygame, 'HIDDEN')

        
        try:
            self.screen = pygame.display.set_mode((self.width, self.height), flags)
            pygame.display.set_caption(f"Stitch Viewer {version}")
        except Exception as e:
            self._log(f"Warning: Hardware Doublebuf failed, reverting: {e}")
            flags_fallback = pygame.NOFRAME
            if hasattr(pygame, 'HIDDEN'): flags_fallback |= getattr(pygame, 'HIDDEN')
            self.screen = pygame.display.set_mode((self.width, self.height), flags_fallback)

        self.running = True
        self.hwnd = None

        if os.name == 'nt':
            try:
                self.hwnd = pygame.display.get_wm_info()['window']
                self._log(f"Retrieved Window HWND: {self.hwnd}")

                icon_path = os.path.join(self.asset_dir, "stitch_viewer.ico")
                if not os.path.exists(icon_path):
                    icon_path = os.path.join(self.script_dir, "stitch_viewer.ico")
                if not os.path.exists(icon_path):
                    icon_path = os.path.join(self.asset_dir, "code_stitcher.ico")
                if not os.path.exists(icon_path):
                    icon_path = os.path.join(self.script_dir, "code_stitcher.ico")

                if os.path.exists(icon_path):
                    WM_SETICON = 0x0080
                    hIcon = ctypes.windll.user32.LoadImageW(None, icon_path, 1, 0, 0, 0x0010 | 0x00000040)
                    if hIcon:
                        ctypes.windll.user32.SendMessageW(self.hwnd, WM_SETICON, 0, hIcon)
                        ctypes.windll.user32.SendMessageW(self.hwnd, WM_SETICON, 1, hIcon)

                GWL_EXSTYLE = -20

                WS_EX_TOOLWINDOW = 0x00000080

                WS_EX_APPWINDOW = 0x00040000

                SWP_NOMOVE = 0x0002

                SWP_NOSIZE = 0x0001

                SWP_NOZORDER = 0x0004

                SWP_FRAMECHANGED = 0x0020

                SWP_SHOWWINDOW = 0x0040

                if hasattr(self, '_GetWindowLong') and hasattr(self, '_SetWindowLong'):
                    exstyle = self._GetWindowLong(self.hwnd, GWL_EXSTYLE)
                    if exstyle is not None:
                        new_exstyle = (exstyle & ~WS_EX_TOOLWINDOW) | WS_EX_APPWINDOW
                        self._SetWindowLong(self.hwnd, GWL_EXSTYLE, new_exstyle)

                if self.config.get('CONF_VIEWER_ALWAYS_ON_TOP', True):
                    HWND_TOPMOST = -1
                    ctypes.windll.user32.SetWindowPos(self.hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_FRAMECHANGED | SWP_SHOWWINDOW)

                    def keep_on_top():
                        while getattr(self, 'running', True):
                            try:
                                if self.config.get('CONF_VIEWER_ALWAYS_ON_TOP', True):
                                    ctypes.windll.user32.SetWindowPos(self.hwnd, -1, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
                                else:
                                    ctypes.windll.user32.SetWindowPos(self.hwnd, -2, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
                            except BaseException:
                                pass
                            time.sleep(2)
                    threading.Thread(target=keep_on_top, daemon=True).start()
                else:
                    ctypes.windll.user32.SetWindowPos(self.hwnd, None, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED | SWP_SHOWWINDOW)

                SW_SHOW = 5
                ctypes.windll.user32.ShowWindow(self.hwnd, SW_SHOW)
                ctypes.windll.user32.SetForegroundWindow(self.hwnd)

                self._log("Applied extended styles and brought to foreground successfully.")

                def maintain_transparency():
                    while getattr(self, 'running', True):
                        try:
                            if getattr(self, '_current_alpha_byte', 255) < 255 and getattr(self, 'hwnd', None):
                                ctypes.windll.user32.SetLayeredWindowAttributes(self.hwnd, 0x00FF00FF, self._current_alpha_byte, 3)
                        except BaseException:
                            pass
                        time.sleep(5)
                threading.Thread(target=maintain_transparency, daemon=True).start()

            except Exception as e:
                _pre_log(f"Warning: HWND modification failed: {e}")

        font_name = self.config.get('CONF_FONT_NAME', 'consolas')
        try:
            font_size = int(float(self.config.get('CONF_FONT_SIZE', 13)))
        except (ValueError, TypeError):
            font_size = 13

        self.font = pygame.font.SysFont(font_name, font_size)
        self.font_bold = pygame.font.SysFont(font_name, font_size, bold=True)
        self.title_font = pygame.font.SysFont(font_name, 14, bold=False)
        self.close_font = pygame.font.SysFont(font_name, 18, bold=False)
        self.button_font = pygame.font.SysFont(font_name, 11, bold=False)

        self.tree_stat_font = pygame.font.SysFont(font_name, max(9, font_size - 2))
        self.line_height = self.font.get_linesize() + 4
        self.tree_row_height = 22

        self.focused = True
        self.left_panel_width = 150

        self.scroll_left = 0
        self.scroll_right = 0
        self.scroll_right_target = 0.0
        self.scroll_right_float = 0.0

        
        self.scroll_right_x = 0
        self.scroll_right_x_target = 0.0
        self.scroll_right_x_float = 4490.0
        self.max_right_width = 1
        self.is_dragging_scroll_x = True
        self._scroll_x_drag_offset = 0
        self.max_edit_width = 0
        self.is_dragging_editor_scroll_x = False
        self._editor_scroll_x_offset = 0

        self.hovered_history_idx = -1
        self.hovered_line_idx = None
        self.hovered_line_pane = None

        self.old_lines = []

        self.new_lines = []

        self.diff_blocks = []

        self.selection_start = None
        self.selection_end = None
        self.is_selecting = False
        self.selecting_pane = None
        self.is_dragging_minimap = False

        self.search_text = ""
        self.search_active = False

        self.search_results = []
        self.search_current_idx = -1
        self.is_folded = False

        self.visible_indices = []

        self.actual_to_visual = []
        self.search_rect = pygame.Rect(0,0,0,0)
        self.fold_rect = pygame.Rect(0,0,0,0)

        
        self.in_context_view = False
        self.scroll_context = 0

        self.substantial_changes = []

        
        self.is_editing = False

        self.edit_lines = []
        self.edit_cursor_row = 0
        self.edit_cursor_col = 0
        self.edit_scroll_y = 0
        self.edit_scroll_x = 0
        self.edit_selection_start = None
        self.edit_is_dragging = False

        self.edit_undo_stack = []

        self.edit_redo_stack = []

        if self.render_list:
            for item in self.render_list:
                if item['type'] == 'entry':
                    self._select_entry(item['data'])
                    break

        self._log("__init__ fully completed.")

    except BaseException as fatal_e:
        try:
            appdata = os.environ.get('APPDATA', '')
            if appdata:
                err_dir = os.path.join(appdata, "CodeStitcher")
                os.makedirs(err_dir, exist_ok=True)
            else:
                if getattr(sys, "frozen", False) or "__compiled__" in globals():
                    err_dir = os.path.dirname(os.path.abspath(sys.executable))
                else:
                    err_dir = os.path.dirname(os.path.abspath(__file__))

            log_path = os.path.join(err_dir, "stitch_viewer_debug.log")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] FATAL INIT CRASH: {fatal_e}\n{traceback.format_exc()}\n")
        except:
            pass
        raise

def _restricted_walk(self, directory: str):
    target_base = os.path.abspath(directory)

    for root, dirs, files in os.walk(directory):
        curr_path = os.path.abspath(root)

        
        dirs[:] = [d for d in dirs if d not in ('.git', '__pycache__', 'node_modules', 'venv', 'env', '.redo')]

        if not getattr(self, 'is_pro', False):
            
            if curr_path == target_base:
                
                dirs[:] = [d for d in dirs if d == "ep_backups"]
            elif curr_path == os.path.join(target_base, "ep_backups"):
                
                dirs[:] = []
            else:
                
                dirs[:] = []
        yield root, dirs, files

def _move_selection_to_current(self):
    """Copies custom selection range from historical pane directly to corresponding spot in current version."""
    self.context_menu = None
    pane = "old"
    selected_indices = set()
    for (r1, r2) in getattr(self, 'extra_selections', {}).get(pane, []):
        selected_indices.update(range(r1, r2 + 1))
    if getattr(self, 'selection_start', None) is not None and getattr(self, 'selection_end', None) is not None:
        r1 = min(self.selection_start, self.selection_end)
        r2 = max(self.selection_start, self.selection_end)
        selected_indices.update(range(r1, r2 + 1))

    if not selected_indices:
        return

    sorted_indices = sorted(list(selected_indices))

    old_lns = [self.old_lines[i][2] for i in sorted_indices if self.old_lines[i][2] is not None]
    if not old_lns: return
    old_min, old_max = min(old_lns), max(old_lns)

    new_lns = [self.new_lines[i][2] for i in sorted_indices if self.new_lines[i][2] is not None]

    bak_ref = getattr(self, 'current_entry', {}).get("backup_reference", "")
    if not bak_ref or not hasattr(self, 'active_file_path') or not self.active_file_path:
        return

    parent_dir = os.path.dirname(self.active_file_path)
    old_file_path = os.path.join(parent_dir, "ep_backups", bak_ref)

    if not os.path.exists(old_file_path) or not os.path.exists(self.active_file_path):
        return

    def _get_raw_lines(filepath):
        try:
            with open(filepath, 'rb') as f: raw = f.read()
            for enc in ('utf-8', 'utf-8-sig', 'utf-16', 'windows-1252', 'latin-1'):
                try:
                    text = raw.decode(enc)
                    text = text.replace('\r\n', '\n').replace('\r', '\n')
                    return text.splitlines()
                except: pass
            text = raw.decode('utf-8', errors='ignore')
            text = text.replace('\r\n', '\n').replace('\r', '\n')
            return text.splitlines()
        except: return []

    old_file_lines = _get_raw_lines(old_file_path)
    new_file_lines = _get_raw_lines(self.active_file_path)
    if not old_file_lines or not new_file_lines: return
    old_block_lines = old_file_lines[old_min - 1 : old_max]
    if new_lns:
        new_min, new_max = min(new_lns), max(new_lns)
        final_lines = new_file_lines[:new_min - 1] + old_block_lines + new_file_lines[new_max:]
    else:
        insert_idx = 0
        for i in range(sorted_indices[0] - 1, -1, -1):
            if self.new_lines[i][2] is not None:
                insert_idx = self.new_lines[i][2]
                break
        final_lines = new_file_lines[:insert_idx] + old_block_lines + new_file_lines[insert_idx:]

    try:
        with open(self.active_file_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write("\n".join(final_lines) + "\n")
        self._log("Moved selected code to current version.")
        self._select_entry(self.current_entry)
    except Exception as e:
        self._log(f"Failed to move selection: {e}")

def _copy_selection(self):
    self.context_menu = None
    pane = getattr(self, 'selecting_pane', None)
    if not pane: return

    lines = self.old_lines if pane == "old" else self.new_lines
    selected_indices = set()

    
    for (r1, r2) in getattr(self, 'extra_selections', {}).get(pane, []):
        selected_indices.update(range(r1, r2 + 1))

    
    if getattr(self, 'selection_start', None) is not None and getattr(self, 'selection_end', None) is not None:
        r1 = min(self.selection_start, self.selection_end)
        r2 = max(self.selection_start, self.selection_end)
        selected_indices.update(range(r1, r2 + 1))

    copied_text = []
    for i in sorted(list(selected_indices)):
        if 0 <= i < len(lines):
            text, status, ln = lines[i]
            if status not in ("blank_del", "blank_add", "header"):
                copied_text.append(text)

    if copied_text:
        try: pyperclip.copy("\n".join(copied_text))
        except: pass

def _render_syntax_line(self, text: str, base_color: tuple) -> pygame.Surface:

    if not hasattr(self, '_syntax_cache'):
        self._syntax_cache = {}

    cache_key = (text, base_color)
    if cache_key in self._syntax_cache:
        return self._syntax_cache[cache_key]

    text = text.replace('\t', '    ')
    total_width, h = self.font.size(text)
    if total_width == 0: total_width = 1
    surf = pygame.Surface((total_width, max(h, self.line_height)), pygame.SRCALPHA)

    
    C_KW = (204, 120, 50)      

    C_CLASS = (255, 170, 60)   

    C_STR = (106, 135, 89)     

    C_NUM = (104, 151, 187)    

    C_COM = (128, 128, 128)    

    C_BOOL = (86, 156, 214)    

    classes_kw = {'class', 'struct', 'interface', 'enum', 'namespace'}

    keywords = {
        'if', 'for', 'while', 'try', 'except', 'finally', 'with', 'def',
        'return', 'yield', 'import', 'from', 'as', 'pass', 'break', 'continue',
        'async', 'await', 'raise', 'global', 'nonlocal', 'del', 'in', 'is', 'and', 'or', 'not',
        'let', 'const', 'var', 'function', 'static', 'public', 'private', 'void', 'new', 'switch', 'case'
    }

    booleans = {'True', 'False', 'None', 'true', 'false', 'null', 'undefined'}
    x = 0
    comment_part = ""
    code_part = text

    
    if '#' in text and text.find('#') >= 0:
        in_str = False
        str_char = ''
        for i, char in enumerate(text):
            if char in "\"'":
                if not in_str:
                    in_str = True
                    str_char = char
                elif str_char == char:
                    in_str = False
            elif char == '#' and not in_str:
                code_part = text[:i]
                comment_part = text[i:]
                break

    if not comment_part and '//' in text:
        in_str = False
        str_char = ''
        for i in range(len(text)-1):
            char = text[i]
            if char in "\"'":
                if not in_str:
                    in_str = True
                    str_char = char
                elif str_char == char:
                    in_str = False
            elif text[i:i+2] == '//' and not in_str:
                code_part = text[:i]
                comment_part = text[i:]
                break

    
    tokens = re.split(r'(\s+|[().,\[\]{}:+\-*/=<>!]+|"[^"]*"|\'[^\']*\')', code_part)

    for token in tokens:
        if not token: continue

        color = base_color
        if token in classes_kw:
            color = C_CLASS
        elif token in keywords:
            color = C_KW
        elif token in booleans:
            color = C_BOOL
        elif token.isdigit():
            color = C_NUM
        elif token.startswith('"') or token.startswith("'"):
            color = C_STR

        t_surf = self.font.render(token, True, color)
        surf.blit(t_surf, (x, 0))
        x += self.font.size(token)[0]

    
    if comment_part:
        c_surf = self.font.render(comment_part, True, C_COM)
        surf.blit(c_surf, (x, 0))

    self._syntax_cache[cache_key] = surf
    return surf

def _execute_linter_syntax_check(self):
    """Executes the heavy compilation / stack matching syntax check asynchronously/debounced."""
    self.edit_linter_errors = []
    if not hasattr(self, 'active_file_path') or not self.active_file_path:
        return

    ext = os.path.splitext(self.active_file_path)[1].lower()
    
    clean_lines = self.edit_lines[:-4] if len(self.edit_lines) >= 4 else self.edit_lines
    code_text = "\n".join(clean_lines)

    if ext == '.py':
        try:
            compile(code_text, "<editor>", "exec")
        except SyntaxError as e:
            row = (e.lineno - 1) if e.lineno is not None else 0
            msg = e.msg or "Syntax Error"
            self.edit_linter_errors.append((row, msg))
    elif ext == '.json':
        try:
            json.loads(code_text)
        except ValueError as e:
            m = re.search(r'line (\d+)', str(e))

            row = (int(m.group(1)) - 1) if m else 0
            self.edit_linter_errors.append((row, str(e)))
    else:
        
        open_chars = {'(': ')', '{': '}', '[': ']'}

        stack = []
        for row_idx, line in enumerate(self.edit_lines):
            for col_idx, char in enumerate(line):
                if char in open_chars:
                    stack.append((char, row_idx))
                elif char in open_chars.values():
                    if not stack:
                        self.edit_linter_errors.append((row_idx, f"Mismatched closing bracket '{char}'"))
                        break
                    last_open, last_row = stack.pop()
                    if open_chars[last_open] != char:
                        self.edit_linter_errors.append((row_idx, f"Mismatched bracket: expected '{open_chars[last_open]}', got '{char}'"))
                        break
            if len(self.edit_linter_errors) > 0:
                break
        if stack and not self.edit_linter_errors:
            char, r = stack[-1]
            self.edit_linter_errors.append((r, f"Unclosed bracket '{char}'"))

def _shift_editor_folds(self, start_row, delta):
    """Adjusts editor folded block indices when lines are added or removed."""
    if not hasattr(self, 'edit_folded_blocks'):
        self.edit_folded_blocks = set()
    new_folds = set()
    for r in self.edit_folded_blocks:
        if r >= start_row:
            new_val = r + delta
            if new_val >= 0:
                new_folds.add(new_val)
        else:
            new_folds.add(r)
    self.edit_folded_blocks = new_folds

def _copy_for_llm_selection(self):
    if self.selection_start is None or self.selection_end is None or not self.selecting_pane:
        self.context_menu = None
        return

    r1 = min(self.selection_start, self.selection_end)
    r2 = max(self.selection_start, self.selection_end)

    lines = self.old_lines if self.selecting_pane == "old" else self.new_lines

    copied_text = []
    start_ln = None
    end_ln = None

    for i in range(r1, r2 + 1):
        if 0 <= i < len(lines):
            text, status, ln = lines[i]
            if status not in ("blank_del", "blank_add", "header"):
                copied_text.append(text)
                if ln is not None:
                    if start_ln is None: start_ln = ln
                    end_ln = ln

    if copied_text:
        fname = os.path.basename(getattr(self, 'active_file_path', ''))
        if not fname: fname = "snippet"
        ext = fname.split('.')[-1] if '.' in fname else 'text'
        ln_str = f" (Lines {start_ln}-{end_ln})" if start_ln and end_ln else ""
        header = f"In `{fname}`{ln_str}:\n```{ext}\n"
        footer = "\n```"

        try:
            pyperclip.copy(header + "\n".join(copied_text) + footer)
        except: pass
    self.context_menu = None

def _show_modal_confirm(self, title: str, message_lines: list) -> bool:
    """Draws a custom, blocking modal dialog over the Pygame UI."""

    
    bg_surface = self.screen.copy()
    dim_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
    dim_surface.fill((0, 0, 0, 180)) 
    bg_surface.blit(dim_surface, (0, 0))

    
    box_w = 480
    box_h = 160 + (len(message_lines) * 20)

    box_x = (self.width - box_w) // 2

    box_y = (self.height - box_h) // 2
    box_rect = pygame.Rect(box_x, box_y, box_w, box_h)

    btn_w = 140
    btn_h = 30
    btn_yes = pygame.Rect(box_x + box_w - (btn_w * 2) - 20, box_y + box_h - 45, btn_w, btn_h)
    btn_no = pygame.Rect(box_x + box_w - btn_w - 10, box_y + box_h - 45, btn_w, btn_h)

    clock = pygame.time.Clock()

    
    while True:
        mx, my = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_RETURN:
                    return True
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_yes.collidepoint(mx, my):
                    return True
                elif btn_no.collidepoint(mx, my):
                    return False

        
        self.screen.blit(bg_surface, (0, 0))

        
        pygame.draw.rect(self.screen, (35, 35, 40), box_rect, border_radius=6)
        pygame.draw.rect(self.screen, (100, 100, 110), box_rect, 1, border_radius=6)

        
        title_surf = self.font_bold.render(title, True, (240, 80, 80)) 
        self.screen.blit(title_surf, (box_x + 20, box_y + 20))
        pygame.draw.line(self.screen, (80, 80, 90), (box_x + 20, box_y + 45), (box_x + box_w - 20, box_y + 45))

        
        for i, line in enumerate(message_lines):
            txt_surf = self.font.render(line, True, (200, 200, 200))
            self.screen.blit(txt_surf, (box_x + 20, box_y + 60 + (i * 20)))

        
        hover_yes = btn_yes.collidepoint(mx, my)
        pygame.draw.rect(self.screen, (160, 60, 60) if hover_yes else (120, 50, 50), btn_yes, border_radius=4)
        yes_text = self.font_bold.render("Yes, Overwrite", True, (255, 255, 255))
        self.screen.blit(yes_text, (btn_yes.centerx - yes_text.get_width()//2, btn_yes.centery - yes_text.get_height()//2))

        
        hover_no = btn_no.collidepoint(mx, my)
        pygame.draw.rect(self.screen, (80, 80, 90) if hover_no else (60, 60, 65), btn_no, border_radius=4)
        no_text = self.font.render("Cancel", True, (220, 220, 220))
        self.screen.blit(no_text, (btn_no.centerx - no_text.get_width()//2, btn_no.centery - no_text.get_height()//2))

        pygame.display.flip()
        clock.tick(60)

def _activate_search(self):
    self.search_active = True
    self.context_menu = None
    self.search_sel_start = 0
    self.search_sel_end = len(self.search_text)
    self.search_cursor_pos = len(self.search_text)

def _edit_fold_unchanged_blocks(self):
    self.edit_folded_blocks.clear()

    old_clean = [l[0] for l in self.old_lines if l[1] != 'blank_del']
    sm = difflib.SequenceMatcher(None, old_clean, self.edit_lines)
    changed_lines = set()
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != 'equal':
            changed_lines.update(range(j1, j2))

    for start_i, end_i in getattr(self, 'edit_code_blocks', {}).items():
        block_lines = set(range(start_i, end_i + 1))
        if not block_lines.intersection(changed_lines):
            self.edit_folded_blocks.add(start_i)

    if not self.edit_folded_blocks:
        self.edit_folded_blocks = set(getattr(self, 'edit_code_blocks', {}).keys())

def _handle_mouse_button_down_event(self, event):
    mx, my = event.pos
    pane = self._get_pane_for_x(mx)
    is_pressed = pygame.mouse.get_pressed()[0]

    if getattr(self, 'show_commands_help', False):
        if getattr(self, 'help_close_rect', pygame.Rect(0,0,0,0)).collidepoint(mx, my):
            self.show_commands_help = False
            return

    cm = getattr(self, 'context_menu', None)
    if cm:
        if cm['rect'].collidepoint(mx, my):
            if event.button == 1:
                for opt in cm['options']:
                    if opt.get('rect') and opt['rect'].collidepoint(mx, my):
                        if opt.get('action'): opt['action']()
                        break
            return
        else:
            self.context_menu = None

    
    if my < self.title_bar_height and event.button == 1:
        if mx > self.width - 40:
            self.running = False
        elif mx > self.width - 80:
            if getattr(self, 'hwnd', None):
                ctypes.windll.user32.ShowWindow(self.hwnd, 6)
        else:
            self._is_dragging = True
            if os.name == 'nt' and getattr(self, 'hwnd', None):
                pt = wintypes.POINT()
                ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
                rect = wintypes.RECT()
                ctypes.windll.user32.GetWindowRect(self.hwnd, ctypes.byref(rect))
                self._drag_offset_x = pt.x - rect.left
                self._drag_offset_y = pt.y - rect.top
        return

    
    if not getattr(self, 'is_editing', False) and not getattr(self, 'in_context_view', False):
        right_w = max(1, self.width - self.left_panel_width - self.minimap_width)
        pane_w = max(1, (right_w - self.GAP_WIDTH) // 2)
        pane_old_x = self.left_panel_width
        pane_new_x = pane_old_x + pane_w + self.GAP_WIDTH
        visible_w = pane_w - 65
        max_scroll_x = max(0, getattr(self, 'max_right_width', 0) - visible_w + 50)
        if max_scroll_x > 0:
            scrollbar_h = 12
            scrollbar_rect = pygame.Rect(pane_new_x + 60, self.height - scrollbar_h - 5, pane_w - 65, scrollbar_h)
            ratio = visible_w / max(1, getattr(self, 'max_right_width', 0))
            thumb_w = min(50, max(15, int(scrollbar_rect.width * ratio)))
            max_thumb_travel = scrollbar_rect.width - thumb_w
            thumb_x = scrollbar_rect.x + int((self.scroll_right_x / max_scroll_x) * max_thumb_travel)
            thumb_rect = pygame.Rect(thumb_x, scrollbar_rect.y, thumb_w, scrollbar_h)

            if scrollbar_rect.collidepoint(mx, my):
                if thumb_rect.collidepoint(mx, my):
                    self.is_dragging_scroll_x = True
                    self._scroll_x_drag_offset = mx - thumb_x
                else:
                    click_ratio = (mx - scrollbar_rect.x - thumb_w / 2) / max(1, max_thumb_travel)
                    self.scroll_right_x = max(0, min(max_scroll_x, int(click_ratio * max_scroll_x)))
                    self.scroll_right_x_target = float(self.scroll_right_x)
                    self.scroll_right_x_float = float(self.scroll_right_x)
                return

    
    if event.button == 1 and pane == "minimap" and my > (self.title_bar_height + 25):
        diff_y_start = self.title_bar_height + 25
        map_h = self.height - diff_y_start
        is_ed = getattr(self, 'is_editing', False) or getattr(self, 'edit_anim_t', 0.0) > 0.0
        if is_ed:
            total_lines = len(getattr(self, 'edit_visible_indices', []))
            scroll_val = getattr(self, 'edit_scroll_y_float', float(self.edit_scroll_y))

            max_lines = (self.height - diff_y_start - 5) // self.line_height
        else:
            total_lines = len(getattr(self, 'visible_indices', getattr(self, 'old_lines', [])))
            scroll_val = getattr(self, 'scroll_right_float', float(self.scroll_right))
            max_lines = map_h // self.line_height

        scale_y = map_h / total_lines if total_lines > 0 else 0
        vp_y = diff_y_start + (scroll_val * scale_y)
        vp_h = max(10, max_lines * scale_y)

        if vp_y <= my <= vp_y + vp_h:
            self._minimap_drag_offset = my - vp_y
        else:
            self._minimap_drag_offset = None

        self.is_dragging_minimap = True
        self._scroll_to_minimap(my)
        return

    
    if event.button == 3:
        if pane == "left" and (self.title_bar_height + 25) < my < self.height - 25:
            idx = self.scroll_left + ((my - (self.title_bar_height + 25)) // self.tree_row_height)
            if 0 <= idx < len(self.render_list):
                item = self.render_list[idx]

                
                if item['type'] == 'file':
                    full_path = self.tree_data[item['name']]['full_path']

                    entry = {
                        'file': item['name'],
                        'full_path': full_path,
                        'backup_reference': "",
                        'is_unversioned': True
                    }

                    options = [
                        {"label": "Copy Entire File", "action": lambda e=entry: self._copy_version_to_clipboard(e)},
                        {"label": "Attach to compose window", "action": lambda e=entry: self._attach_to_compose(e)}
                    ]
                    w, h = 210, len(options) * 22
                    draw_x = mx if mx + w < self.width else self.width - w
                    draw_y = my if my + h < self.height else self.height - h

                    self.context_menu = {'rect': pygame.Rect(draw_x, draw_y, w, h), 'options': []}
                    for i_opt, opt in enumerate(options):
                        opt_rect = pygame.Rect(draw_x, draw_y + (i_opt * 22), w, 22)
                        self.context_menu['options'].append({'label': opt['label'], 'action': opt['action'], 'rect': opt_rect})
                    return

                elif item['type'] == 'entry':
                    if getattr(self, 'is_editing', False):
                        self.edit_save_btn_flash = 1.0
                        self.edit_show_discard_btn = True
                        return

                    options = []
                    if not item['data'].get('is_unversioned', False):
                        options.append({"label": "Revert Entire File", "action": lambda e=item['data']: self._revert_version(e)})

                    options.append({"label": "Copy Entire File", "action": lambda e=item['data']: self._copy_version_to_clipboard(e)})
                    options.append({"label": "Attach to compose window", "action": lambda e=item['data']: self._attach_to_compose(e)})

                    w, h = 210, len(options) * 22
                    draw_x = mx if mx + w < self.width else self.width - w
                    draw_y = my if my + h < self.height else self.height - h

                    self.context_menu = {'rect': pygame.Rect(draw_x, draw_y, w, h), 'options': []}
                    for i_opt, opt in enumerate(options):
                        opt_rect = pygame.Rect(draw_x, draw_y + (i_opt * 22), w, 22)
                        self.context_menu['options'].append({'label': opt['label'], 'action': opt['action'], 'rect': opt_rect})
                    return

        
        is_right_col = False
        if my > (self.title_bar_height + 25):
            if getattr(self, 'is_editing', False):
                right_w = max(1, self.width - self.left_panel_width - self.minimap_width)
                pane_w = max(1, (right_w - self.GAP_WIDTH) // 2)
                editor_x = self.left_panel_width + 35
                if editor_x <= mx < (self.width - self.minimap_width - 20):
                    is_right_col = True
            else:
                if pane == "new":
                    is_right_col = True

        if is_right_col:
            full_path = getattr(self, 'active_file_path', '')

            entry = {
                'file': os.path.basename(full_path) if full_path else '',
                'full_path': full_path,
                'backup_reference': "",
                'is_unversioned': True
            }
            
            options = [
                {
                    "label": "Copy Entire File",
                    "action": lambda e=entry: (
                        open(e['full_path'], 'w', encoding='utf-8', newline='\n').write("\n".join(self.edit_lines) + "\n")
                        if (getattr(self, 'is_editing', False) and e.get('full_path')) else None,
                        self._copy_version_to_clipboard(e)
                    )
                },
                {
                    "label": "Attach to compose window",
                    "action": lambda e=entry: (
                        open(e['full_path'], 'w', encoding='utf-8', newline='\n').write("\n".join(self.edit_lines) + "\n")
                        if (getattr(self, 'is_editing', False) and e.get('full_path')) else None,
                        self._attach_to_compose(e)
                    )
                }
            ]

            
            if getattr(self, 'is_editing', False):
                
                scroll_y_float = getattr(self, 'edit_scroll_y_float', float(self.edit_scroll_y))
                start_v_idx = int(scroll_y_float)

                fractional_offset = (scroll_y_float - start_v_idx) * self.line_height
                click_v_idx = start_v_idx + int((my - (self.title_bar_height + 25) + fractional_offset) // self.line_height)

                clicked_block = None
                if 0 <= click_v_idx < len(self.edit_visible_indices):
                    actual_row = self.edit_visible_indices[click_v_idx]

                    
                    best_len = float('inf')
                    for b_start, b_end in getattr(self, 'edit_code_blocks', {}).items():
                        if b_start <= actual_row <= b_end:
                            if (b_end - b_start) < best_len:
                                best_len = b_end - b_start

                                clicked_block = (b_start, b_end)

                if clicked_block is not None:
                    options.insert(0, {"label": "Copy Function", "action": lambda b=clicked_block: self._copy_editor_function(b)})

                sel = self._get_editor_selection_range()
                if sel and sel[0] != sel[1]:
                    options.insert(0, {"label": "Copy Selection", "action": self._copy_editor_selection})
                    options.insert(1, {"label": "Search Selection", "action": self._search_editor_selection})
                    options.insert(2, {"label": "Replace...", "action": self._activate_replace})
                else:
                    options.insert(0, {"label": "Replace...", "action": self._activate_replace})

            if not getattr(self, 'is_editing', False):
                diff_y_start = self.title_bar_height + 25
                scroll_r_float = getattr(self, 'scroll_right_float', float(self.scroll_right))
                start_v_idx = int(scroll_r_float)

                fractional_offset = (scroll_r_float - start_v_idx) * self.line_height
                v_idx = start_v_idx + int((my - diff_y_start + fractional_offset) // self.line_height)

                clicked_block = None
                touched_blocks = set()

                if v_idx < len(self.visible_indices):
                    i = self.visible_indices[v_idx]
                    has_sel = False
                    if getattr(self, 'selecting_pane', None) == "new":
                        if getattr(self, 'selection_start', None) is not None and getattr(self, 'selection_end', None) is not None:
                            if self.selection_start != self.selection_end:
                                has_sel = True
                    if getattr(self, 'extra_selections', {}).get("new", []):
                        has_sel = True

                    selected_lines = set()
                    if has_sel:
                        for (r1, r2) in getattr(self, 'extra_selections', {}).get("new", []):
                            selected_lines.update(range(r1, r2 + 1))
                        if getattr(self, 'selecting_pane', None) == "new" and getattr(self, 'selection_start', None) is not None and getattr(self, 'selection_end', None) is not None:
                            r1 = min(self.selection_start, self.selection_end)
                            r2 = max(self.selection_start, self.selection_end)
                            selected_lines.update(range(r1, r2 + 1))
                    else:
                        selected_lines.add(i)

                    for sl in selected_lines:
                        best_len = float('inf')
                        best_block = None
                        for b_start, b_end in getattr(self, 'code_blocks', {}).items():
                            if b_start <= sl <= b_end:
                                if (b_end - b_start) < best_len:
                                    best_len = b_end - b_start

                                    best_block = (b_start, b_end)
                        if best_block:
                            touched_blocks.add(best_block)

                if touched_blocks:
                    blks = list(touched_blocks)
                    options.append({"label": "Copy Function(s)", "action": lambda bs=blks, p="new": self._copy_multiple_code_blocks(bs, p)})

                if has_sel:
                    options.append({"label": "Copy Selection", "action": self._copy_selection})

                options.extend([
                    {"label": "Go To Line...", "action": self._prompt_goto_line},
                    {"label": "Search...", "action": self._activate_search}
                ])

            w, h = 210, len(options) * 22
            draw_x = mx if mx + w < self.width else self.width - w
            draw_y = my if my + h < self.height else self.height - h

            self.context_menu = {'rect': pygame.Rect(draw_x, draw_y, w, h), 'options': []}
            for idx_opt, opt in enumerate(options):
                opt_rect = pygame.Rect(draw_x, draw_y + (idx_opt * 22), w, 22)
                self.context_menu['options'].append({'label': opt['label'], 'action': opt['action'], 'rect': opt_rect})
            return

        
        if pane == "old" and my > (self.title_bar_height + 25):
            options = []
            diff_y_start = self.title_bar_height + 25
            scroll_r_float = getattr(self, 'scroll_right_float', float(self.scroll_right))
            start_v_idx = int(scroll_r_float)

            fractional_offset = (scroll_r_float - start_v_idx) * self.line_height
            v_idx = start_v_idx + int((my - diff_y_start + fractional_offset) // self.line_height)

            clicked_block = None
            touched_blocks = set()

            if v_idx < len(self.visible_indices):
                i = self.visible_indices[v_idx]

                has_sel = False
                if getattr(self, 'selecting_pane', None) == "old":
                    if getattr(self, 'selection_start', None) is not None and getattr(self, 'selection_end', None) is not None:
                        if self.selection_start != self.selection_end:
                            has_sel = True
                if getattr(self, 'extra_selections', {}).get("old", []):
                    has_sel = True

                selected_lines = set()
                if has_sel:
                    for (r1, r2) in getattr(self, 'extra_selections', {}).get("old", []):
                        selected_lines.update(range(r1, r2 + 1))
                    if getattr(self, 'selecting_pane', None) == "old" and getattr(self, 'selection_start', None) is not None and getattr(self, 'selection_end', None) is not None:
                        r1 = min(self.selection_start, self.selection_end)
                        r2 = max(self.selection_start, self.selection_end)
                        selected_lines.update(range(r1, r2 + 1))
                else:
                    selected_lines.add(i)

                for sl in selected_lines:
                    best_len = float('inf')
                    best_block = None
                    for b_start, b_end in getattr(self, 'code_blocks', {}).items():
                        if b_start <= sl <= b_end:
                            if (b_end - b_start) < best_len:
                                best_len = b_end - b_start

                                best_block = (b_start, b_end)
                    if best_block:
                        touched_blocks.add(best_block)

            if touched_blocks:
                blks = list(touched_blocks)
                options.append({"label": "Copy Function(s)", "action": lambda bs=blks, p="old": self._copy_multiple_code_blocks(bs, p)})
                options.append({"label": "Function to Current Version", "action": lambda bs=blks: self._replace_multiple_functions(bs)})

            if has_sel:
                options.append({"label": "Selection to Current Version", "action": self._move_selection_to_current})
                options.append({"label": "Copy Selection", "action": self._copy_selection})

            options.extend([
                {"label": "Go To Line...", "action": self._prompt_goto_line},
                {"label": "Search...", "action": self._activate_search}
            ])

            w, h = 250, len(options) * 22
            draw_x = mx if mx + w < self.width else self.width - w
            draw_y = my if my + h < self.height else self.height - h

            self.context_menu = {'rect': pygame.Rect(draw_x, draw_y, w, h), 'options': []}
            for idx_opt, opt in enumerate(options):
                opt_rect = pygame.Rect(draw_x, draw_y + (idx_opt * 22), w, 22)
                self.context_menu['options'].append({'label': opt['label'], 'action': opt['action'], 'rect': opt_rect})
            return

    if getattr(self, 'is_editing', False):
        if getattr(self, 'edit_search_summary_active', False):
            if getattr(self, 'edit_search_summary_rect', pygame.Rect(0,0,0,0)).collidepoint(mx, my):
                sh = min(300, 45 + len(self.edit_search_summary_results) * 25)

                max_visible = (sh - 45) // 25
                if event.button == 4:
                    self.edit_search_summary_scroll = max(0, getattr(self, 'edit_search_summary_scroll', 0) - 1)
                    return
                elif event.button == 5:
                    max_s = max(0, len(self.edit_search_summary_results) - max_visible)
                    self.edit_search_summary_scroll = max(0, min(max_s, getattr(self, 'edit_search_summary_scroll', 0) + 1))
                    return
                elif event.button == 1:
                    sy = self.edit_search_summary_rect.y + 40
                    scroll = getattr(self, 'edit_search_summary_scroll', 0)
                    for i, (row_idx, _) in enumerate(self.edit_search_summary_results[scroll:scroll+max_visible]):
                        item_rect = pygame.Rect(self.edit_search_summary_rect.x + 5, sy + i*25, self.edit_search_summary_rect.width - 10, 25)
                        if item_rect.collidepoint(mx, my):
                            self.edit_cursor_row = row_idx
                            self.edit_cursor_col = 0
                            self.edit_selection_start = None  

                            unfolded = False
                            for start_i, end_i in getattr(self, 'edit_code_blocks', {}).items():
                                if start_i <= row_idx <= end_i:
                                    if start_i in getattr(self, 'edit_folded_blocks', set()):
                                        self.edit_folded_blocks.remove(start_i)
                                        unfolded = True

                            if unfolded or not getattr(self, 'edit_visible_indices', []):
                                self._build_edit_visible_indices()

                            
                            diff_y_start = self.title_bar_height + 25

                            max_lines = (self.height - diff_y_start - 30) // self.line_height
                            v_idx = self.edit_actual_to_visual[row_idx] if row_idx < len(self.edit_actual_to_visual) else -1
                            if v_idx != -1:
                                self.edit_target_scroll_y = float(max(0, min(len(self.edit_visible_indices) - max_lines, v_idx - (max_lines // 2))))
                            self._scroll_editor_to_cursor()
                            return
                return
            else:
                if event.button == 1:
                    self.edit_search_summary_active = False

        elif getattr(self, 'edit_search_summary_results', []) and getattr(self, 'edit_search_btn_rect', pygame.Rect(0,0,0,0)).collidepoint(mx, my):
            if event.button == 1:
                self.edit_search_summary_active = True
                return

        
        if self.title_bar_height < my < (self.title_bar_height + 25) and event.button == 1:
            if getattr(self, 'edit_btn_rect', pygame.Rect(0,0,0,0)).collidepoint(mx, my):
                self._exit_edit_mode()
                return
            elif getattr(self, 'discard_btn_rect', pygame.Rect(0,0,0,0)).collidepoint(mx, my):
                self._exit_edit_mode_discard()
                return
            elif getattr(self, 'help_btn_rect', pygame.Rect(0,0,0,0)).collidepoint(mx, my):
                self.show_commands_help = not getattr(self, 'show_commands_help', False)
                return
            elif getattr(self, 'search_rect', pygame.Rect(0,0,0,0)).collidepoint(mx, my):
                self.search_active = True
                self.search_sel_start = 0
                self.search_sel_end = len(self.search_text)
                self.search_cursor_pos = len(self.search_text)
                return
            elif getattr(self, 'fold_in_rect', pygame.Rect(0,0,0,0)).collidepoint(mx, my):
                self._adjust_fold_level(-1)
                return
            elif getattr(self, 'fold_out_rect', pygame.Rect(0,0,0,0)).collidepoint(mx, my):
                self._adjust_fold_level(1)
                return

        if event.button == 1:
            
            if self._handle_editor_mouse(event, down=True):
                return
            self.search_active = False 
            self.edit_is_dragging = True
            self._handle_editor_mouse(event, down=True)
        elif event.button in (4, 5):
            target_y = getattr(self, 'edit_target_scroll_y', self.edit_scroll_y)
            self.edit_target_scroll_y = max(0, min(len(self.edit_visible_indices) - 1, target_y + (6 if event.button == 5 else -6)))
        return

    if getattr(self, 'in_context_view', False) and pane in ("old", "new", "gap") and my > (self.title_bar_height + 25):
        if event.button == 1:
            for card in getattr(self, 'context_cards', []):
                if card['rect'].collidepoint(mx, my):
                    self.in_context_view = False
                    actual_start = card['target']

                    
                    if hasattr(self, 'code_blocks'):
                        unfolded_anything = False
                        for start_i, end_i in self.code_blocks.items():
                            if start_i <= actual_start <= end_i:
                                if start_i in getattr(self, 'folded_blocks', set()):
                                    self.folded_blocks.remove(start_i)
                                    unfolded_anything = True
                        if unfolded_anything:
                            self._build_visible_indices()

                    if actual_start < len(self.actual_to_visual):
                        target_v = self.actual_to_visual[actual_start]
                        if target_v != -1:
                            diff_y_start = self.title_bar_height + 25

                            max_lines = (self.height - diff_y_start) // self.line_height
                            max_scroll = max(0, len(self.visible_indices) - max_lines)

                            new_target = float(max(0, min(max_scroll, target_v - 3)))
                            self.scroll_right_target = new_target
                            self.scroll_right_float = new_target
                            self.scroll_right = int(new_target)

                            
                            self.selection_start = self.visible_indices[target_v]
                            self.selection_end = self.selection_start
                            self.selecting_pane = "new"  

                    return

    if self.title_bar_height < my < (self.title_bar_height + 25) and event.button == 1:
        if getattr(self, 'edit_btn_rect', pygame.Rect(0,0,0,0)).collidepoint(mx, my):
            if not getattr(self, 'is_editing', False):
                self._enter_edit_mode()
            return
        elif getattr(self, 'help_btn_rect', pygame.Rect(0,0,0,0)).collidepoint(mx, my):
            self.show_commands_help = not getattr(self, 'show_commands_help', False)
            return
        elif getattr(self, 'tree_fold_rect', pygame.Rect(0,0,0,0)).collidepoint(mx, my):
            current_file = getattr(self, 'active_tree_file', None)
            if not current_file and hasattr(self, 'current_entry') and self.current_entry:
                current_file = self.current_entry.get("file")

            active_fully_expanded = False
            if current_file and current_file in getattr(self, 'tree_data', {}):
                fdata = self.tree_data[current_file]
                if fdata['expanded'] and all(r['expanded'] for r in fdata['runs'].values()):
                    active_fully_expanded = True

            if active_fully_expanded:
                for fname, fdata in getattr(self, 'tree_data', {}).items():
                    fdata['expanded'] = False
                    for run in fdata['runs'].values():
                        run['expanded'] = False
            else:
                for fname, fdata in getattr(self, 'tree_data', {}).items():
                    if current_file and fname == current_file:
                        fdata['expanded'] = True
                        for run in fdata['runs'].values():
                            run['expanded'] = True
                    else:
                        fdata['expanded'] = False
                        for run in fdata['runs'].values():
                            run['expanded'] = False

            self._rebuild_render_list()

            if not active_fully_expanded and current_file:
                for idx, item in enumerate(self.render_list):
                    if item['type'] == 'file' and item['name'] == current_file:
                        self.scroll_left = max(0, idx - 1)
                        break

        elif getattr(self, 'refresh_rect', pygame.Rect(0,0,0,0)).collidepoint(mx, my):
            self._load_history()

        elif self.search_rect.collidepoint(mx, my):
            self.search_active = True
            self.search_sel_start = 0
            self.search_sel_end = len(self.search_text)
            self.search_cursor_pos = len(self.search_text)
        else:
            self.search_active = False
            if getattr(self, 'fold_in_rect', pygame.Rect(0,0,0,0)).collidepoint(mx, my):
                self._adjust_fold_level(-1)
            elif getattr(self, 'fold_out_rect', pygame.Rect(0,0,0,0)).collidepoint(mx, my):
                self._adjust_fold_level(1)
            elif getattr(self, 'context_rect', pygame.Rect(0,0,0,0)).collidepoint(mx, my):
                self.in_context_view = not getattr(self, 'in_context_view', False)
                if self.in_context_view:
                    self.scroll_context = 0
    else:
        self.search_active = False

    if event.button == 1 and my > (self.title_bar_height + 25):
        b_idx, sc_idx, action = self._get_hovered_gap_button(mx, my)
        if b_idx is not None:
            self._apply_diff_block(b_idx, sc_idx, action)
            return

        if pane == "left":
            if my < self.height - 25:
                idx = self.scroll_left + ((my - (self.title_bar_height + 25)) // self.tree_row_height)
                if 0 <= idx < len(self.render_list):
                    item = self.render_list[idx]
                    if item['type'] == 'file':
                        self.active_tree_file = item['name']
                        self.tree_data[item['name']]['expanded'] = not self.tree_data[item['name']]['expanded']
                        self._rebuild_render_list()
                    elif item['type'] == 'run':
                        self.active_tree_file = item['file']
                        self.tree_data[item['file']]['runs'][item['name']]['expanded'] = not self.tree_data[item['file']]['runs'][item['name']]['expanded']
                        self._rebuild_render_list()
                    elif item['type'] == 'entry':
                        if getattr(self, 'is_editing', False):
                            self.edit_save_btn_flash = 1.0
                            self.edit_show_discard_btn = True
                            return
                        self._select_entry(item['data'])

        elif pane in ("old", "new"):
            diff_y_start = self.title_bar_height + 25
            scroll_r_float = getattr(self, 'scroll_right_float', float(self.scroll_right))
            start_v_idx = int(scroll_r_float)

            fractional_offset = (scroll_r_float - start_v_idx) * self.line_height
            v_idx = start_v_idx + int((my - diff_y_start + fractional_offset) // self.line_height)

            if v_idx < len(self.visible_indices):
                i = self.visible_indices[v_idx]
                if i in getattr(self, 'code_blocks', {}):
                    clicked_fold = False
                    depth = getattr(self, 'block_depths', {}).get(i, 0)
                    if pane == "old":
                        if self.left_panel_width + 35 + (depth * 10) <= mx <= self.left_panel_width + 60 + (depth * 10):
                            clicked_fold = True
                    elif pane == "new":
                        right_w = max(1, self.width - self.left_panel_width - self.minimap_width)
                        pane_w = max(1, (right_w - self.GAP_WIDTH) // 2)
                        pane_new_x = self.left_panel_width + pane_w + self.GAP_WIDTH
                        if pane_new_x + 35 + (depth * 10) <= mx <= pane_new_x + 60 + (depth * 10):
                            clicked_fold = True

                    if clicked_fold:
                        offset = v_idx - scroll_r_float

                        if i in self.folded_blocks:
                            self.folded_blocks.remove(i)
                        else:
                            self.folded_blocks.add(i)
                            
                            end_idx = getattr(self, 'code_blocks', {}).get(i, i)
                            if getattr(self, 'selection_start', -1) is not None:
                                if i < self.selection_start <= end_idx:
                                    self.selection_start = i
                                    self.selection_end = i

                        self._build_visible_indices()
                        self._update_search()

                        new_v_idx = self.actual_to_visual[i]
                        if new_v_idx != -1:
                            max_r = max(0, len(self.visible_indices) - ((self.height - (self.title_bar_height + 25)) // self.line_height))
                            self.scroll_right_target = min(float(max_r), max(0.0, float(new_v_idx) - offset))
                            self.scroll_right_float = self.scroll_right_target
                            self.scroll_right = int(self.scroll_right_target)

                        return

            self._mouse_down_origin = event.pos
            if v_idx < len(self.visible_indices):
                mods = pygame.key.get_mods()

                if mods & pygame.KMOD_CTRL:
                    if not hasattr(self, 'extra_selections'):
                        self.extra_selections = {'old': [], 'new': []}

                    if getattr(self, 'selection_start', None) is not None and getattr(self, 'selection_end', None) is not None:
                        curr_pane = getattr(self, 'selecting_pane', pane)
                        if curr_pane:
                            r1 = min(self.selection_start, self.selection_end)
                            r2 = max(self.selection_start, self.selection_end)
                            self.extra_selections[curr_pane].append((r1, r2))

                    self.selection_start = self.visible_indices[v_idx]
                    self.selection_end = self.selection_start
                    self.selecting_pane = pane

                elif mods & pygame.KMOD_SHIFT and getattr(self, 'selection_start', None) is not None:
                    self.selection_end = self.visible_indices[v_idx]

                else:
                    self.extra_selections = {'old': [], 'new': []}
                    self.selection_start = self.visible_indices[v_idx]
                    self.selection_end = self.selection_start
                    self.selecting_pane = pane

def _process_text_input_event(self, event, text, cursor, sel_start, sel_end):
    """Modular text input logic for isolating all input box fields away from the editor."""
    mods = pygame.key.get_mods()
    ctrl = mods & pygame.KMOD_CTRL
    shift = mods & pygame.KMOD_SHIFT

    is_paste = (event.key == pygame.K_v and ctrl) or (event.key == pygame.K_INSERT and shift)

    is_copy = (event.key == pygame.K_c and ctrl) or (event.key == pygame.K_INSERT and ctrl)

    is_cut = (event.key == pygame.K_x and ctrl) or (event.key == pygame.K_DELETE and shift)

    is_select_all = (event.key == pygame.K_a and ctrl)
    s = min(sel_start, sel_end)
    e = max(sel_start, sel_end)

    if is_paste:
        if s != e:
            text = text[:s] + text[e:]
            cursor = s
        try:
            pt = pyperclip.paste() or ""
            pt = pt.replace('\n', ' ').replace('\r', '')
            text = text[:cursor] + pt + text[cursor:]
            cursor += len(pt)
            sel_start = sel_end = cursor
        except: pass
        return text, cursor, sel_start, sel_end, True

    elif is_copy or is_cut:
        to_copy = text[s:e] if s != e else text
        if to_copy:
            try: pyperclip.copy(to_copy)
            except: pass
        if is_cut:
            if s != e:
                text = text[:s] + text[e:]
                cursor = s
            else:
                text = ""
                cursor = 0
            sel_start = sel_end = cursor
        return text, cursor, sel_start, sel_end, True

    elif is_select_all:
        return text, len(text), 0, len(text), True

    elif event.key == pygame.K_BACKSPACE:
        if s != e:
            text = text[:s] + text[e:]
            cursor = s
        elif cursor > 0:
            text = text[:cursor-1] + text[cursor:]
            cursor -= 1
        sel_start = sel_end = cursor
        return text, cursor, sel_start, sel_end, True

    elif event.key == pygame.K_DELETE:
        if s != e:
            text = text[:s] + text[e:]
            cursor = s
        elif cursor < len(text):
            text = text[:cursor] + text[cursor+1:]
        sel_start = sel_end = cursor
        return text, cursor, sel_start, sel_end, True

    elif event.key == pygame.K_LEFT:
        cursor = max(0, cursor - 1)
        if shift: sel_end = cursor
        else: sel_start = sel_end = cursor
        return text, cursor, sel_start, sel_end, True

    elif event.key == pygame.K_RIGHT:
        cursor = min(len(text), cursor + 1)
        if shift: sel_end = cursor
        else: sel_start = sel_end = cursor
        return text, cursor, sel_start, sel_end, True

    elif event.key == pygame.K_HOME:
        cursor = 0
        if shift: sel_end = cursor
        else: sel_start = sel_end = cursor
        return text, cursor, sel_start, sel_end, True

    elif event.key == pygame.K_END:
        cursor = len(text)
        if shift: sel_end = cursor
        else: sel_start = sel_end = cursor
        return text, cursor, sel_start, sel_end, True

    elif event.unicode.isprintable() and len(event.unicode) > 0 and event.unicode not in ('\r', '\n'):
        if s != e:
            text = text[:s] + text[e:]
            cursor = s
        text = text[:cursor] + event.unicode + text[cursor:]
        cursor += len(event.unicode)
        sel_start = sel_end = cursor
        return text, cursor, sel_start, sel_end, True

    return text, cursor, sel_start, sel_end, False

def _handle_mouse_wheel_event(self, event):
    mx, my = pygame.mouse.get_pos()
    pane = self._get_pane_for_x(mx)

    if getattr(self, 'is_editing', False) and getattr(self, 'edit_search_summary_active', False) and getattr(self, 'edit_search_summary_rect', pygame.Rect(0,0,0,0)).collidepoint(mx, my):
        sh = min(300, 45 + len(self.edit_search_summary_results) * 25)

        max_visible = (sh - 45) // 25
        max_s = max(0, len(self.edit_search_summary_results) - max_visible)
        self.edit_search_summary_scroll = max(0, min(max_s, getattr(self, 'edit_search_summary_scroll', 0) - event.y))
        return

