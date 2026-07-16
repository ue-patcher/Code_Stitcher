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

class StitchViewerApp:

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

    def _load_config(self):
        """Loads live-updating settings like Always On Top from the INI file."""
        appdata = os.environ.get('APPDATA', '')
        config_dir = os.path.join(appdata, "CodeStitcher") if appdata else getattr(self, 'script_dir', '')
        ini_path = os.path.join(config_dir, "cs_settings.ini")

        if os.path.exists(ini_path):
            try:
                with open(ini_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line_stripped = line.strip()
                        if line_stripped.startswith('CONF_VIEWER_ALWAYS_ON_TOP'):
                            val = line.split('=', 1)[1].strip().strip('"\'').lower()

                            new_always_on_top = (val == 'true')
                            if new_always_on_top != self.config.get('CONF_VIEWER_ALWAYS_ON_TOP', True):
                                self.config['CONF_VIEWER_ALWAYS_ON_TOP'] = new_always_on_top
                                self._log(f"Live updated Always On Top to: {new_always_on_top}")
                        elif line_stripped.startswith('CONF_VIEWER_WIDTH'):
                            val = line.split('=', 1)[1].strip().strip('"\'')
                            try:
                                new_width = max(800, int(float(val)))
                                if new_width != self.config.get('CONF_VIEWER_WIDTH', 1260):
                                    self.config['CONF_VIEWER_WIDTH'] = new_width
                                    self._log(f"Live updated CONF_VIEWER_WIDTH to: {new_width}")
                                    self.width = new_width
                                    self._reposition_and_resize_window()
                            except Exception as e:
                                self._log(f"Failed to parse live CONF_VIEWER_WIDTH: {e}")
            except Exception as e:
                self._log(f"Failed to reload config: {e}")

    def _format_bytes(self, size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}" if unit != 'B' else f"{size} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    def _get_parent_window_rect(self):
        """Helper to find the screen geometry bounds of the parent CodeStitcher process using raw platform types."""
        if os.name != 'nt' or not self.parent_pid:
            return None

        rects = []

        try:
            WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

            GetWindowThreadProcessId = ctypes.windll.user32.GetWindowThreadProcessId

            GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
            GetWindowThreadProcessId.restype = wintypes.DWORD

            IsWindowVisible = ctypes.windll.user32.IsWindowVisible

            IsWindowVisible.argtypes = [wintypes.HWND]
            IsWindowVisible.restype = wintypes.BOOL

            GetWindowRect = ctypes.windll.user32.GetWindowRect

            GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
            GetWindowRect.restype = wintypes.BOOL

            EnumWindows = ctypes.windll.user32.EnumWindows

            EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
            EnumWindows.restype = wintypes.BOOL

            def enum_windows_callback(hwnd, lparam):
                try:
                    w = rect.right - rect.left
                    h = rect.bottom - rect.top
                    
                    if w > 200 and h > 200 and -4000 < rect.left < 12000 and -4000 < rect.top < 12000:
                        rects.append((rect.left, rect.top, rect.right, rect.bottom))
                        return False
                except BaseException as err:
                    self._log(f"Error in enum_windows_callback: {err}")
                return True

            callback = WNDENUMPROC(enum_windows_callback)
            EnumWindows(callback, 0)
        except Exception as e:
            self._log(f"Error enumerating windows safely: {e}")

        return rects[0] if rects else None

    def _get_ext_color(self, filename):
        """Returns standard consensus-free custom cohesive file system colors.
        Harmonized to use the custom 4-color palette of the Stitch Viewer's core theme."""
        ext = os.path.splitext(filename)[1].lower()

        
        gold_orange   = (235, 195, 115) 

        string_green  = (106, 135, 89)  

        copper_rust   = (215, 100, 75)  

        orchid_purple = (155, 110, 190) 

        mapping = {
            
            '.py': gold_orange,
            '.js': gold_orange,
            '.jsx': gold_orange,
            '.ts': gold_orange,
            '.tsx': gold_orange,

            
            '.sh': string_green,
            '.bash': string_green,
            '.bat': string_green,
            '.ps1': string_green,
            '.go': string_green,

            
            '.cpp': copper_rust,
            '.cc': copper_rust,
            '.cxx': copper_rust,
            '.cs': copper_rust,
            '.java': copper_rust,
            '.rs': copper_rust,

            
            '.c': orchid_purple,
            '.h': orchid_purple,
            '.hpp': orchid_purple,
        }

        
        dull_exts = {
            '.html', '.htm', '.css', '.scss', '.sass', '.less',
            '.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
            '.md', '.markdown', '.txt', '.csv', '.log'
        }

        if ext in dull_exts:
            return (140, 140, 140)

        return mapping.get(ext, (210, 210, 210))  

    def _reposition_and_resize_window(self):
        """Resizes the Pygame surface and aligns it next to the parent window on the left-hand side."""
        if not getattr(self, 'hwnd', None) or os.name != 'nt':
            return

        parent_rect = self._get_parent_window_rect()
        if parent_rect:
            try:
                lx = int(parent_rect[0]) - self.width - 10
                ly = int(parent_rect[1])
                if -4000 < lx < 12000 and -4000 < ly < 12000:
                    
                    ctypes.windll.user32.SetWindowPos(self.hwnd, 0, lx, ly, self.width, self.height, 0x0004 | 0x0010)
            except (ValueError, TypeError) as e:
                self._log(f"Reposition failed: {e}")

        try:
            
            flags = self.screen.get_flags()
            self.screen = pygame.display.set_mode((self.width, self.height), flags)
        except Exception as e:
            self._log(f"Surface resize failed: {e}")

    def _update_ini_setting(self, key: str, value):
        """Helper to safely write values back to the ini file without overwriting other settings."""
        appdata = os.environ.get('APPDATA', '')
        if appdata:
            config_dir = os.path.join(appdata, "CodeStitcher")
        else:
            config_dir = getattr(self, 'script_dir', '')

        ini_path = os.path.join(config_dir, "cs_settings.ini")
        if not os.path.exists(ini_path): return

        try:
            with open(ini_path, 'r', encoding='utf-8') as f:
                content = f.read()

            val_str = f'"{value}"' if isinstance(value, str) else str(value)

            pat = re.compile(rf'^{key}\s*=.*$', re.MULTILINE)
            if pat.search(content):
                content = pat.sub(lambda m: f'{key} = {val_str}', content)
            else:
                content = content.rstrip() + f'\n{key} = {val_str}\n'

            with open(ini_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except: pass

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

    def _load_history(self):
        """Loads history while preserving exact tree expansion states during live reloads.
        Discovers all code files (even untracked) and groups external changes chronologically."""
        old_tree_data = getattr(self, 'tree_data', {})

        raw_history = []
        search_dirs = self.config.get("search_dirs", [])

        appdata = os.environ.get('APPDATA', '')
        if appdata:
            config_dir = os.path.join(appdata, "CodeStitcher")
        else:
            config_dir = getattr(self, 'script_dir', '')

        ini_path = os.path.join(config_dir, "cs_settings.ini")

        if os.path.exists(ini_path):
            try:
                with open(ini_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("CONF_LAST_DIFF_FILE"):
                            parts = line.split("=", 1)
                            if len(parts) > 1:
                                val = parts[1].strip().strip('"').strip("'")
                                if val:
                                    self.config["CONF_LAST_DIFF_FILE"] = val
                                    break
            except Exception:
                pass

        
        code_exts = {'.py', '.html', '.js', '.css', '.json', '.txt', '.md', '.c', '.cpp', '.cs', '.java', '.php', '.go', '.rs', '.ts', '.jsx', '.tsx', '.sh', '.bat'}

        discovered_files = {}

        for sdir in search_dirs:
            if not os.path.exists(sdir): continue
            for root, dirs, files in self._restricted_walk(sdir):
                if os.path.basename(root) == "ep_backups":
                    continue

                for f in files:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in code_exts:
                        full_path = os.path.join(root, f)
                        try:
                            mtime = os.path.getmtime(full_path)
                            ts_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))
                            
                            if f not in discovered_files or ts_str > discovered_files[f]['ts_str']:
                                discovered_files[f] = {'ts_str': ts_str, 'full_path': full_path}
                        except Exception:
                            pass

        
        known_baks = set()
        total_backups_bytes = 0

        for sdir in search_dirs:
            if not os.path.exists(sdir): continue
            for root, dirs, files in self._restricted_walk(sdir):
                if os.path.basename(root) != "ep_backups": continue

                
                for f in files:
                    try:
                        total_backups_bytes += os.path.getsize(os.path.join(root, f))
                    except Exception:
                        pass

                
                if "ep_history.json" in files:
                    json_path = os.path.join(root, "ep_history.json")
                    try:
                        with open(json_path, 'r', encoding='utf-8') as hf:
                            data = json.load(hf)
                            if isinstance(data, list):
                                for entry in data:
                                    
                                    diff_text = entry.get("diff", "")
                                    if diff_text.strip():
                                        entry['lines_added'] = sum(1 for l in diff_text.splitlines() if l.startswith('+') and not l.startswith('+++'))
                                        entry['lines_removed'] = sum(1 for l in diff_text.splitlines() if l.startswith('-') and not l.startswith('---'))
                                    else:
                                        entry['lines_added'] = 0
                                        entry['lines_removed'] = 0

                                    raw_history.append(entry)
                                    if entry.get("backup_reference"):
                                        known_baks.add(entry.get("backup_reference"))
                    except Exception:
                        pass

                
                
                for f in files:
                    if f.endswith('.bak') and f not in known_baks:
                        m = re.search(r'^(.*)_(\d+)_([A-Z]+)_(\d+)\.bak$', f)
                        if m:
                            orig_name = m.group(1)
                            parent_dir = os.path.dirname(root)
                            full_path = os.path.join(parent_dir, orig_name)

                            try:
                                mtime = os.path.getmtime(os.path.join(root, f))
                                ts_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))
                            except Exception:
                                ts_str = "1970-01-01 00:00:00"

                            raw_history.append({
                                "file": orig_name,
                                "full_path": full_path,
                                "timestamp": ts_str,
                                "backup_reference": f,
                                "lines_added": 0,
                                "lines_removed": 0
                            })

        self.total_backups_size_str = self._format_bytes(total_backups_bytes)

        file_groups = {}
        for entry in raw_history:
            fname = entry.get("file", "Unknown")
            if fname not in file_groups: file_groups[fname] = []
            file_groups[fname].append(entry)

        self.tree_data = {}

        
        for fname, info in discovered_files.items():
            self.tree_data[fname] = {
                'expanded': False,
                'runs': {},
                'last_ts': info['ts_str'],
                'full_path': info['full_path']
            }

        
        for fname, entries in file_groups.items():
            entries.sort(key=lambda x: x.get("timestamp", ""))
            current_run_id = "External Run"
            current_sess = 0

            for entry in entries:
                ref = entry.get("backup_reference", "")
                m = re.search(r'_(\d+)_([A-Z]+)_(\d+)\.bak$', ref)
                if m:
                    sess, let, wr = m.groups()
                    current_run_id = f"Run {sess}"
                    current_sess = int(sess)
                    entry['is_internal'] = (int(wr) == 1)
                    entry['job_letter'] = let
                    entry['write_num'] = int(wr)
                    entry['sess'] = current_sess
                else:
                    entry['is_internal'] = False
                    entry['job_letter'] = "E"
                    entry['write_num'] = 0
                    entry['sess'] = current_sess

                entry['run_id'] = current_run_id

            last_hist_ts = entries[-1].get("timestamp", "")
            if fname not in self.tree_data:
                self.tree_data[fname] = {
                    'expanded': False,
                    'runs': {},
                    'last_ts': last_hist_ts,
                    'full_path': entries[-1].get("full_path", "")
                }
            else:
                if last_hist_ts > self.tree_data[fname]['last_ts']:
                    self.tree_data[fname]['last_ts'] = last_hist_ts

            for entry in entries:
                run_id = entry['run_id']
                if run_id not in self.tree_data[fname]['runs']:
                    self.tree_data[fname]['runs'][run_id] = {'expanded': False, 'entries': [], 'sess': entry['sess']}
                self.tree_data[fname]['runs'][run_id]['entries'].append(entry)

        
        for fname, fdata in self.tree_data.items():
            if not fdata['runs']:
                fdata['runs']["Unversioned"] = {
                    'expanded': False,
                    'sess': 999999,
                    'entries': [{
                        'file': fname,
                        'full_path': fdata['full_path'],
                        'timestamp': fdata['last_ts'],
                        'backup_reference': "",
                        'is_internal': False,
                        'job_letter': "C",
                        'write_num': 0,
                        'sess': 999999,
                        'run_id': "Unversioned",
                        'lines_added': 0,
                        'lines_removed': 0,
                        'is_unversioned': True
                    }]
                }

        
        last_file = self.config.get("CONF_LAST_DIFF_FILE", "")
        if not last_file and self.tree_data:
            last_file = max(self.tree_data.keys(), key=lambda k: self.tree_data[k]['last_ts'])

        for fname, fdata in self.tree_data.items():
            if fname in old_tree_data:
                fdata['expanded'] = old_tree_data[fname]['expanded']
                for r_id, rdata in fdata['runs'].items():
                    if r_id in old_tree_data[fname]['runs']:
                        rdata['expanded'] = old_tree_data[fname]['runs'][r_id]['expanded']
            else:
                if fname == last_file:
                    fdata['expanded'] = True
                    if fdata['runs']:
                        latest_run = max(fdata['runs'].keys(), key=lambda k: fdata['runs'][k]['sess'])
                        fdata['runs'][latest_run]['expanded'] = True
                else:
                    fdata['expanded'] = False
                    for r in fdata['runs'].values():
                        r['expanded'] = False

        self._rebuild_render_list()

    def _rebuild_render_list(self):
        self.render_list = []
        sorted_files = sorted(self.tree_data.items(), key=lambda x: x[1]['last_ts'], reverse=True)
        for fname, fdata in sorted_files:
            self.render_list.append({'type': 'file', 'name': fname, 'expanded': fdata['expanded'], 'data': None})
            if fdata['expanded']:
                sorted_runs = sorted(fdata['runs'].items(), key=lambda x: x[1]['sess'], reverse=True)
                for run_id, rdata in sorted_runs:
                    self.render_list.append({'type': 'run', 'name': run_id, 'expanded': rdata['expanded'], 'file': fname, 'data': None})
                    if rdata['expanded']:
                        sorted_entries = sorted(rdata['entries'], key=lambda x: x.get('timestamp', ''), reverse=True)
                        for entry in sorted_entries:
                            self.render_list.append({'type': 'entry', 'name': fname, 'data': entry})

    def _get_entry_id(self, entry):
        return entry.get("timestamp", "") + entry.get("backup_reference", "")

    def _select_entry(self, entry):
        """Loads the complete files, handling ghost records intelligently so the renderer doesn't glitch."""
        if not entry: return
        self.active_entry_id = self._get_entry_id(entry)
        self.current_entry = entry
        self.current_file = entry.get("file")

        fname = entry.get("file", "")
        if fname:
            self._update_ini_setting('CONF_LAST_DIFF_FILE', fname)
            self.config['CONF_LAST_DIFF_FILE'] = fname

        full_path = entry.get("full_path", "")
        bak_ref = entry.get("backup_reference", "")

        self.active_file_path = full_path

        
        self.in_context_view = False
        self.scroll_context = 0

        
        new_lines = []
        self.new_file_size_str = "0 B"
        if full_path:
            if os.path.exists(full_path):
                new_text = self._read_file_text(full_path)
                new_lines = new_text.splitlines() if new_text else [""]
                try:
                    self.new_file_size_str = self._format_bytes(os.path.getsize(full_path))
                except Exception: pass
            else:
                new_lines = [
                    "// ------------------------------------------------ //",
                    "// ERROR: LIVE FILE DOES NOT EXIST                  //",
                    "// ------------------------------------------------ //"
                ]

        
        old_lines = []
        self.old_file_size_str = "0 B"
        if full_path and bak_ref:
            bak_path = os.path.join(os.path.dirname(full_path), "ep_backups", bak_ref)
            if os.path.exists(bak_path):
                old_text = self._read_file_text(bak_path)
                old_lines = old_text.splitlines() if old_text else [""]
                try:
                    self.old_file_size_str = self._format_bytes(os.path.getsize(bak_path))
                except Exception: pass
            else:
                old_lines = [
                    "// ------------------------------------------------ //",
                    "// ERROR: HISTORICAL BACKUP FILE DOES NOT EXIST     //",
                    f"// PATH: {bak_ref}",
                    "// This record exists in the history JSON, but the  //",
                    "// physical .bak file was deleted or moved.         //",
                    "// ------------------------------------------------ //"
                ]
        elif entry.get('is_unversioned', False):
            old_lines = [
                "// ------------------------------------------------ //",
                "// THIS IS AN UNVERSIONED LIVE FILE                 //",
                "// NO HISTORICAL DATA EXISTS                        //",
                "// ------------------------------------------------ //"
            ]

        self._build_side_by_side(old_lines, new_lines)
        self.scroll_right = 0
        self.scroll_right_target = 0.0
        self.scroll_right_float = 0.0
        self.selection_start = None
        self.selection_end = None

        
        if getattr(self, 'search_text', ''):
            self._update_search(jump=False)

    def _nav_history(self, direction):
        entry_indices = [i for i, item in enumerate(self.render_list) if item['type'] == 'entry']
        if not entry_indices: return

        curr_idx = -1
        for i, idx in enumerate(entry_indices):
            if self._get_entry_id(self.render_list[idx]['data']) == self.active_entry_id:
                curr_idx = i
                break

        if curr_idx != -1:
            new_idx = curr_idx + direction
            if 0 <= new_idx < len(entry_indices):
                target_item = self.render_list[entry_indices[new_idx]]
                self._select_entry(target_item['data'])

                
                vis_y = entry_indices[new_idx]

                max_visible = (self.height - self.title_bar_height) // 40
                if vis_y < self.scroll_left:
                    self.scroll_left = vis_y
                elif vis_y >= self.scroll_left + max_visible:
                    self.scroll_left = vis_y - max_visible + 1

    def _build_side_by_side(self, old_file_lines, new_file_lines):
        """Builds a full-file side-by-side comparison using difflib opcodes to align matching blocks.
        Splits contiguous diff blocks into sub-chunks by classes and functions, ignoring CRLF-only updates."""

        self.old_lines = []

        self.new_lines = []

        self.diff_blocks = []
        self.scroll_right_x = 0  
        self.scroll_right_x_target = 0.0
        self.scroll_right_x_float = 0.0

        self.max_right_width = 0
        for line in new_file_lines:
            w, _ = self.font.size(line.replace('\t', '    '))
            if w > self.max_right_width:
                self.max_right_width = w

        sm = difflib.SequenceMatcher(None, old_file_lines, new_file_lines)
        opcodes = sm.get_opcodes()

        for tag, i1, i2, j1, j2 in opcodes:
            if tag == 'equal':
                for k in range(i2 - i1):
                    self.old_lines.append((old_file_lines[i1 + k], "context", i1 + k + 1))
                    self.new_lines.append((new_file_lines[j1 + k], "context", j1 + k + 1))
            else:
                start_idx = len(self.old_lines)
                left_chunk = old_file_lines[i1:i2]
                right_chunk = new_file_lines[j1:j2]
                max_len = max(len(left_chunk), len(right_chunk))

                sub_blocks = []

                current_sub = {'start': start_idx, 'num_dels': 0, 'num_adds': 0, 'state': 'diff'}
                for k in range(max_len):
                    o_text = left_chunk[k] if k < len(left_chunk) else ""
                    n_text = right_chunk[k] if k < len(right_chunk) else ""

                    if k > 0:
                        o_strp = o_text.lstrip()
                        n_strp = n_text.lstrip()
                        split_cond = False
                        for prefix in ("def ", "class ", "async def ", "@"):
                            if o_strp.startswith(prefix) or n_strp.startswith(prefix):
                                split_cond = True
                                break
                        if split_cond:
                            current_sub['end'] = len(self.old_lines) - 1
                            sub_blocks.append(current_sub)

                            current_sub = {'start': len(self.old_lines), 'num_dels': 0, 'num_adds': 0, 'state': 'diff'}

                    if k < len(left_chunk):
                        self.old_lines.append((left_chunk[k], "deleted", i1 + k + 1))
                        current_sub['num_dels'] += 1
                    else:
                        self.old_lines.append(("", "blank_del", None))

                    if k < len(right_chunk):
                        self.new_lines.append((right_chunk[k], "added", j1 + k + 1))
                        current_sub['num_adds'] += 1
                    else:
                        self.new_lines.append(("", "blank_add", None))

                current_sub['end'] = len(self.old_lines) - 1
                sub_blocks.append(current_sub)

                end_idx = len(self.old_lines) - 1
                self.diff_blocks.append({
                    'start': start_idx,
                    'end': end_idx,
                    'num_dels': len(left_chunk),
                    'num_adds': len(right_chunk),
                    'state': 'diff',
                    'sub_chunks': sub_blocks
                })

        
        for block in self.diff_blocks:
            for sc in block.get('sub_chunks', []):
                is_sub = False
                for i in range(sc['start'], sc['end'] + 1):
                    o_text, o_status, _ = self.old_lines[i]
                    n_text, n_status, _ = self.new_lines[i]
                    if o_status == "deleted" and o_text.strip():
                        is_sub = True
                    if n_status == "added" and n_text.strip():
                        is_sub = True
                if not is_sub:
                    sc['state'] = 'merged'
                    for i in range(sc['start'], sc['end'] + 1):
                        o_text, o_status, o_ln = self.old_lines[i]
                        n_text, n_status, n_ln = self.new_lines[i]
                        if o_status == "deleted":
                            self.old_lines[i] = (o_text, "context", o_ln)
                        elif o_status == "blank_del":
                            self.old_lines[i] = ("", "blank_del", None)
                        if n_status == "added":
                            self.new_lines[i] = (n_text, "context", n_ln)
                        elif n_status == "blank_add":
                            self.new_lines[i] = ("", "blank_add", None)

        for block in self.diff_blocks:
            if all(sc.get('state', 'diff') == 'merged' for sc in block['sub_chunks']):
                block['state'] = 'merged'

        
        for _ in range(4):
            self.old_lines.append(("", "context", None))
            self.new_lines.append(("", "context", None))

        self._analyze_code_blocks()

        
        self.substantial_changes = []
        for block in self.diff_blocks:
            if block['state'] != 'diff': continue
            for sc_idx, sc in enumerate(block.get('sub_chunks', [])):
                if sc['state'] != 'diff': continue

                old_chunk = []

                new_chunk = []
                for i in range(sc['start'], sc['end'] + 1):
                    o_text, o_status, o_ln = self.old_lines[i]
                    n_text, n_status, n_ln = self.new_lines[i]
                    if o_status == "deleted" and o_text.strip():
                        old_chunk.append((o_text, o_ln, i))
                    if n_status == "added" and n_text.strip():
                        new_chunk.append((n_text, n_ln, i))

                if not old_chunk and not new_chunk:
                    continue

                
                func_name = "Global Scope"
                best_start = -1
                for b_start, b_end in getattr(self, 'code_blocks', {}).items():
                    if b_start <= sc['start'] <= b_end:
                        if b_start > best_start:
                            best_start = b_start
                if best_start != -1:
                    func_name = self.old_lines[best_start][0].strip()
                    if ":" in func_name:
                        func_name = func_name.split(":")[0]

                self.substantial_changes.append({
                    'func_name': func_name,
                    'old_lines': old_chunk[:4],  
                    'new_lines': new_chunk[:4],  
                    'visual_target': sc['start'],
                    'block_idx': self.diff_blocks.index(block),
                    'sc_idx': sc_idx
                })

        self._build_visible_indices()

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

    def _build_visible_indices(self):
        """Builds a mapping of visually active lines based on individually folded blocks."""
        if not hasattr(self, 'old_lines') or not self.old_lines:
            self.visible_indices = []

            self.actual_to_visual = []
            return

        self.is_line_folded = [False] * len(self.old_lines)
        i = 0

        while i < len(self.old_lines):
            if i in getattr(self, 'folded_blocks', set()):
                
                self.is_line_folded[i] = False
                end_idx = self.code_blocks[i]

                
                for j in range(i + 1, end_idx + 1):
                    self.is_line_folded[j] = True

                i = end_idx + 1 
            else:
                self.is_line_folded[i] = False
                i += 1

        self.visible_indices = [i for i in range(len(self.old_lines)) if not self.is_line_folded[i]]

        self.actual_to_visual = [-1] * len(self.old_lines)
        for v_idx, i in enumerate(self.visible_indices):
            self.actual_to_visual[i] = v_idx

        self._update_search(jump=False)

    def _update_search(self, jump=True):
        self.search_results = []
        old_current_idx = self.search_current_idx
        if not self.search_text or len(self.search_text) < 1:
            self.search_current_idx = -1
            return

        q = self.search_text.lower()

        
        
        if getattr(self, 'is_editing', False):
            for i, line in enumerate(self.edit_lines):
                if q in line.lower():
                    self.search_results.append(i)
        else:
            for i in range(len(self.old_lines)):
                t_old = self.old_lines[i][0].lower()
                t_new = self.new_lines[i][0].lower()
                if q in t_old or q in t_new:
                    self.search_results.append(i)

        if self.search_results:
            if getattr(self, 'is_editing', False):
                curr_row = self.edit_cursor_row
                closest_idx = 0
                min_dist = float('inf')
                for idx, r in enumerate(self.search_results):
                    dist = abs(r - curr_row)
                    if dist < min_dist:
                        min_dist = dist
                        closest_idx = idx
                self.search_current_idx = closest_idx
            else:
                if old_current_idx >= 0 and old_current_idx < len(self.search_results):
                    self.search_current_idx = old_current_idx
                else:
                    self.search_current_idx = 0

            if jump:
                self._jump_to_search_result()
        else:
            self.search_current_idx = -1

    def _scroll_to_minimap(self, my: int):
        diff_y_start = self.title_bar_height + 25
        map_h = self.height - diff_y_start

        is_ed = getattr(self, 'is_editing', False) or getattr(self, 'edit_anim_t', 0.0) > 0.0
        if is_ed:
            total_lines = len(getattr(self, 'edit_visible_indices', []))

            max_lines = (self.height - diff_y_start - 5) // self.line_height
        else:
            total_lines = len(getattr(self, 'visible_indices', getattr(self, 'old_lines', [])))
            max_lines = map_h // self.line_height
        if total_lines == 0 or map_h <= 0: return
        max_scroll = max(0, total_lines - max_lines)
        if getattr(self, '_minimap_drag_offset', None) is not None:
            
            click_y = my - diff_y_start - self._minimap_drag_offset
            ratio = click_y / map_h
            target_scroll = ratio * total_lines

            if is_ed:
                self.edit_target_scroll_y = max(0, min(max_scroll, target_scroll))
            else:
                if not hasattr(self, 'scroll_right_target'):
                    self.scroll_right_target = float(self.scroll_right)
                self.scroll_right_target = max(0.0, min(float(max_scroll), float(target_scroll)))
        else:
            
            click_y = my - diff_y_start
            ratio = click_y / map_h
            target_line = int(ratio * total_lines)

            if is_ed:
                self.edit_target_scroll_y = max(0, min(max_scroll, target_line - (max_lines // 2)))
            else:
                if not hasattr(self, 'scroll_right_target'):
                    self.scroll_right_target = float(self.scroll_right)
                self.scroll_right_target = max(0.0, min(float(max_scroll), float(target_line - (max_lines // 2))))

    def _get_pane_for_x(self, x):
        if x < self.left_panel_width:
            return "left"

        right_w = max(1, self.width - self.left_panel_width - self.minimap_width)
        pane_w = max(1, (right_w - self.GAP_WIDTH) // 2)
        gap_x = self.left_panel_width + pane_w

        if x < gap_x:
            return "old"
        elif x < gap_x + self.GAP_WIDTH:
            return "gap"
        elif x >= self.width - self.minimap_width:
            return "minimap"
        return "new"

    def _get_hovered_gap_button(self, mx, my):
        right_w = max(1, self.width - self.left_panel_width - self.minimap_width)
        pane_w = max(1, (right_w - self.GAP_WIDTH) // 2)
        gap_x = self.left_panel_width + pane_w

        if not (gap_x <= mx <= gap_x + self.GAP_WIDTH):
            return None, None, None

        diff_y_start = self.title_bar_height + 25

        for idx, block in enumerate(self.diff_blocks):
            if block['state'] != 'diff': continue

            active_scs = [sc for sc in block.get('sub_chunks', []) if sc['state'] == 'diff']
            if not active_scs: continue

            first_unmerged = active_scs[0]
            
            has_big_arrow = sum(1 for sc in active_scs if sc['num_dels'] > 0) > 1

            for sc_idx, sc in enumerate(block['sub_chunks']):
                if sc['state'] != 'diff': continue

                v_start_sc = -1
                for i in range(sc['start'], sc['end'] + 1):
                    if self.actual_to_visual[i] != -1:
                        v_start_sc = self.actual_to_visual[i]
                        break

                if v_start_sc == -1: continue

                y1_sc = diff_y_start + ((v_start_sc - self.scroll_right) * self.line_height)
                btn_y = y1_sc + 5

                is_first = (sc == first_unmerged)
                if is_first and has_big_arrow:
                    
                    big_arrow_rect = pygame.Rect(gap_x + 4, y1_sc + 2, self.GAP_WIDTH - 8, 22)
                    if big_arrow_rect.collidepoint(mx, my):
                        return idx, None, 'restore_all'

                    
                    btn_y += 26

                if sc['num_dels'] > 0:
                    btn_restore_rect = pygame.Rect(gap_x + 4, btn_y, 22, 22)
                    if btn_restore_rect.collidepoint(mx, my):
                        return idx, sc_idx, 'restore'

                if sc['num_adds'] > 0:
                    btn_delete_rect = pygame.Rect(gap_x + self.GAP_WIDTH - 26, btn_y, 22, 22)
                    if btn_delete_rect.collidepoint(mx, my):
                        return idx, sc_idx, 'delete'

        return None, None, None

    def _apply_diff_block(self, idx, sc_idx, action):
        """Applies a block or specific sub-chunk in memory and immediately Auto-Saves to the live file."""
        block = self.diff_blocks[idx]

        if sc_idx is None:
            
            chunks = [sc for sc in block['sub_chunks'] if sc.get('state', 'diff') == 'diff']
        else:
            chunks = [block['sub_chunks'][sc_idx]]

        for sc in chunks:
            start = sc['start']
            end = sc['end']

            if action in ('restore', 'restore_all'):
                for i in range(start, end + 1):
                    left_text, left_status, ln = self.old_lines[i]
                    if left_status == 'deleted':
                        self.new_lines[i] = (left_text, "context", None)
                        self.old_lines[i] = (left_text, "context", ln)
                    elif left_status == 'blank_del':
                        self.new_lines[i] = ("", "blank_add", None)
                sc['state'] = 'merged'

            elif action == 'delete':
                for i in range(start, end + 1):
                    right_text, right_status, ln = self.new_lines[i]
                    if right_status == 'added':
                        self.new_lines[i] = ("", "blank_add", None)
                sc['state'] = 'merged'

        
        if all(sc.get('state', 'diff') == 'merged' for sc in block['sub_chunks']):
            block['state'] = 'merged'

        
        if hasattr(self, 'active_file_path') and self.active_file_path:
            if os.path.exists(self.active_file_path):
                try:
                    output_lines = []
                    for text, status, ln in self.new_lines:
                        if status in ("context", "added"):
                            output_lines.append(text)
                    with open(self.active_file_path, 'w', encoding='utf-8', newline='\n') as f:
                        f.write("\n".join(output_lines) + "\n")
                except Exception as e:
                    print(f"Auto-Save failed: {e}")

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

    def _copy_multiple_code_blocks(self, blocks, pane):
        self.context_menu = None
        lines = self.old_lines if pane == "old" else self.new_lines
        selected_indices = set()

        for b_start, b_end in blocks:
            selected_indices.update(range(b_start, b_end + 1))

        copied_text = []
        for i in sorted(list(selected_indices)):
            if 0 <= i < len(lines):
                text, status, ln = lines[i]
                if status not in ("blank_del", "blank_add", "header"):
                    copied_text.append(text)

        if copied_text:
            try: pyperclip.copy("\n".join(copied_text))
            except: pass

    def _copy_editor_selection(self):
        self.context_menu = None
        sel = self._get_editor_selection_range()
        if sel:
            (r1, c1), (r2, c2) = sel
            
            r1 = max(0, min(len(self.edit_lines) - 1, r1))
            r2 = max(0, min(len(self.edit_lines) - 1, r2))
            c1 = max(0, min(len(self.edit_lines[r1]), c1))
            c2 = max(0, min(len(self.edit_lines[r2]), c2))

            if r1 == r2:
                text = self.edit_lines[r1][c1:c2]
            else:
                text_parts = [self.edit_lines[r1][c1:]]
                for r in range(r1+1, r2):
                    text_parts.append(self.edit_lines[r])
                text_parts.append(self.edit_lines[r2][:c2])
                text = "\n".join(text_parts)
            try:
                pyperclip.copy(text)
                self._log("Copied editor selection to clipboard.")
            except Exception as e:
                self._log(f"Editor right-click copy selection failed: {e}")

    def _search_editor_selection(self):
        self.context_menu = None
        sel = self._get_editor_selection_range()
        if sel:
            (r1, c1), (r2, c2) = sel
            
            r1 = max(0, min(len(self.edit_lines) - 1, r1))
            r2 = max(0, min(len(self.edit_lines) - 1, r2))
            c1 = max(0, min(len(self.edit_lines[r1]), c1))
            c2 = max(0, min(len(self.edit_lines[r2]), c2))

            if r1 == r2:
                text = self.edit_lines[r1][c1:c2]
            else:
                text_parts = [self.edit_lines[r1][c1:]]
                for r in range(r1+1, r2):
                    text_parts.append(self.edit_lines[r])
                text_parts.append(self.edit_lines[r2][:c2])
                text = "\n".join(text_parts)

            if text:
                self.search_text = text

                self.edit_search_summary_results = []
                q_low = text.lower()
                for i, line in enumerate(self.edit_lines):
                    if q_low in line.lower():
                        self.edit_search_summary_results.append((i, line))
                self.edit_search_summary_active = True
                self.edit_search_summary_scroll = 0
                self._update_search()

    def handle_events(self) -> bool:
        """Dispatches event loops cleanly to modular scope helpers."""
        events = pygame.event.get()
        if not events:
            return False

        for event in events:
            try:
                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.ACTIVEEVENT:
                    if getattr(event, 'state', 0) & 2:
                        self.focused = bool(event.gain)

                elif event.type == pygame.KEYDOWN:
                    self._handle_keydown_event(event)

                elif event.type == pygame.MOUSEMOTION:
                    self._handle_mouse_motion_event(event)

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self._handle_mouse_button_down_event(event)

                elif event.type == pygame.MOUSEBUTTONUP:
                    self._handle_mouse_button_up_event(event)

                elif event.type == pygame.MOUSEWHEEL:
                    self._handle_mouse_wheel_event(event)

            except BaseException as e:
                self._log(f"FATAL ERROR IN EVENT LOOP: {e}\n{traceback.format_exc()}")

        return True

    def run(self):
        """Viewer loop with Native Python Parent-Process Heartbeat and Live INI monitoring."""
        self._log("Entered run() loop.")
        os.environ['SDL_MOUSE_FOCUS_CLICKTHROUGH'] = "1"
        clock = pygame.time.Clock()

        dirty = True
        last_mx, last_my = -1, -1
        update_timer = 0
        heartbeat_timer = 0
        consecutive_draw_errors = 0

        def is_parent_running(pid):
            if pid is None: return True
            if os.name == 'nt':
                try:
                    kernel32 = ctypes.windll.kernel32
                    if not hasattr(kernel32.OpenProcess, 'argtypes'):
                        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
                        kernel32.OpenProcess.restype = wintypes.HANDLE

                        kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
                        kernel32.GetExitCodeProcess.restype = wintypes.BOOL

                        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
                        kernel32.CloseHandle.restype = wintypes.BOOL

                    process = kernel32.OpenProcess(0x1000, False, pid)
                    if process:
                        exit_code = wintypes.DWORD()
                        kernel32.GetExitCodeProcess(process, ctypes.byref(exit_code))
                        kernel32.CloseHandle(process)
                        return exit_code.value == 259
                    return False
                except Exception as e:
                    self._log(f"Warning: is_parent_running Windows error: {e}")
                    return True
            else:
                try:
                    os.kill(pid, 0)
                    return True
                except ProcessLookupError:
                    return False
                except PermissionError:
                    return True
                except Exception as e:
                    self._log(f"Warning: is_parent_running Linux error: {e}")
                    return True

        while self.running:
            try:
                if self.handle_events():
                    dirty = True

                
                if getattr(self, 'edit_is_dragging', False) and getattr(self, 'is_editing', False):
                    mx, my = pygame.mouse.get_pos()
                    diff_y_start = self.title_bar_height + 25
                    scroll_speed = 0.0

                    if my < diff_y_start:
                        dist = diff_y_start - my
                        scroll_speed = -(0.2 + (dist ** 1.3) * 0.02)
                    elif my > self.height - 5:
                        dist = my - (self.height - 5)
                        scroll_speed = 0.2 + (dist ** 1.3) * 0.02

                    if scroll_speed != 0.0:
                        max_lines = (self.height - diff_y_start - 5) // self.line_height
                        old_target = getattr(self, 'edit_target_scroll_y', 0.0)
                        max_scroll = max(0, len(getattr(self, 'edit_visible_indices', [])) - max_lines)
                        self.edit_target_scroll_y = max(0.0, min(float(max_scroll), old_target + scroll_speed))

                        if abs(old_target - self.edit_target_scroll_y) > 0.01:
                            
                            class DummyEvent:
                                pos = (mx, my)
                            self._handle_editor_mouse(DummyEvent(), down=False)
                            dirty = True

                mx, my = pygame.mouse.get_pos()
                if (mx, my) != (last_mx, last_my):
                    dirty = True
                    last_mx, last_my = mx, my

                if getattr(self, 'is_selecting', False) or getattr(self, 'is_dragging_minimap', False) or getattr(self, '_is_dragging', False):
                    dirty = True

                if getattr(self, 'is_editing', False) or getattr(self, 'search_active', False):
                    dirty = True

                
                target_t = 1.0 if getattr(self, 'is_editing', False) else 0.0
                if not hasattr(self, 'edit_anim_t'):
                    self.edit_anim_t = 0.0
                if self.edit_anim_t != target_t:
                    self.edit_anim_t += (target_t - self.edit_anim_t) * 0.15
                    if abs(self.edit_anim_t - target_t) < 0.005:
                        self.edit_anim_t = target_t
                    dirty = True

                if getattr(self, 'is_editing', False) or getattr(self, 'edit_anim_t', 0.0) > 0.0:
                    
                    if not hasattr(self, 'edit_target_scroll_y'):
                        self.edit_target_scroll_y = self.edit_scroll_y
                    if not hasattr(self, 'edit_scroll_y_float'):
                        self.edit_scroll_y_float = float(self.edit_scroll_y)

                    if abs(self.edit_scroll_y_float - self.edit_target_scroll_y) > 0.01:
                        self.edit_scroll_y_float += (self.edit_target_scroll_y - self.edit_scroll_y_float) * 0.15
                        self.edit_scroll_y = int(self.edit_scroll_y_float)
                        dirty = True
                    else:
                        self.edit_scroll_y_float = float(self.edit_target_scroll_y)
                        self.edit_scroll_y = int(self.edit_target_scroll_y)

                    
                    if getattr(self, 'edit_flash_line_nums', 0.0) > 0.0:
                        self.edit_flash_line_nums -= 0.08
                        if self.edit_flash_line_nums < 0.0:
                            self.edit_flash_line_nums = 0.0
                        dirty = True

                    
                    if getattr(self, 'edit_save_btn_flash', 0.0) > 0.0:
                        self.edit_save_btn_flash -= 0.08
                        if self.edit_save_btn_flash < 0.0:
                            self.edit_save_btn_flash = 0.0
                        dirty = True

                
                if not hasattr(self, 'scroll_right_target'):
                    self.scroll_right_target = float(self.scroll_right)
                if not hasattr(self, 'scroll_right_float'):
                    self.scroll_right_float = float(self.scroll_right)

                if abs(self.scroll_right_float - self.scroll_right_target) > 0.01:
                    self.scroll_right_float += (self.scroll_right_target - self.scroll_right_float) * 0.15
                    self.scroll_right = int(self.scroll_right_float)
                    dirty = True
                else:
                    self.scroll_right_float = float(self.scroll_right_target)
                    self.scroll_right = int(self.scroll_right_target)

                
                if not hasattr(self, 'scroll_right_x_target'):
                    self.scroll_right_x_target = float(self.scroll_right_x)
                if not hasattr(self, 'scroll_right_x_float'):
                    self.scroll_right_x_float = float(self.scroll_right_x)

                if getattr(self, 'is_dragging_scroll_x', False):
                    self.scroll_right_x_target = float(self.scroll_right_x)
                    self.scroll_right_x_float = float(self.scroll_right_x)
                elif abs(self.scroll_right_x_float - self.scroll_right_x_target) > 0.01:
                    self.scroll_right_x_float += (self.scroll_right_x_target - self.scroll_right_x_float) * 0.15
                    self.scroll_right_x = int(self.scroll_right_x_float)
                    dirty = True
                else:
                    self.scroll_right_x_float = float(self.scroll_right_x_target)
                    self.scroll_right_x = int(self.scroll_right_x_target)

                
                if getattr(self, 'edit_structure_pending', False):
                    if time.time() - getattr(self, 'edit_structure_request_time', 0) > 0.3: 
                        self._analyze_edit_code_blocks()
                        self._build_edit_visible_indices()
                        self.edit_structure_pending = False
                        dirty = True

                
                if getattr(self, 'edit_linter_pending', False):
                    if time.time() - getattr(self, 'edit_linter_request_time', 0) > 0.35: 
                        self._execute_linter_syntax_check()
                        self.edit_linter_pending = False
                        dirty = True

                update_timer += 1
                heartbeat_timer += 1

                
                if update_timer >= 180:
                    update_timer = 0
                    if self._check_history_updates():
                        dirty = True

                    
                    try:
                        appdata = os.environ.get('APPDATA', '')
                        conf_dir = os.path.join(appdata, "CodeStitcher") if appdata else getattr(self, 'script_dir', '')
                        ini_path = os.path.join(conf_dir, "cs_settings.ini")
                        if os.path.exists(ini_path):
                            curr_mtime = os.path.getmtime(ini_path)
                            if not hasattr(self, '_last_ini_mtime'):
                                self._last_ini_mtime = curr_mtime
                            elif curr_mtime > self._last_ini_mtime:
                                self._last_ini_mtime = curr_mtime
                                self._log("INI file modification detected. Live-reloading config.")
                                self._load_config()
                                dirty = True
                    except Exception:
                        pass

                
                if heartbeat_timer >= 120:
                    heartbeat_timer = 0
                    if self.parent_pid is not None and not is_parent_running(self.parent_pid):
                        self._log(f"HEARTBEAT FAILED! Parent PID {self.parent_pid} is no longer running. Exiting gracefully.")
                        self.running = False
                        break

                if dirty:
                    try:
                        self.draw()
                        pygame.display.flip()
                        consecutive_draw_errors = 0
                        dirty = False
                    except Exception as e:
                        consecutive_draw_errors += 1
                        self._log(f"DRAW ERROR ({consecutive_draw_errors}): {e}\n{traceback.format_exc()}")
                        if consecutive_draw_errors > 5:
                            self._log("Too many consecutive draw errors. Resetting UI state to attempt healing.")
                            self.is_editing = False
                            self.in_context_view = False
                            consecutive_draw_errors = 0
                        dirty = False

                clock.tick(60)

            except BaseException as run_err:
                self._log(f"CRASH IN MAIN RUN LOOP CAUGHT: {run_err}\n{traceback.format_exc()}")
                if isinstance(run_err, SystemExit):
                    raise
                time.sleep(0.1)

        self._log("Main loop terminated. Saving position and exiting.")
        pygame.quit()
        sys.exit(0)

    def draw_title_bar(self, title):
        is_focused = getattr(self, 'focused', True)

        BAR_COLOR = (80, 80, 80) if is_focused else (50, 50, 50)
        pygame.draw.rect(self.screen, BAR_COLOR, (0, 0, self.width, self.title_bar_height))

        text_color = (255, 255, 255) if is_focused else (180, 180, 180)
        title_surf = self.title_font.render(title, True, text_color)

        title_y = (((self.title_bar_height - title_surf.get_height()) // 2 ) + 1)
        self.screen.blit(title_surf, (10, title_y))

        mx, my = pygame.mouse.get_pos()
        is_over_titlebar = my < self.title_bar_height

        BUTTON_WIDTH = 40

        BUTTON_HEIGHT = self.title_bar_height
        minimize_rect = pygame.Rect(self.width - BUTTON_WIDTH * 2, 0, BUTTON_WIDTH, BUTTON_HEIGHT)
        close_rect    = pygame.Rect(self.width - BUTTON_WIDTH,     0, BUTTON_WIDTH, BUTTON_HEIGHT)

        min_hovered = is_over_titlebar and minimize_rect.collidepoint(mx, my)

        min_color = (110, 110, 110) if min_hovered else BAR_COLOR
        pygame.draw.rect(self.screen, min_color, minimize_rect)
        min_surf = self.close_font.render("–", True, text_color)
        min_x = minimize_rect.centerx - min_surf.get_width() // 2
        min_y = minimize_rect.centery - min_surf.get_height() // 2
        self.screen.blit(min_surf, (min_x, min_y))

        close_hovered = is_over_titlebar and close_rect.collidepoint(mx, my)

        close_color = (200, 50, 50) if close_hovered else BAR_COLOR
        pygame.draw.rect(self.screen, close_color, close_rect)
        x_surf = self.close_font.render("×", True, text_color)
        x_x = close_rect.centerx - x_surf.get_width() // 2
        x_y = close_rect.centery - x_surf.get_height() // 2
        self.screen.blit(x_surf, (x_x, x_y))

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

    def _check_history_updates(self) -> bool:
        """Polls json history AND live code file modifications. Updates UI if new edits are found."""
        if not hasattr(self, 'history_mtimes'):
            self.history_mtimes = {}

        this_that = 1
        that_this = 2308
        needs_reload = False
        search_dirs = self.config.get("search_dirs", [])

        code_exts = {'.py', '.html', '.js', '.css', '.json', '.txt', '.md', '.c', '.cpp', '.cs', '.java', '.php', '.go', '.rs', '.ts', '.jsx', '.tsx', '.sh', '.bat'}

        for sdir in search_dirs:
            if not os.path.exists(sdir): continue
            for root, dirs, files in self._restricted_walk(sdir):
                is_backup_dir = (os.path.basename(root) == "ep_backups")

                for f in files:
                    if is_backup_dir:
                        if f == "ep_history.json":
                            json_path = os.path.join(root, f)
                            try:
                                current_mtime = os.path.getmtime(json_path)
                                last_mtime = self.history_mtimes.get(json_path)
                                if last_mtime is None or current_mtime > last_mtime:
                                    self.history_mtimes[json_path] = current_mtime
                                    needs_reload = True
                            except: pass
                    else:
                        ext = os.path.splitext(f)[1].lower()
                        if ext in code_exts:
                            full_path = os.path.join(root, f)
                            try:
                                current_mtime = os.path.getmtime(full_path)
                                last_mtime = self.history_mtimes.get(full_path)
                                if last_mtime is None:
                                    self.history_mtimes[full_path] = current_mtime
                                elif current_mtime > last_mtime:
                                    self.history_mtimes[full_path] = current_mtime
                                    needs_reload = True
                            except: pass

        if needs_reload:
            self._load_history()
            return True

        return False

    def _log(self, msg: str) -> None:
        """Appends timestamped debug messages to stitch_viewer_debug.log. Never crashes the app."""
        try:
            appdata = os.environ.get('APPDATA', '')
            if appdata:
                log_dir = os.path.join(appdata, "CodeStitcher")
                os.makedirs(log_dir, exist_ok=True)
            else:
                log_dir = getattr(self, 'script_dir', '')

            log_path = os.path.join(log_dir, "stitch_viewer_debug.log")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        except Exception:
            pass

    def _analyze_code_blocks(self):
        """Properly detects nested functions/classes for BOTH Python and brace-based languages."""
        self.code_blocks = {}

        self.block_depths = {}
        self.folded_blocks = set()

        if hasattr(self, 'current_fold_level'):
            del self.current_fold_level

        stack = []

        path = getattr(self, 'active_file_path', '')
        ext = os.path.splitext(path)[1].lower() if path else ''
        is_brace_lang = ext in {'.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs',
                                '.c', '.cpp', '.cc', '.cxx', '.h', '.hpp',
                                '.java', '.cs', '.go', '.rs', '.swift', '.kt', '.scala', '.php',
                                '.json', '.css', '.scss', '.less'}

        last_def_line = -1

        for i in range(len(self.old_lines)):
            t_new, st_new, _ = self.new_lines[i]
            t_old, st_old, _ = self.old_lines[i]
            t = t_new if st_new not in ("blank_add", "blank_del") else t_old
            stripped = t.lstrip()

            
            if not stripped or stripped.startswith('#') or stripped.startswith('//'):
                continue

            
            if is_brace_lang:
                lower = stripped.lower()

                
                if any(kw in lower for kw in ('function', 'class ', 'struct ', 'interface ', 'enum ', 'namespace ', '=>')) or\
                   (stripped.endswith(')') and '(' in stripped) or\
                   stripped.endswith('='):
                    last_def_line = i

                open_braces = stripped.count('{') + stripped.count('[')
                close_braces = stripped.count('}') + stripped.count(']')

                for _ in range(open_braces):
                    if last_def_line != -1 and (i - last_def_line) <= 2:
                        stack.append((last_def_line, len(stack)))
                        last_def_line = -1
                    else:
                        stack.append((i, len(stack)))

                for _ in range(close_braces):
                    if stack:
                        start, depth = stack.pop()
                        if start not in self.code_blocks:
                            self.code_blocks[start] = i
                            self.block_depths[start] = depth

            
            else:
                indent = len(t) - len(stripped)

                
                while stack:
                    prev_i, _ = stack[-1]
                    pt_new, pst_new, _ = self.new_lines[prev_i]
                    pt_old, pst_old, _ = self.old_lines[prev_i]
                    pt = pt_new if pst_new not in ("blank_add", "blank_del") else pt_old
                    prev_indent = len(pt) - len(pt.lstrip())

                    if indent <= prev_indent:
                        start, depth = stack.pop()
                        
                        end_val = i - 1
                        while end_val > start:
                            et_new, est_new, _ = self.new_lines[end_val]
                            et_old, est_old, _ = self.old_lines[end_val]
                            et = et_new if est_new not in ("blank_add", "blank_del") else et_old
                            if et.strip():
                                break
                            end_val -= 1

                        if end_val > start:
                            self.code_blocks[start] = end_val
                            self.block_depths[start] = depth
                    else:
                        break

                stack.append((i, len(stack)))

        
        while stack:
            start, depth = stack.pop()
            end_val = len(self.old_lines) - 1
            while end_val > start:
                t_check_new, st_check_new, _ = self.new_lines[end_val]
                t_check_old, st_check_old, _ = self.old_lines[end_val]
                t_check = t_check_new if st_check_new not in ("blank_add", "blank_del") else t_check_old
                if t_check.strip():
                    break
                end_val -= 1

            if end_val > start:
                if not is_brace_lang:
                    self.code_blocks[start] = end_val
                    self.block_depths[start] = depth
                elif start not in self.code_blocks:
                    self.code_blocks[start] = end_val
                    self.block_depths[start] = depth

        
        keys_to_remove = [k for k, v in self.code_blocks.items() if v <= k]
        for k in keys_to_remove:
            del self.code_blocks[k]
            if k in getattr(self, 'block_depths', {}):
                del self.block_depths[k]

    def draw(self) -> None:
        self.screen.fill((30, 30, 30))
        self.draw_title_bar(f"Stitch Viewer {version} - File Revision History, Diff Viewer, Editor and built-in Linter")
        self._linter_tooltip = None

        mx, my = pygame.mouse.get_pos()
        is_pressed = pygame.mouse.get_pressed()[0]
        tree_y_start = self.title_bar_height + 25

        
        pygame.draw.rect(self.screen, (35, 35, 35), (0, self.title_bar_height, self.left_panel_width, 25))
        self.tree_fold_rect = pygame.Rect(5, self.title_bar_height + 3, self.left_panel_width - 35, 19)
        self.refresh_rect = pygame.Rect(self.left_panel_width - 27, self.title_bar_height + 3, 22, 19)

        
        hover_tf = self.tree_fold_rect.collidepoint(mx, my)
        click_tf = hover_tf and is_pressed
        pygame.draw.rect(self.screen, (40, 40, 45) if click_tf else ((70, 70, 75) if hover_tf else (50, 50, 55)), self.tree_fold_rect, border_radius=3)
        pygame.draw.rect(self.screen, (90, 90, 100) if click_tf else ((110, 110, 120) if hover_tf else (90, 90, 100)), self.tree_fold_rect, 1, border_radius=3)

        current_file = self.current_entry.get("file") if hasattr(self, 'current_entry') and self.current_entry else None
        active_fully_expanded = False
        if current_file and current_file in getattr(self, 'tree_data', {}):
            fdata = self.tree_data[current_file]
            if fdata['expanded'] and all(r['expanded'] for r in fdata['runs'].values()):
                active_fully_expanded = True

        tf_text = "[-] Collapse All" if active_fully_expanded else "[+] Expand Active"
        tf_surf = self.font.render(tf_text, True, (200, 200, 200))
        oy_tf = 1 if click_tf else 0
        self.screen.blit(tf_surf, (self.tree_fold_rect.centerx - tf_surf.get_width()//2, self.tree_fold_rect.centery - tf_surf.get_height()//2 + 1 + oy_tf))

        
        hover_ref = self.refresh_rect.collidepoint(mx, my)
        click_ref = hover_ref and is_pressed
        pygame.draw.rect(self.screen, (40, 40, 45) if click_ref else ((70, 70, 75) if hover_ref else (50, 50, 55)), self.refresh_rect, border_radius=3)
        pygame.draw.rect(self.screen, (90, 90, 100) if click_ref else ((110, 110, 120) if hover_ref else (90, 90, 100)), self.refresh_rect, 1, border_radius=3)
        cx, cy = self.refresh_rect.center
        if click_ref: cy += 1
        pygame.draw.circle(self.screen, (200, 200, 200), (cx, cy), 5, 2)
        pygame.draw.rect(self.screen, (40, 40, 45) if click_ref else ((70, 70, 75) if hover_ref else (50, 50, 55)), (cx, cy-6, 6, 6)) 
        pygame.draw.polygon(self.screen, (200, 200, 200), [(cx, cy-8), (cx+5, cy-5), (cx+1, cy-1)]) 

        
        pygame.draw.rect(self.screen, (25, 25, 25), (0, tree_y_start, self.left_panel_width, self.height - tree_y_start))

        left_clip = pygame.Rect(0, tree_y_start, self.left_panel_width, self.height - tree_y_start - 25)
        self.screen.set_clip(left_clip)

        visible_items = (self.height - tree_y_start - 25) // self.tree_row_height + 1

        for i in range(self.scroll_left, min(len(self.render_list), self.scroll_left + visible_items)):
            item = self.render_list[i]
            y = tree_y_start + ((i - self.scroll_left) * self.tree_row_height)
            rect = pygame.Rect(0, y, self.left_panel_width, self.tree_row_height)

            is_hovered = (i == self.hovered_history_idx)

            indent_file = 5
            indent_run = 18
            indent_entry = 32

            if item['type'] == 'entry':
                entry = item['data']

                is_active = (self._get_entry_id(entry) == self.active_entry_id)
                if is_active:
                    pygame.draw.rect(self.screen, (50, 75, 120), rect)
                elif is_hovered:
                    pygame.draw.rect(self.screen, (40, 40, 45), rect)

                pygame.draw.line(self.screen, (60, 60, 60), (indent_run + 4, y), (indent_run + 4, y + self.tree_row_height // 2))
                pygame.draw.line(self.screen, (60, 60, 60), (indent_run + 4, y + self.tree_row_height // 2), (indent_entry - 4, y + self.tree_row_height // 2))

                ts_raw = entry.get("timestamp", "")
                ts_str = ts_raw.split(" ")[1][:5] if " " in ts_raw else ts_raw[-8:-3]

                if entry.get('is_unversioned', False):
                    name_str = f"{ts_str} - Live File"

                    fg_color = (100, 140, 100)
                elif entry['is_internal']:
                    name_str = f"{ts_str} - {entry['job_letter']}{entry['write_num']}"

                    fg_color = (190, 190, 190)
                else:
                    name_str = f"{ts_str} - Ext"

                    fg_color = (100, 100, 100)
                    e_surf = self.tree_stat_font.render("E", True, (160, 140, 50))
                    self.screen.blit(e_surf, (4, y + (self.tree_row_height - e_surf.get_height()) // 2))

                t_surf = self.font.render(name_str, True, fg_color)
                self.screen.blit(t_surf, (indent_entry + 2, y + (self.tree_row_height - t_surf.get_height()) // 2))

                adds = entry.get("lines_added", 0)
                dels = entry.get("lines_removed", 0)
                if adds > 0 or dels > 0:
                    stats = f"+{adds} -{dels}"
                    s_surf = self.tree_stat_font.render(stats, True, (110, 160, 110))
                    self.screen.blit(s_surf, (self.left_panel_width - s_surf.get_width() - 4, y + (self.tree_row_height - s_surf.get_height()) // 2))

            elif item['type'] == 'run':
                if is_hovered: pygame.draw.rect(self.screen, (40, 40, 45), rect)
                pygame.draw.line(self.screen, (60, 60, 60), (indent_file + 4, y), (indent_file + 4, y + self.tree_row_height))
                box_rect = pygame.Rect(indent_run, y + self.tree_row_height//2 - 4, 9, 9)
                pygame.draw.rect(self.screen, (100, 100, 100), box_rect, 1)
                pygame.draw.line(self.screen, (200, 200, 200), (box_rect.left + 2, box_rect.centery), (box_rect.right - 3, box_rect.centery))
                if not item['expanded']:
                    pygame.draw.line(self.screen, (200, 200, 200), (box_rect.centerx, box_rect.top + 2), (box_rect.centerx, box_rect.bottom - 3))

                rn = item['name']
                if rn.startswith("Run "): rn = rn.replace("Run ", "R ")
                j_surf = self.font.render(rn, True, (150, 170, 190))
                self.screen.blit(j_surf, (indent_run + 14, y + (self.tree_row_height - j_surf.get_height()) // 2))

            elif item['type'] == 'file':
                if is_hovered: pygame.draw.rect(self.screen, (40, 40, 45), rect)
                box_rect = pygame.Rect(indent_file, y + self.tree_row_height//2 - 4, 9, 9)

                
                ext_color = self._get_ext_color(item['name'])

                pygame.draw.rect(self.screen, ext_color, box_rect, 1)
                pygame.draw.line(self.screen, (220, 220, 220), (box_rect.left + 2, box_rect.centery), (box_rect.right - 3, box_rect.centery))
                if not item['expanded']:
                    pygame.draw.line(self.screen, (220, 220, 220), (box_rect.centerx, box_rect.top + 2), (box_rect.centerx, box_rect.bottom - 3))

                f_surf = self.font_bold.render(item['name'], True, ext_color)
                self.screen.blit(f_surf, (indent_file + 14, y + (self.tree_row_height - f_surf.get_height()) // 2))

        self.screen.set_clip(None)

        
        pygame.draw.rect(self.screen, (35, 35, 40), (0, self.height - 25, self.left_panel_width, 25))
        pygame.draw.line(self.screen, (55, 55, 60), (0, self.height - 25), (self.left_panel_width, self.height - 25))
        bak_sz = getattr(self, 'total_backups_size_str', '0 B')
        b_surf = self.tree_stat_font.render(f"Backup Cache: {bak_sz}", True, (150, 150, 160))
        self.screen.blit(b_surf, (5, self.height - 25 + (25 - b_surf.get_height()) // 2))

        
        right_w = max(1, self.width - self.left_panel_width - self.minimap_width)
        pane_w = max(1, (right_w - self.GAP_WIDTH) // 2)
        pane_old_x = self.left_panel_width
        gap_x = pane_old_x + pane_w
        pane_new_x = gap_x + self.GAP_WIDTH
        diff_y_start = self.title_bar_height + 25

        pygame.draw.rect(self.screen, (30, 30, 30), (pane_old_x, self.title_bar_height, pane_w, self.height))
        pygame.draw.rect(self.screen, (22, 22, 22), (gap_x, self.title_bar_height, self.GAP_WIDTH, self.height))
        pygame.draw.rect(self.screen, (30, 30, 30), (pane_new_x, self.title_bar_height, pane_w, self.height))

        pygame.draw.line(self.screen, (55, 55, 55), (gap_x, self.title_bar_height), (gap_x, self.height))
        pygame.draw.line(self.screen, (55, 55, 55), (pane_new_x, self.title_bar_height), (pane_new_x, self.height))

        pygame.draw.rect(self.screen, (35, 35, 35), (pane_old_x, self.title_bar_height, right_w, 25))

        o_head_str = "Historical Version"
        if hasattr(self, 'current_entry') and self.current_entry:
            f_name = self.current_entry.get('file', '')
            ts_r = self.current_entry.get('timestamp', '')
            if len(ts_r) >= 16:
                y_str = ts_r[2:4]
                m_str = ts_r[5:7]
                d_str = ts_r[8:10]
                t_str = ts_r[11:16]

                try:
                    loc_lang = locale.getlocale()[0] or ""
                except:
                    loc_lang = ""

                is_us = loc_lang and "US" in loc_lang.upper()
                if is_us:
                    ts_str = f"{m_str}-{d_str}-{y_str} {t_str}"
                else:
                    ts_str = f"{d_str}-{m_str}-{y_str} {t_str}"
            else:
                ts_str = ts_r
            if f_name:
                old_sz = getattr(self, 'old_file_size_str', '0 B')
                new_sz = getattr(self, 'new_file_size_str', '0 B')
                
                o_head_str = f"Old: {f_name} [{ts_str}] ({old_sz} / {new_sz})"

        o_head = self.font_bold.render(o_head_str, True, (150, 150, 150))
        self.screen.blit(o_head, (pane_old_x + 10, self.title_bar_height + 9))

        
        t = getattr(self, 'edit_anim_t', 0.0)
        if t < 1.0:
            n_sz_str = getattr(self, 'new_file_size_str', '')
            n_sz_disp = f" ({n_sz_str})" if n_sz_str else ""
            n_head = self.font_bold.render(f"Current State{n_sz_disp}", True, (180, 180, 180))
            if t > 0.0:
                n_head.set_alpha(int(255 * (1.0 - t)))
            self.screen.blit(n_head, (pane_new_x + 10, self.title_bar_height + 9))

        
        self.context_rect = pygame.Rect(pane_old_x + right_w - 110, self.title_bar_height + 3, 100, 19)
        self.fold_out_rect = pygame.Rect(self.context_rect.left - 65, self.title_bar_height + 3, 55, 19)
        self.fold_in_rect = pygame.Rect(self.fold_out_rect.left - 60, self.title_bar_height + 3, 55, 19)
        self.edit_btn_rect = pygame.Rect(self.fold_in_rect.left - 110, self.title_bar_height + 3, 100, 19)

        if getattr(self, 'is_editing', False) and getattr(self, 'edit_show_discard_btn', False):
            self.discard_btn_rect = pygame.Rect(self.edit_btn_rect.left - 110, self.title_bar_height + 3, 100, 19)
            self.search_rect = pygame.Rect(self.discard_btn_rect.left - 210, self.title_bar_height + 3, 200, 19)
        else:
            self.discard_btn_rect = pygame.Rect(0, 0, 0, 0)
            self.search_rect = pygame.Rect(self.edit_btn_rect.left - 210, self.title_bar_height + 3, 200, 19)

        self.help_btn_rect = pygame.Rect(self.search_rect.left - 30, self.title_bar_height + 3, 20, 19)

        
        hover_edit = self.edit_btn_rect.collidepoint(mx, my)
        click_edit = hover_edit and is_pressed
        flash_val = getattr(self, 'edit_save_btn_flash', 0.0)

        if getattr(self, 'is_editing', False):
            
            base_r = 110 if hover_edit else 80
            base_g = 65 if hover_edit else 45
            base_b = 65 if hover_edit else 45
            if click_edit:
                base_r -= 20; base_g -= 10; base_b -= 10
            btn_label = "Save Changes"
            eb_surf = self.font.render(btn_label, True, (255, 200, 200) if flash_val > 0.0 else (240, 180, 180))

            r_col = min(255, max(0, base_r + int(120 * flash_val)))
            g_col = max(0, base_g - int(25 * flash_val))
            b_col = max(0, base_b - int(25 * flash_val))

            border_col = (130 + int(90 * flash_val), 80, 80)
        else:
            
            base_r = 75 if hover_edit else 55
            base_g = 75 if hover_edit else 55
            base_b = 80 if hover_edit else 60
            if click_edit:
                base_r = 45; base_g = 45; base_b = 50
            btn_label = "Edit File"
            eb_surf = self.font.render(btn_label, True, (220, 220, 220))

            r_col = base_r
            g_col = base_g
            b_col = base_b

            border_col = (80, 80, 90) if click_edit else (100, 100, 110)

        pygame.draw.rect(self.screen, (r_col, g_col, b_col), self.edit_btn_rect, border_radius=3)
        pygame.draw.rect(self.screen, border_col, self.edit_btn_rect, 1, border_radius=3)
        oy_edit = 1 if click_edit else 0
        self.screen.blit(eb_surf, (self.edit_btn_rect.centerx - eb_surf.get_width()//2, self.edit_btn_rect.centery - eb_surf.get_height()//2 + 1 + oy_edit))

        
        if getattr(self, 'is_editing', False) and getattr(self, 'edit_show_discard_btn', False):
            hover_disc = self.discard_btn_rect.collidepoint(mx, my)
            click_disc = hover_disc and is_pressed

            base_db_r = 60 if hover_disc else 40
            base_db_g = 70 if hover_disc else 50
            base_db_b = 110 if hover_disc else 80
            if click_disc:
                base_db_r -= 10; base_db_g -= 15; base_db_b -= 20

            db_r = max(0, base_db_r - int(20 * flash_val))
            db_g = max(0, base_db_g - int(20 * flash_val))
            db_b = min(255, base_db_b + int(120 * flash_val))

            pygame.draw.rect(self.screen, (db_r, db_g, db_b), self.discard_btn_rect, border_radius=3)
            pygame.draw.rect(self.screen, (60, 80, 140) if click_disc else (80, 100, 160 + int(90 * flash_val)), self.discard_btn_rect, 1, border_radius=3)

            db_surf = self.font.render("Discard Changes", True, (255, 255, 255) if flash_val > 0.0 else (180, 200, 240))
            oy_disc = 1 if click_disc else 0
            self.screen.blit(db_surf, (self.discard_btn_rect.centerx - db_surf.get_width()//2, self.discard_btn_rect.centery - db_surf.get_height()//2 + 1 + oy_disc))

        
        disp_text = getattr(self, 'search_text', '')
        if not disp_text and not getattr(self, 'search_active', False):
            disp_text = "Search..."

        hover_search = self.search_rect.collidepoint(mx, my) or getattr(self, 'search_active', False)

        search_bg = (80, 80, 80) if hover_search else (40, 40, 45)
        pygame.draw.rect(self.screen, search_bg, self.search_rect, border_radius=3)
        pygame.draw.rect(self.screen, (100, 100, 110), self.search_rect, 1, border_radius=3)

        max_w = self.search_rect.width - 10
        if getattr(self, 'search_text', ''):
            if getattr(self, 'search_results', []):
                cnt_str = f"{self.search_current_idx + 1}/{len(self.search_results)}"
            else:
                cnt_str = "0/0"
            cnt_w = self.font.size(cnt_str)[0]
            max_w -= (cnt_w + 10)

        txt_clip_rect = pygame.Rect(self.search_rect.x + 5, self.search_rect.y, max_w, self.search_rect.height)

        c_pos = getattr(self, 'search_cursor_pos', len(disp_text))
        if c_pos > len(disp_text): c_pos = len(disp_text)
        px_w = self.font.size(disp_text[:c_pos])[0]

        scroll_x = getattr(self, '_search_scroll_x', 0)
        if px_w - scroll_x > max_w - 5:
            scroll_x = px_w - max_w + 5
        elif px_w - scroll_x < 0:
            scroll_x = max(0, px_w - 20)
        self._search_scroll_x = scroll_x

        self.screen.set_clip(txt_clip_rect)

        
        if getattr(self, 'search_active', False) and getattr(self, 'search_sel_start', 0) != getattr(self, 'search_sel_end', 0):
            s_idx = min(self.search_sel_start, self.search_sel_end)
            e_idx = max(self.search_sel_start, self.search_sel_end)
            s_px, _ = self.font.size(disp_text[:s_idx])
            sel_w, _ = self.font.size(disp_text[s_idx:e_idx])

            sel_rect = pygame.Rect(txt_clip_rect.x - scroll_x + s_px, self.search_rect.y + 2, sel_w, self.search_rect.height - 4)
            pygame.draw.rect(self.screen, (40, 80, 140), sel_rect)

        
        s_surf = self.font.render(disp_text, True, (200, 200, 200) if getattr(self, 'search_text', '') or getattr(self, 'search_active', False) else (120, 120, 120))
        self.screen.blit(s_surf, (txt_clip_rect.x - scroll_x, self.search_rect.centery - s_surf.get_height()//2 + 1))

        
        if getattr(self, 'search_active', False) and getattr(self, 'search_sel_start', 0) == getattr(self, 'search_sel_end', 0) and (time.time() % 0.8 < 0.4):
            cx = txt_clip_rect.x - scroll_x + px_w
            if txt_clip_rect.left <= cx <= txt_clip_rect.right:
                pygame.draw.line(self.screen, (255, 255, 255), (cx, self.search_rect.y + 4), (cx, self.search_rect.bottom - 4), 2)

        self.screen.set_clip(None)

        
        if getattr(self, 'search_text', ''):
            if getattr(self, 'search_results', []):
                cnt_str = f"{self.search_current_idx + 1}/{len(self.search_results)}"

                c_color = (150, 150, 150)
            else:
                cnt_str = "0/0"

                c_color = (255, 100, 100)
            c_surf = self.font.render(cnt_str, True, c_color)
            self.screen.blit(c_surf, (self.search_rect.right - c_surf.get_width() - 5, self.search_rect.centery - c_surf.get_height()//2 + 1))

        
        
        hover_help = self.help_btn_rect.collidepoint(mx, my)
        click_help = hover_help and is_pressed
        pygame.draw.rect(self.screen, (40, 40, 45) if click_help else ((70, 70, 75) if hover_help else (50, 50, 55)), self.help_btn_rect, border_radius=3)
        pygame.draw.rect(self.screen, (90, 90, 100) if click_help else ((110, 110, 120) if hover_help else (90, 90, 100)), self.help_btn_rect, 1, border_radius=3)
        h_surf = self.font_bold.render("?", True, (200, 200, 200))
        oy_help = 1 if click_help else 0
        self.screen.blit(h_surf, (self.help_btn_rect.centerx - h_surf.get_width()//2, self.help_btn_rect.centery - h_surf.get_height()//2 + 1 + oy_help))

        
        hover_fold_in = self.fold_in_rect.collidepoint(mx, my)
        click_fold_in = hover_fold_in and is_pressed
        pygame.draw.rect(self.screen, (40, 40, 45) if click_fold_in else ((70, 70, 75) if hover_fold_in else (50, 50, 55)), self.fold_in_rect, border_radius=3)
        pygame.draw.rect(self.screen, (90, 90, 100) if click_fold_in else ((110, 110, 120) if hover_fold_in else (90, 90, 100)), self.fold_in_rect, 1, border_radius=3)
        f_minus = self.font.render("-   FOLD", True, (200, 200, 200))
        oy_fold_in = 1 if click_fold_in else 0
        self.screen.blit(f_minus, (self.fold_in_rect.centerx - f_minus.get_width()//2, self.fold_in_rect.centery - f_minus.get_height()//2 + 1 + oy_fold_in))

        
        hover_fold_out = self.fold_out_rect.collidepoint(mx, my)
        click_fold_out = hover_fold_out and is_pressed

        pygame.draw.rect(self.screen, (40, 40, 45) if click_fold_out else ((70, 70, 75) if hover_fold_out else (50, 50, 55)), self.fold_out_rect, border_radius=3)
        pygame.draw.rect(self.screen, (90, 90, 100) if click_fold_out else ((110, 110, 120) if hover_fold_out else (90, 90, 100)), self.fold_out_rect, 1, border_radius=3)

        
        text_normal = self.font.render("UNFOLD ", True, (200, 200, 200))
        plus_size = int(self.font.get_height() * 1.80)
        font_plus = pygame.font.Font(None, plus_size)
        text_plus = font_plus.render("+", True, (200, 200, 200))

        
        total_width = text_normal.get_width() + text_plus.get_width()
        center_x = self.fold_out_rect.centerx - total_width // 2
        center_y = self.fold_out_rect.centery
        oy_fold_out = 1 if click_fold_out else 0
        self.screen.blit(text_normal, (center_x, center_y - text_normal.get_height()//2 + 1 + oy_fold_out))
        
        self.screen.blit(text_plus, (center_x + text_normal.get_width(),
                                     center_y - text_plus.get_height()//2 + 1 + oy_fold_out - 2))

        
        hover_ctx = self.context_rect.collidepoint(mx, my)
        click_ctx = hover_ctx and is_pressed

        ctx_bg = (60, 80, 120) if getattr(self, 'in_context_view', False) else ((40, 40, 45) if click_ctx else ((70, 70, 75) if hover_ctx else (50, 50, 55)))

        ctx_border = (100, 140, 200) if getattr(self, 'in_context_view', False) else ((90, 90, 100) if click_ctx else ((110, 110, 120) if hover_ctx else (90, 90, 100)))
        pygame.draw.rect(self.screen, ctx_bg, getattr(self, 'context_rect', pygame.Rect(0,0,0,0)), border_radius=3)
        pygame.draw.rect(self.screen, ctx_border, getattr(self, 'context_rect', pygame.Rect(0,0,0,0)), 1, border_radius=3)
        ctx_surf = self.font.render(" Context", True, (220, 230, 255) if getattr(self, 'in_context_view', False) else (200, 200, 200))
        oy_ctx = 1 if click_ctx else 0
        self.screen.blit(ctx_surf, (getattr(self, 'context_rect', pygame.Rect(0,0,0,0)).centerx - ctx_surf.get_width()//2, getattr(self, 'context_rect', pygame.Rect(0,0,0,0)).centery - ctx_surf.get_height()//2 + 1 + oy_ctx))

        
        if getattr(self, 'in_context_view', False):
            pygame.draw.rect(self.screen, (22, 22, 25), (pane_old_x, diff_y_start, right_w, self.height - diff_y_start))

            ctx_title = self.font_bold.render("Substantial Changes Summary (Max 4 lines shown per change)", True, (200, 220, 200))
            self.screen.blit(ctx_title, (pane_old_x + 20, diff_y_start + 15))

            self.context_cards = []
            card_y = diff_y_start + 45

            clip_rect = pygame.Rect(pane_old_x, diff_y_start + 40, right_w, max(1, self.height - diff_y_start - 50))
            self.screen.set_clip(clip_rect)

            for chg in getattr(self, 'substantial_changes', []):
                num_old = len(chg['old_lines'])
                num_new = len(chg['new_lines'])
                max_lines_in_card = max(num_old, num_new)
                card_h = 32 + max_lines_in_card * self.line_height + 12

                render_y = card_y - getattr(self, 'scroll_context', 0)
                card_rect = pygame.Rect(pane_old_x + 20, render_y, right_w - 40, card_h)

                self.context_cards.append({
                    'rect': card_rect,
                    'target': chg['visual_target']
                })
                is_card_hovered = card_rect.collidepoint(mx, my)

                bg_col = (42, 45, 52) if is_card_hovered else (32, 34, 38)

                border_col = (110, 160, 130) if is_card_hovered else (60, 70, 65)
                pygame.draw.rect(self.screen, bg_col, card_rect, border_radius=5)
                pygame.draw.rect(self.screen, border_col, card_rect, 1, border_radius=5)

                f_surf = self.font_bold.render(f"{chg['func_name']}", True, (230, 210, 130))
                self.screen.blit(f_surf, (card_rect.x + 15, card_rect.y + 8))

                col_w = max(1, (card_rect.width - 30) // 2)

                curr_y_old = card_rect.y + 32
                for text, ln, _ in chg['old_lines']:
                    line_rect = pygame.Rect(card_rect.x + 10, curr_y_old, col_w, self.line_height)
                    pygame.draw.rect(self.screen, (75, 45, 35), line_rect)
                    ln_str = f"{ln}: " if ln else ""
                    t_surf = self.font.render(f"- {ln_str}{text}", True, (240, 185, 185))

                    txt_surf_clipped = pygame.Surface((max(1, col_w - 10), max(1, self.line_height)), pygame.SRCALPHA)
                    txt_surf_clipped.blit(t_surf, (0, 0))
                    self.screen.blit(txt_surf_clipped, (line_rect.x + 5, line_rect.y + 2))
                    curr_y_old += self.line_height

                curr_y_new = card_rect.y + 32
                for text, ln, _ in chg['new_lines']:
                    line_rect = pygame.Rect(card_rect.x + 20 + col_w, curr_y_new, col_w, self.line_height)
                    pygame.draw.rect(self.screen, (50, 65, 40), line_rect)
                    ln_str = f"{ln}: " if ln else ""
                    t_surf = self.font.render(f"+ {ln_str}{text}", True, (185, 240, 185))

                    txt_surf_clipped = pygame.Surface((max(1, col_w - 10), max(1, self.line_height)), pygame.SRCALPHA)
                    txt_surf_clipped.blit(t_surf, (0, 0))
                    self.screen.blit(txt_surf_clipped, (line_rect.x + 5, line_rect.y + 2))
                    curr_y_new += self.line_height
                card_y += card_h + 15
            self.screen.set_clip(None)
        else:
            
            clip_rect = pygame.Rect(pane_old_x, diff_y_start, self.width - pane_old_x, max(1, self.height - diff_y_start))
            self.screen.set_clip(clip_rect)

            max_lines = (self.height - diff_y_start) // self.line_height
            for p_idx, pane in enumerate([self.old_lines, self.new_lines]):
                base_x = pane_old_x if p_idx == 0 else pane_new_x
                pane_name = "old" if p_idx == 0 else "new"

                if p_idx == 1 and getattr(self, 'edit_anim_t', 0.0) > 0.0:
                    t = self.edit_anim_t
                    editor_x_end = pane_old_x + 35
                    curr_x = pane_new_x - (pane_new_x - editor_x_end) * t
                    curr_w = right_w - (curr_x - pane_old_x) - 20

                    
                    dim_surf = pygame.Surface((pane_w, max(1, self.height - diff_y_start)), pygame.SRCALPHA)
                    dim_surf.fill((0, 0, 0, int(230 * t)))
                    self.screen.blit(dim_surf, (pane_old_x, diff_y_start))

                    self._draw_editor_pane(curr_x, diff_y_start, curr_w, self.height - diff_y_start - 5)

                    
                    errors = getattr(self, 'edit_linter_errors', [])
                    current_error = next((msg for r, msg in errors if r == self.edit_cursor_row), None)
                    if not current_error and errors:
                        current_error = f"Line {errors[0][0] + 1}: {errors[0][1]}"

                    if current_error:
                        err_surf = self.font_bold.render(f"⚠ {current_error}", True, (240, 80, 80))
                        err_surf.set_alpha(int(255 * t))
                        self.screen.blit(err_surf, (curr_x + 10, self.height - 22))

                    
                    n_head_str = "EDITING MODE ACTIVE"

                    n_head_color = (int(255 * t), int(100 * t), int(100 * t))
                    n_head = self.font_bold.render(n_head_str, True, n_head_color)
                    n_head_x = curr_x + curr_w - n_head.get_width() - 10
                    self.screen.blit(n_head, (n_head_x, self.height - 22))

                    continue

                scroll_r_float = getattr(self, 'scroll_right_float', float(self.scroll_right))
                start_v_idx = int(scroll_r_float)

                fractional_offset = (scroll_r_float - start_v_idx) * self.line_height

                for v_idx in range(start_v_idx, min(len(self.visible_indices), start_v_idx + max_lines + 2)):
                    i = self.visible_indices[v_idx]
                    text, status, ln = pane[i]
                    y = diff_y_start + int((v_idx - start_v_idx) * self.line_height - fractional_offset)

                    bg_color = (30, 30, 30)

                    fg_color = (200, 200, 200)
                    if status == "deleted": bg_color = (75, 45, 35)
                    elif status == "added": bg_color = (55, 65, 40)
                    elif status in ("blank_del", "blank_add"): bg_color = (35, 30, 30)
                    elif status == "header":
                        fg_color = (100, 150, 200)

                        bg_color = (25, 25, 35)
                    is_selected = False
                    for (r1, r2) in getattr(self, 'extra_selections', {}).get(pane_name, []):
                        if r1 <= i <= r2:
                            is_selected = True
                            break

                    if not is_selected and (getattr(self, 'is_selecting', False) or (getattr(self, 'selection_start', None) is not None and getattr(self, 'selection_end', None) is not None)):
                        if getattr(self, 'selecting_pane', None) == pane_name:
                            r1 = min(self.selection_start, self.selection_end)
                            r2 = max(self.selection_start, self.selection_end)
                            if r1 <= i <= r2:
                                is_selected = True

                    
                    is_active_line = (i == getattr(self, 'selection_start', None) and pane_name == getattr(self, 'selecting_pane', None))

                    is_hovered_line = (i == getattr(self, 'hovered_line_idx', None) and pane_name == getattr(self, 'hovered_line_pane', None))
                    is_func_start = i in getattr(self, 'code_blocks', {})

                    if is_selected:
                        r, g, b = bg_color

                        bg_color = (min(255, r + 30), min(255, g + 40), min(255, b + 75))
                    elif is_active_line or is_hovered_line:
                        r, g, b = bg_color

                        bg_color = (min(255, r + 15), min(255, g + 15), min(255, b + 15))
                    elif is_func_start and status == "context":
                        r, g, b = bg_color

                        bg_color = (min(255, r + 5), min(255, g + 10), min(255, b + 20))
                    pygame.draw.rect(self.screen, bg_color, (base_x, y, pane_w, self.line_height))
                    if i in getattr(self, 'code_blocks', {}):
                        depth = getattr(self, 'block_depths', {}).get(i, 0)
                        box_x = base_x + 45 + (depth * 10)
                        box_rect = pygame.Rect(box_x, y + (self.line_height // 2) - 4, 9, 9)
                        is_folded = i in self.folded_blocks
                        pygame.draw.rect(self.screen, (150, 150, 150), box_rect, 1)
                        pygame.draw.line(self.screen, (200, 200, 200), (box_rect.left + 2, box_rect.centery), (box_rect.right - 3, box_rect.centery))
                        if is_folded:
                            pygame.draw.line(self.screen, (200, 200, 200), (box_rect.centerx, box_rect.top + 2), (box_rect.centerx, box_rect.bottom - 3))

                    if status not in ("blank_del", "blank_add"):
                        if status == "header":
                            t_surf = self.font.render(text.replace('\t', '    '), True, fg_color)
                        else:
                            line_fg = (235, 195, 115) if is_func_start and status == "context" else fg_color
                            t_surf = self._render_syntax_line(text, line_fg)

                        ln_color = (240, 240, 240) if is_selected else (100, 100, 100)

                        if pane_name == "old":
                            if ln is not None:
                                ln_surf = self.font.render(str(ln), True, ln_color)
                                self.screen.blit(ln_surf, (base_x + 5, y + 2))
                            text_x = base_x + 60
                            txt_clip = pygame.Rect(0, 0, max(1, pane_w - 65), max(1, self.line_height))
                        else:
                            text_x = base_x + 60
                            if ln is not None:
                                ln_surf = self.font.render(str(ln), True, ln_color)
                                self.screen.blit(ln_surf, (base_x + 5, y + 2))
                            txt_clip = pygame.Rect(0, 0, max(1, pane_w - 65), max(1, self.line_height))

                        t_surf_clipped = pygame.Surface(txt_clip.size, pygame.SRCALPHA)
                        offset_x = -self.scroll_right_x if pane_name == "new" else 0
                        t_surf_clipped.blit(t_surf, (offset_x, 0))

                        q = getattr(self, 'search_text', '').lower()
                        if q and len(q) >= 1:
                            match_idx = text.lower().find(q)
                            if match_idx != -1:
                                prefix = text[:match_idx].replace('\t', '    ')
                                match_str = text[match_idx:match_idx+len(q)].replace('\t', '    ')
                                px_w, _ = self.font.size(prefix)
                                m_w = max(1, self.font.size(match_str)[0])

                                hl_surf = pygame.Surface((m_w, max(1, self.line_height)), pygame.SRCALPHA)

                                is_active_match = False
                                if getattr(self, 'search_results', []) and getattr(self, 'search_current_idx', -1) >= 0:
                                    if i == self.search_results[self.search_current_idx]:
                                        is_active_match = True

                                if is_active_match:
                                    hl_surf.fill((255, 120, 0, 255))
                                    pygame.draw.rect(hl_surf, (255, 200, 0), hl_surf.get_rect(), 1)
                                else:
                                    hl_surf.fill((200, 200, 0, 255))

                                match_text_surf = self.font.render(match_str, True, (20, 20, 25))
                                hl_surf.blit(match_text_surf, (0, 0))

                                t_surf_clipped.blit(hl_surf, (px_w + offset_x, 0))
                        self.screen.blit(t_surf_clipped, (text_x, y + 2))

            
            if not getattr(self, 'is_editing', False) and getattr(self, 'edit_anim_t', 0.0) == 0.0:
                for idx, block in enumerate(self.diff_blocks):
                    if block['state'] != 'diff': continue

                    active_scs = [sc for sc in block.get('sub_chunks', []) if sc['state'] != 'merged']
                    if not active_scs: continue

                    first_unmerged = active_scs[0]
                    has_big_arrow = sum(1 for sc in active_scs if sc['num_dels'] > 0) > 1

                    for sc_idx, sc in enumerate(block.get('sub_chunks', [])):
                        if sc['state'] != 'diff': continue

                        v_start = -1
                        for i in range(sc['start'], sc['end'] + 1):
                            if self.actual_to_visual[i] != -1:
                                v_start = self.actual_to_visual[i]
                                break

                        v_end = -1
                        for i in range(sc['end'], sc['start'] - 1, -1):
                            if self.actual_to_visual[i] != -1:
                                v_end = self.actual_to_visual[i]
                                break

                        if v_start == -1 or v_end == -1:
                            continue

                        
                        y_top = diff_y_start + int((v_start - scroll_r_float) * self.line_height)
                        y_bot = diff_y_start + int((v_end - scroll_r_float + 1) * self.line_height)

                        if y_bot < diff_y_start or y_top > self.height:
                            continue

                        num_dels = sum(1 for i in range(sc['start'], sc['end']+1) if self.actual_to_visual[i] != -1 and self.old_lines[i][1] == 'deleted')
                        num_adds = sum(1 for i in range(sc['start'], sc['end']+1) if self.actual_to_visual[i] != -1 and self.new_lines[i][1] == 'added')

                        if num_dels == 0 or num_adds == 0:
                            gap_rect = pygame.Rect(gap_x, y_top, self.GAP_WIDTH, max(1, y_bot - y_top))
                            pygame.draw.rect(self.screen, (60, 40, 35), gap_rect)
                            pygame.draw.rect(self.screen, (90, 60, 50), gap_rect, 1)
                        else:
                            left_bot = y_top + (num_dels * self.line_height)
                            right_bot = y_top + (num_adds * self.line_height)

                            poly_pts = [
                                (gap_x, y_top),
                                (gap_x + self.GAP_WIDTH, y_top),
                                (gap_x + self.GAP_WIDTH, right_bot),
                                (gap_x, left_bot)
                            ]
                            pygame.draw.polygon(self.screen, (60, 40, 35), poly_pts)
                            pygame.draw.polygon(self.screen, (90, 60, 50), poly_pts, 1)
                        btn_y = y_top + 5

                        is_first_unmerged = (sc == first_unmerged)
                        if is_first_unmerged and has_big_arrow:
                            big_arrow_rect = pygame.Rect(gap_x + 4, y_top + 2, self.GAP_WIDTH - 8, 22)
                            hover_big = big_arrow_rect.collidepoint(mx, my)
                            click_big = hover_big and is_pressed
                            pygame.draw.rect(self.screen, (40, 100, 50) if click_big else ((60, 150, 70) if hover_big else (50, 120, 60)), big_arrow_rect, border_radius=3)
                            pygame.draw.rect(self.screen, (80, 150, 90) if click_big else ((100, 200, 110) if hover_big else (90, 180, 100)), big_arrow_rect, 1, border_radius=3)

                            ba_surf = self.font_bold.render("ALL →", True, (255, 255, 255))
                            oy_big = 1 if click_big else 0
                            self.screen.blit(ba_surf, (big_arrow_rect.centerx - ba_surf.get_width()//2, big_arrow_rect.centery - ba_surf.get_height()//2 + 1 + oy_big))

                            btn_y += 26

                        if num_dels > 0:
                            btn_restore_rect = pygame.Rect(gap_x + 4, btn_y, 22, 22)
                            hover_r = btn_restore_rect.collidepoint(mx, my)
                            click_r = hover_r and is_pressed
                            pygame.draw.rect(self.screen, (60, 45, 40) if click_r else ((120, 90, 80) if hover_r else (80, 60, 50)), btn_restore_rect, border_radius=3)
                            r_arrow = self.font_bold.render("→", True, (255, 255, 255))
                            oy_r = 1 if click_r else 0
                            self.screen.blit(r_arrow, (btn_restore_rect.centerx - r_arrow.get_width()//2, btn_restore_rect.centery - r_arrow.get_height()//2 + 1 + oy_r))

                        if num_adds > 0:
                            btn_delete_rect = pygame.Rect(gap_x + self.GAP_WIDTH - 26, btn_y, 22, 22)
                            hover_l = btn_delete_rect.collidepoint(mx, my)
                            click_l = hover_l and is_pressed
                            pygame.draw.rect(self.screen, (90, 35, 30) if click_l else ((180, 70, 60) if hover_l else (120, 50, 45)), btn_delete_rect, border_radius=3)
                            l_cross = self.font_bold.render("×", True, (255, 255, 255))
                            oy_l = 1 if click_l else 0
                            self.screen.blit(l_cross, (btn_delete_rect.centerx - l_cross.get_width()//2, btn_delete_rect.centery - l_cross.get_height()//2 + oy_l))

            
            minimap_x = self.width - self.minimap_width
            map_h = self.height - diff_y_start

            is_ed = getattr(self, 'is_editing', False) or getattr(self, 'edit_anim_t', 0.0) > 0.0
            if is_ed:
                total_lines = len(getattr(self, 'edit_visible_indices', []))
                scroll_val = getattr(self, 'edit_scroll_y_float', float(self.edit_scroll_y))

                max_lines = (self.height - diff_y_start - 5) // self.line_height
            else:
                total_lines = len(self.visible_indices)
                scroll_val = getattr(self, 'scroll_right_float', float(self.scroll_right))

                max_lines = (self.height - diff_y_start) // self.line_height

            pygame.draw.rect(self.screen, (18, 18, 18), (minimap_x, diff_y_start, self.minimap_width, max(1, map_h)))
            pygame.draw.rect(self.screen, (35, 35, 35), (minimap_x, self.title_bar_height, self.minimap_width, 25))
            pygame.draw.line(self.screen, (55, 55, 55), (minimap_x, self.title_bar_height), (minimap_x, self.height))

            if total_lines > 0:
                scale_y = map_h / total_lines
                if not is_ed:
                    for block in self.diff_blocks:
                        if block['state'] != 'diff': continue

                        for sc in block.get('sub_chunks', []):
                            if sc['state'] != 'diff': continue

                            v_start = -1
                            for i in range(sc['start'], sc['end'] + 1):
                                if self.actual_to_visual[i] != -1:
                                    v_start = self.actual_to_visual[i]
                                    break

                            v_end = -1
                            for i in range(sc['end'], sc['start'] - 1, -1):
                                if self.actual_to_visual[i] != -1:
                                    v_end = self.actual_to_visual[i]
                                    break

                            if v_start == -1 or v_end == -1: continue

                            m_y1 = diff_y_start + (v_start * scale_y)
                            m_h = max(2, (v_end - v_start + 1) * scale_y)

                            if sc['num_adds'] > 0 and sc['num_dels'] == 0:
                                map_col = (90, 140, 80)
                            elif sc['num_dels'] > 0 and sc['num_adds'] == 0:
                                map_col = (160, 60, 50)
                            else:
                                map_col = (140, 110, 60)

                            pygame.draw.rect(self.screen, map_col, (minimap_x + 2, m_y1, self.minimap_width - 4, m_h))

                vp_y = diff_y_start + (scroll_val * scale_y)
                vp_h = max(10, max_lines * scale_y)
                vp_surf = pygame.Surface((self.minimap_width, vp_h), pygame.SRCALPHA)
                vp_surf.fill((255, 255, 255, 45))
                self.screen.blit(vp_surf, (minimap_x, vp_y))
                pygame.draw.rect(self.screen, (200, 200, 200), (minimap_x, vp_y, self.minimap_width, vp_h), 1)

            
            if not getattr(self, 'is_editing', False) and not getattr(self, 'in_context_view', False):
                visible_w = pane_w - 65
                max_scroll_x = max(0, getattr(self, 'max_right_width', 0) - visible_w + 50)
                if max_scroll_x > 0:
                    scrollbar_h = 12
                    scrollbar_rect = pygame.Rect(pane_new_x + 60, self.height - scrollbar_h - 5, pane_w - 65, scrollbar_h)
                    ratio = visible_w / max(1, getattr(self, 'max_right_width', 0))
                    thumb_w = min(50, max(15, int(scrollbar_rect.width * ratio)))
                    max_thumb_travel = scrollbar_rect.width - thumb_w
                    thumb_x = scrollbar_rect.x + int((self.scroll_right_x / max_scroll_x) * max_thumb_travel)

                    
                    track_surf = pygame.Surface((scrollbar_rect.width, scrollbar_rect.height), pygame.SRCALPHA)
                    track_surf.fill((18, 18, 18, 51))
                    self.screen.blit(track_surf, (scrollbar_rect.x, scrollbar_rect.y))

                    
                    thumb_surf = pygame.Surface((thumb_w, scrollbar_rect.height), pygame.SRCALPHA)
                    thumb_surf.fill((255, 255, 255, 51))
                    pygame.draw.rect(thumb_surf, (200, 200, 200, 51), (0, 0, thumb_w, scrollbar_rect.height), 1)
                    self.screen.blit(thumb_surf, (thumb_x, scrollbar_rect.y))

            self.screen.set_clip(None)

        
        cm = getattr(self, 'context_menu', None)
        if cm:
            
            pygame.draw.rect(self.screen, (38, 38, 43), cm['rect'], border_radius=4)
            pygame.draw.rect(self.screen, (85, 85, 95), cm['rect'], 1, border_radius=4)

            
            for opt in cm['options']:
                opt_rect = opt['rect']
                is_hovered = opt_rect.collidepoint(mx, my)

                if is_hovered:
                    pygame.draw.rect(self.screen, (50, 75, 125), opt_rect, border_radius=3)

                text_surf = self.font.render(opt['label'], True, (235, 235, 235))
                text_y = opt_rect.y + (opt_rect.height - text_surf.get_height()) // 2
                self.screen.blit(text_surf, (opt_rect.x + 12, text_y))

        if getattr(self, 'show_commands_help', False):
            self._draw_commands_help_overlay(mx, my)

        if getattr(self, '_linter_tooltip', None):
            mx, my, err_msg = self._linter_tooltip
            err_surf = self.font.render(err_msg, True, (255, 200, 200))
            tw = err_surf.get_width() + 20
            th = err_surf.get_height() + 10

            tx = mx + 15
            ty = my + 15
            if tx + tw > self.width: tx = self.width - tw - 5
            if ty + th > self.height: ty = self.height - th - 5

            tt_rect = pygame.Rect(tx, ty, tw, th)
            pygame.draw.rect(self.screen, (50, 20, 20), tt_rect, border_radius=4)
            pygame.draw.rect(self.screen, (200, 60, 60), tt_rect, 1, border_radius=4)
            self.screen.blit(err_surf, (tx + 10, ty + 5))

    def _draw_editor_help_overlay(self, x, y, w):
        help_lines = [
            "=== Editor Keyboard Shortcuts ===",
            "",
            " Navigation:",
            "  • Arrows / Home / End : Move cursor",
            "  • Ctrl + Left/Right   : Word jump",
            "  • Mouse Click/Drag    : Place cursor / Select",
            "",
            " Selection & Editing:",
            "  • Shift + Arrows/Click: Highlight text",
            "  • Ctrl + A            : Select All",
            "  • Ctrl + F            : Find",
            "  • Ctrl + H            : Find and Replace",
            "  • Ctrl + C / X / V    : Copy / Cut / Paste",
            "  • Tab / Shift+Tab     : Indent / Dedent blocks",
            "  • Enter               : Newline & auto-indent",
            "",
            " History & Tools:",
            "  • Ctrl + Z            : Undo",
            "  • Ctrl + Y (or Sh+Z)  : Redo",
            "  • Fold Code (Top Bar) : Fold unchanged code",
            "",
            "  Press ESC to Save & Exit Editor."
        ]

        h = len(help_lines) * 20 + 20
        box_w = 340
        box_x = x + w - box_w - 20
        box_y = y + 5

        overlay = pygame.Surface((box_w, h), pygame.SRCALPHA)
        overlay.fill((20, 25, 30, 240))
        pygame.draw.rect(overlay, (80, 120, 160, 255), overlay.get_rect(), 2, border_radius=5)

        for i, line in enumerate(help_lines):
            color = (255, 255, 255) if line.startswith("===") else (200, 220, 240)
            if "ESC" in line: color = (255, 150, 150)
            t_surf = self.font.render(line, True, color)
            overlay.blit(t_surf, (15, 10 + i * 20))

        self.screen.blit(overlay, (box_x, box_y))

    def _run_linter(self, force_structure_rebuild=False):
        """Prepares fast layout indices instantly, and queues the heavy syntax compilation check."""
        num_lines = len(self.edit_lines)
        if force_structure_rebuild or not hasattr(self, '_last_edit_lines_len') or num_lines != self._last_edit_lines_len:
            self._analyze_edit_code_blocks()
            self._build_edit_visible_indices()
            self._last_edit_lines_len = num_lines
            self.edit_structure_pending = False
        else:
            
            self.edit_structure_pending = True
            self.edit_structure_request_time = time.time()

        
        self.edit_linter_pending = True
        self.edit_linter_request_time = time.time()

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

    def _enter_edit_mode(self):
        if not hasattr(self, 'active_file_path') or not self.active_file_path or not os.path.exists(self.active_file_path):
            self._log("Cannot enter edit mode: no valid active file path.")
            return

        self.context_menu = None
        self.in_context_view = False
        text = self._read_file_text(self.active_file_path)
        self.edit_lines = text.splitlines() if text else [""]
        
        self.edit_lines.extend(["", "", "", ""])
        self.is_editing = True

        self.edit_undo_stack = []

        self.edit_redo_stack = []
        self.edit_selection_start = None
        self.edit_is_dragging = False

        self._analyze_edit_code_blocks()
        self.edit_folded_blocks = set()

        
        if hasattr(self, 'folded_blocks') and self.folded_blocks:
            for i in self.folded_blocks:
                if i < len(self.new_lines):
                    _, _, ln = self.new_lines[i]
                    if ln is not None:
                        edit_idx = ln - 1
                        if edit_idx in self.edit_code_blocks:
                            self.edit_folded_blocks.add(edit_idx)
                        else:
                            for delta in (1, -1, 2, -2):
                                if (edit_idx + delta) in self.edit_code_blocks:
                                    self.edit_folded_blocks.add(edit_idx + delta)
                                    break

        self._build_edit_visible_indices()
        self._last_edit_lines_len = len(self.edit_lines)

        start_ln = 1
        if self.visible_indices and self.scroll_right < len(self.visible_indices):
            v_i = self.visible_indices[self.scroll_right]
            if v_i < len(self.new_lines):
                _, _, ln = self.new_lines[v_i]
                
                if ln is None:
                    for scan_v_i in range(self.scroll_right, len(self.visible_indices)):
                        real_i = self.visible_indices[scan_v_i]
                        if real_i < len(self.new_lines):
                            _, _, tmp_ln = self.new_lines[real_i]
                            if tmp_ln is not None:
                                ln = tmp_ln
                                break
                if ln is not None:
                    start_ln = ln

        cursor_ln = None
        if getattr(self, 'selection_start', None) is not None:
            sel_pane = getattr(self, 'selecting_pane', 'new')
            lines_source = self.new_lines if sel_pane == 'new' else self.old_lines
            if self.selection_start < len(lines_source):
                _, _, ln = lines_source[self.selection_start]
                if ln is None:
                    for scan_i in range(self.selection_start, len(lines_source)):
                        _, _, tmp_ln = lines_source[scan_i]
                        if tmp_ln is not None:
                            ln = tmp_ln
                            break
                if ln is not None:
                    cursor_ln = ln

        if cursor_ln is None:
            cursor_ln = start_ln

        
        target_scroll_idx = max(0, start_ln - 1)
        if target_scroll_idx < len(self.edit_actual_to_visual):
            v_idx = self.edit_actual_to_visual[target_scroll_idx]
            if v_idx != -1:
                self.edit_scroll_y = v_idx
            else:
                for r in range(target_scroll_idx, -1, -1):
                    if r < len(self.edit_actual_to_visual) and self.edit_actual_to_visual[r] != -1:
                        self.edit_scroll_y = self.edit_actual_to_visual[r]
                        break
                else:
                    self.edit_scroll_y = 0
        else:
            self.edit_scroll_y = 0

        self.edit_target_scroll_y = self.edit_scroll_y
        self.edit_scroll_y_float = float(self.edit_scroll_y)

        self.edit_cursor_row = max(0, cursor_ln - 1)
        self.edit_cursor_col = 0

        
        self.edit_scroll_x = getattr(self, 'scroll_right_x', 0)

        self.edit_show_discard_btn = True

        self._run_linter(force_structure_rebuild=True)
        pygame.key.set_repeat(300, 60)
        self._update_search(jump=False)

    def _exit_edit_mode(self):
        if hasattr(self, 'active_file_path') and self.active_file_path:
            try:
                
                clean_lines = self.edit_lines[:-4] if len(self.edit_lines) >= 4 else self.edit_lines
                with open(self.active_file_path, 'w', encoding='utf-8', newline='\n') as f:
                    f.write("\n".join(clean_lines) + "\n")
                self._log("Editor mode exited, saved changes directly to file.")
            except Exception as e:
                self._log(f"Editor mode exit save failed: {e}")

        
        top_v_idx = int(self.edit_scroll_y)
        top_ln = 1
        if 0 <= top_v_idx < len(getattr(self, 'edit_visible_indices', [])):
            top_ln = self.edit_visible_indices[top_v_idx] + 1

        cursor_ln = self.edit_cursor_row + 1

        self.is_editing = False
        saved_scroll_x = getattr(self, 'edit_scroll_x', 0) 

        
        saved_folds = set(getattr(self, 'edit_folded_blocks', set()))

        if hasattr(self, 'current_entry') and self.current_entry:
            self._select_entry(self.current_entry)

        
        if saved_folds:
            self.folded_blocks = set()
            for r in saved_folds:
                for i, (t, st, ln) in enumerate(self.new_lines):
                    if ln == r + 1:
                        if i in getattr(self, 'code_blocks', {}):
                            self.folded_blocks.add(i)
                        else:
                            for delta in (1, -1, 2, -2):
                                if (i + delta) in getattr(self, 'code_blocks', {}):
                                    self.folded_blocks.add(i + delta)
                                    break
                        break
            self._build_visible_indices()

        
        
        self.scroll_right_x = saved_scroll_x
        self.scroll_right_x_target = float(saved_scroll_x)
        self.scroll_right_x_float = float(saved_scroll_x)

        found_top_v_idx = -1
        found_cursor_v_idx = -1
        for v_idx, i in enumerate(self.visible_indices):
            _, _, ln_new = self.new_lines[i]
            if ln_new == top_ln:
                found_top_v_idx = v_idx
            if ln_new == cursor_ln:
                found_cursor_v_idx = v_idx

        if found_top_v_idx != -1:
            self.scroll_right = found_top_v_idx
            self.scroll_right_target = float(found_top_v_idx)
            self.scroll_right_float = float(found_top_v_idx)
        elif found_cursor_v_idx != -1:
            max_lines = (self.height - (self.title_bar_height + 25)) // self.line_height
            max_r = max(0, len(self.visible_indices) - max_lines)
            target = min(max_r, max(0, found_cursor_v_idx - (max_lines // 2)))
            self.scroll_right = target
            self.scroll_right_target = float(target)
            self.scroll_right_float = float(target)

        if found_cursor_v_idx != -1:
            self.selection_start = self.visible_indices[found_cursor_v_idx]
            self.selection_end = self.selection_start
            self.selecting_pane = "new"

        
        pygame.key.set_repeat(400, 60)
        self._update_search()

    def _save_editor_state(self):
        state = {
            'lines': self.edit_lines.copy(),
            'r': self.edit_cursor_row,
            'c': self.edit_cursor_col,
            'sel': self.edit_selection_start
        }
        self.edit_undo_stack.append(state)
        self.edit_redo_stack.clear()
        if len(self.edit_undo_stack) > 100:
            self.edit_undo_stack.pop(0)

    def _undo_editor_state(self):
        if not self.edit_undo_stack: return

        current_state = {
            'lines': self.edit_lines.copy(),
            'r': self.edit_cursor_row,
            'c': self.edit_cursor_col,
            'sel': self.edit_selection_start
        }
        self.edit_redo_stack.append(current_state)

        state = self.edit_undo_stack.pop()
        self.edit_lines = state['lines'].copy()
        self.edit_cursor_row = state['r']
        self.edit_cursor_col = state['c']
        self.edit_selection_start = state['sel']
        self._scroll_editor_to_cursor()

    def _redo_editor_state(self):
        if not self.edit_redo_stack: return

        current_state = {
            'lines': self.edit_lines.copy(),
            'r': self.edit_cursor_row,
            'c': self.edit_cursor_col,
            'sel': self.edit_selection_start
        }
        self.edit_undo_stack.append(current_state)

        state = self.edit_redo_stack.pop()
        self.edit_lines = state['lines'].copy()
        self.edit_cursor_row = state['r']
        self.edit_cursor_col = state['c']
        self.edit_selection_start = state['sel']
        self._scroll_editor_to_cursor()

    def _get_editor_selection_range(self):
        if not getattr(self, 'edit_selection_start', None):
            return None
        r1, c1 = self.edit_selection_start
        r2, c2 = self.edit_cursor_row, self.edit_cursor_col

        if r1 > r2 or (r1 == r2 and c1 > c2):
            return ((r2, c2), (r1, c1))
        return ((r1, c1), (r2, c2))

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

    def _register_undo_point(self, group_type=None):
        """Intelligently groups undo points by action types (e.g. typing a word, deleting) or pauses."""
        now = time.time()
        last_type = getattr(self, '_last_undo_group_type', None)
        last_time = getattr(self, '_last_undo_group_time', 0.0)

        
        
        
        
        is_new_group = (
            group_type is None or
            group_type == 'force' or
            last_type is None or
            group_type != last_type or
            (now - last_time > 1.0)
        )

        if is_new_group:
            
            state = {
                'lines': self.edit_lines.copy(),
                'r': self.edit_cursor_row,
                'c': self.edit_cursor_col,
                'sel': self.edit_selection_start
            }
            self.edit_undo_stack.append(state)
            self.edit_redo_stack.clear()
            if len(self.edit_undo_stack) > 100:
                self.edit_undo_stack.pop(0)

        
        self._last_undo_group_type = group_type
        self._last_undo_group_time = now

    def _delete_editor_selection(self):
        try:
            sel = self._get_editor_selection_range()
            if not sel: return False

            (r1, c1), (r2, c2) = sel
            
            r1 = max(0, min(len(self.edit_lines) - 1, r1))
            r2 = max(0, min(len(self.edit_lines) - 1, r2))
            c1 = max(0, min(len(self.edit_lines[r1]), c1))
            c2 = max(0, min(len(self.edit_lines[r2]), c2))

            
            self._register_undo_point('force')

            if r1 == r2:
                self.edit_lines[r1] = self.edit_lines[r1][:c1] + self.edit_lines[r1][c2:]
            else:
                self.edit_lines[r1] = self.edit_lines[r1][:c1] + self.edit_lines[r2][c2:]
                num_deleted = r2 - r1
                del self.edit_lines[r1+1:r2+1]
                self._shift_editor_folds(r1 + 1, -num_deleted)

            self.edit_cursor_row, self.edit_cursor_col = r1, c1
            self.edit_selection_start = None
            return True
        except Exception as e:
            self._log(f"Exception in _delete_editor_selection: {e}\n{traceback.format_exc()}")
            return False

    def _get_next_word_pos(self, row, col, direction):
        line = self.edit_lines[row]
        if direction == 1:  
            if col >= len(line):
                if row < len(self.edit_lines) - 1:
                    return row + 1, 0
                return row, col
            c = col
            
            if not line[c].isalnum():
                while c < len(line) and not line[c].isalnum() and not line[c].isspace():
                    c += 1
            
            if c < len(line) and line[c].isalnum():
                while c < len(line) and line[c].isalnum():
                    c += 1
            
            while c < len(line) and line[c].isspace():
                c += 1
            return row, c
        else:  
            if col == 0:
                if row > 0:
                    return row - 1, len(self.edit_lines[row - 1])
                return row, col
            c = col - 1
            
            while c > 0 and line[c].isspace():
                c -= 1
            
            if line[c].isalnum():
                while c > 0 and line[c-1].isalnum():
                    c -= 1
            else:
                while c > 0 and not line[c-1].isalnum() and not line[c-1].isspace():
                    c -= 1
            return row, c

    def _exit_edit_mode_discard(self):
        """Immediately exits editing mode, discarding all structural session updates."""
        top_v_idx = int(self.edit_scroll_y)
        top_ln = 1
        if 0 <= top_v_idx < len(getattr(self, 'edit_visible_indices', [])):
            top_ln = self.edit_visible_indices[top_v_idx] + 1

        cursor_ln = self.edit_cursor_row + 1

        self.is_editing = False
        self.edit_show_discard_btn = False
        saved_scroll_x = getattr(self, 'edit_scroll_x', 0) 

        saved_folds = set(getattr(self, 'edit_folded_blocks', set()))

        if hasattr(self, 'current_entry') and self.current_entry:
            self._select_entry(self.current_entry)

        
        if saved_folds:
            self.folded_blocks = set()
            for r in saved_folds:
                for i, (t, st, ln) in enumerate(self.new_lines):
                    if ln == r + 1:
                        if i in getattr(self, 'code_blocks', {}):
                            self.folded_blocks.add(i)
                        else:
                            for delta in (1, -1, 2, -2):
                                if (i + delta) in getattr(self, 'code_blocks', {}):
                                    self.folded_blocks.add(i + delta)
                                    break
                        break
            self._build_visible_indices()

        
        self.scroll_right_x = saved_scroll_x

        found_top_v_idx = -1
        found_cursor_v_idx = -1
        for v_idx, i in enumerate(self.visible_indices):
            _, _, ln_new = self.new_lines[i]
            if ln_new == top_ln:
                found_top_v_idx = v_idx
            if ln_new == cursor_ln:
                found_cursor_v_idx = v_idx

        if found_top_v_idx != -1:
            self.scroll_right = found_top_v_idx
            self.scroll_right_target = float(found_top_v_idx)
            self.scroll_right_float = float(found_top_v_idx)
        elif found_cursor_v_idx != -1:
            max_lines = (self.height - (self.title_bar_height + 25)) // self.line_height
            max_r = max(0, len(self.visible_indices) - max_lines)
            target = min(max_r, max(0, found_cursor_v_idx - (max_lines // 2)))
            self.scroll_right = target
            self.scroll_right_target = float(target)
            self.scroll_right_float = float(target)

        if found_cursor_v_idx != -1:
            self.selection_start = self.visible_indices[found_cursor_v_idx]
            self.selection_end = self.selection_start
            self.selecting_pane = "new"

        pygame.key.set_repeat(400, 60)
        self._update_search()

    def _scroll_editor_to_cursor(self):
        diff_y_start = self.title_bar_height + 25

        max_lines = (self.height - diff_y_start - 5) // self.line_height
        target_y = getattr(self, 'edit_target_scroll_y', self.edit_scroll_y)
        unfolded = False
        if self.edit_cursor_row < len(self.edit_actual_to_visual) and self.edit_actual_to_visual[self.edit_cursor_row] == -1:
            for start_i, end_i in getattr(self, 'edit_code_blocks', {}).items():
                if start_i <= self.edit_cursor_row <= end_i:
                    if start_i in getattr(self, 'edit_folded_blocks', set()):
                        self.edit_folded_blocks.remove(start_i)
                        unfolded = True
            if unfolded:
                self._build_edit_visible_indices()

        if self.edit_cursor_row < len(self.edit_actual_to_visual):
            v_idx = self.edit_actual_to_visual[self.edit_cursor_row]
            if v_idx != -1:
                if v_idx < target_y:
                    target_y = v_idx
                elif v_idx >= target_y + max_lines:
                    target_y = v_idx - max_lines + 1

        self.edit_target_scroll_y = max(0, min(len(self.edit_visible_indices) - max_lines, target_y))

        right_w = max(1, self.width - self.left_panel_width - self.minimap_width)
        pane_w = max(1, (right_w - self.GAP_WIDTH) // 2)
        pane_old_x = self.left_panel_width
        pane_new_x = pane_old_x + pane_w + self.GAP_WIDTH

        t = getattr(self, 'edit_anim_t', 1.0)
        editor_x_end = pane_old_x + 35
        editor_x = pane_new_x - (pane_new_x - editor_x_end) * t
        editor_w = right_w - (editor_x - pane_old_x) - 20
        text_offset = 60 + int(25 * t)

        pre_text = self.edit_lines[self.edit_cursor_row][:self.edit_cursor_col]
        px_w, _ = self.font.size(pre_text.replace('\t', '    '))

        if px_w < self.edit_scroll_x:
            self.edit_scroll_x = max(0, px_w - 50)
        elif px_w > self.edit_scroll_x + editor_w - text_offset - 15:
            self.edit_scroll_x = px_w - editor_w + text_offset + 15

    def _draw_editor_sidebar(self, x, y, w, h):
        """Draws vertical editor tools inside the exposed panel region with smooth fade transitions."""
        try:
            x = int(x)
            y = int(y)
            w = int(w)
            h = int(h)

            if w <= 15 or h <= 0: return
            t = getattr(self, 'edit_anim_t', 0.0)
            alpha = int(255 * t)
            sidebar_surf = pygame.Surface((w, h), pygame.SRCALPHA)

            help_lines = [
                ("Ctrl+F", "Find", (150, 200, 255)),
                ("Ctrl+H", "Find and Replace", (150, 200, 255)),
                ("Ctrl+Z", "Undo Change", (150, 200, 255)),
                ("Ctrl+Y", "Redo Change", (150, 200, 255)),
                ("Ctrl+A", "Select All", (150, 200, 255)),
                ("Tab", "Indent Lines", (150, 200, 255)),
                ("Sh+Tab", "Dedent Lines", (150, 200, 255)),
                ("Ctrl+Left", "Word Jump Left", (150, 200, 255)),
                ("Ctrl+Right", "Word Jump Right", (150, 200, 255)),
                ("Click Margin", "Bookmark", (150, 200, 255)),
            ]

            curr_y = 10
            for key, desc, color in help_lines:
                key_w = self.font_bold.size(key)[0]
                key_surf = self.font_bold.render(key, True, color)
                sep_surf = self.font.render("-", True, (120, 120, 120))
                desc_surf = self.font.render(desc, True, (170, 170, 170))

                key_surf.set_alpha(alpha)
                sep_surf.set_alpha(alpha)
                desc_surf.set_alpha(alpha)

                sidebar_surf.blit(key_surf, (5, curr_y))
                sidebar_surf.blit(sep_surf, (5 + key_w + 3, curr_y))
                sidebar_surf.blit(desc_surf, (5 + key_w + sep_surf.get_width() + 6, curr_y))

                curr_y += 18

            self.screen.blit(sidebar_surf, (x, y))
        except Exception as e:
            self._log(f"Error in _draw_editor_sidebar: {e}")

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

    def _jump_to_next_diff(self, direction):
        if not hasattr(self, 'diff_blocks') or not self.diff_blocks:
            return

        current_v_idx = int(getattr(self, 'scroll_right_target', float(self.scroll_right)))
        target_v_idx = None

        block_v_starts = []
        for block in self.diff_blocks:
            if block['state'] != 'diff': continue
            for sc in block.get('sub_chunks', []):
                if sc['state'] != 'diff': continue
                v_start = -1
                for i in range(sc['start'], sc['end'] + 1):
                    if self.actual_to_visual[i] != -1:
                        v_start = self.actual_to_visual[i]
                        break
                if v_start != -1:
                    block_v_starts.append(v_start)

        if not block_v_starts: return

        if direction == 1: 
            for v_start in block_v_starts:
                if v_start > current_v_idx + 3:
                    target_v_idx = v_start
                    break
            if target_v_idx is None:
                target_v_idx = block_v_starts[0] 
        else: 
            for v_start in reversed(block_v_starts):
                if v_start < current_v_idx - 1:
                    target_v_idx = v_start
                    break
            if target_v_idx is None:
                target_v_idx = block_v_starts[-1] 

        if target_v_idx is not None:
            self.scroll_right_target = max(0.0, float(target_v_idx - 3))

    def _fold_unchanged_blocks(self):
        if not hasattr(self, 'code_blocks') or not hasattr(self, 'diff_blocks'):
            return

        self.folded_blocks.clear()

        changed_lines = set()
        for block in self.diff_blocks:
            if block['state'] == 'diff':
                for sc in block.get('sub_chunks', []):
                    if sc['state'] == 'diff':
                        for i in range(sc['start'], sc['end'] + 1):
                            changed_lines.add(i)

        for start_i, end_i in self.code_blocks.items():
            block_lines = set(range(start_i, end_i + 1))
            if not block_lines.intersection(changed_lines):
                self.folded_blocks.add(start_i)

        self._build_visible_indices()
        self._update_search()

        
        self._jump_to_next_diff(1)

    def _revert_version(self, entry):
        self.context_menu = None
        if not entry: return

        full_path = entry.get("full_path", "")
        bak_ref = entry.get("backup_reference", "")

        
        if not full_path or not bak_ref:
            return

        
        title = "Confirm Historical Revert"

        lines = [
            "WARNING: This will completely overwrite the live file.",
            "Any unsaved changes currently in the file will be lost.",
            "",
            f"File: {entry.get('file', 'Unknown')}",
            f"Run:  {entry.get('run_id', 'Unknown')}"
        ]

        
        if getattr(self, 'hwnd', None) and os.name == 'nt':
            ctypes.windll.user32.ShowWindow(self.hwnd, 5) 
            ctypes.windll.user32.SetForegroundWindow(self.hwnd)

        if not self._show_modal_confirm(title, lines):
            return 

        bak_path = os.path.join(os.path.dirname(full_path), "ep_backups", bak_ref)
        if os.path.exists(bak_path) and os.path.exists(full_path):
            try:
                old_text = self._read_file_text(bak_path)
                with open(full_path, 'w', encoding='utf-8', newline='\n') as f:
                    f.write(old_text)

                
                self._increment_registry_stat("PastVersionReverts")

                self._log(f"Successfully reverted {full_path} to {bak_ref}")
            except Exception as e:
                self._log(f"Failed to revert file: {e}")

    def _goto_end(self):
        diff_y_start = self.title_bar_height + 25

        max_lines = (self.height - diff_y_start) // self.line_height
        max_r = max(0, len(self.visible_indices) - max_lines)
        self.scroll_right_target = float(max_r)
        self.context_menu = None

    def _goto_next_block_type(self, block_type):
        self.context_menu = None
        if not hasattr(self, 'old_lines') or not self.old_lines: return

        current_v_idx = int(getattr(self, 'scroll_right_target', float(self.scroll_right)))
        target_v_idx = None

        def _is_match(idx):
            i = self.visible_indices[idx]
            if i not in getattr(self, 'code_blocks', {}): return False
            t_low = self.old_lines[i][0].lstrip().lower()
            is_class = any(p in t_low for p in ['class ', 'struct ', 'interface ', '@interface', 'target {'])
            is_method = any(p in t_low for p in ['def ', 'func ', 'function', 'void ', 'public ', 'private ', 'async ', 'const ', 'let ', 'var ']) or\
                        (not is_class and '{' in t_low) or (t_low.startswith('<') and not t_low.startswith('</'))
            return (block_type == 'class' and is_class) or (block_type == 'method' and is_method)

        
        for v_idx in range(current_v_idx + 1, len(self.visible_indices)):
            if _is_match(v_idx):
                target_v_idx = v_idx
                break
        
        if target_v_idx is None:
            for v_idx in range(0, current_v_idx):
                if _is_match(v_idx):
                    target_v_idx = v_idx
                    break

        if target_v_idx is not None:
            self.scroll_right_target = float(target_v_idx)

    def _read_file_text(self, filepath: str) -> str:
        """
        Specialised text parser that aggressively forces text into a Pygame-safe format.
        Reads raw bytes, handles encodings, and eradicates non-printable control characters.
        Also normalizes CRLF and CR line endings to LF to prevent line ending differences.
        """
        if not os.path.exists(filepath): return ""

        try:
            with open(filepath, 'rb') as f:
                raw_bytes = f.read()
        except Exception as e:
            self._log(f"Failed to read raw bytes from {filepath}: {e}")
            return ""

        
        
        if len(raw_bytes) > 2 and b'\x00' in raw_bytes[:100]:
            encodings = ('utf-16', 'utf-8', 'utf-8-sig', 'windows-1252', 'latin-1')
        else:
            encodings = ('utf-8', 'utf-8-sig', 'utf-16', 'windows-1252', 'latin-1')

        text = ""
        for enc in encodings:
            try:
                text = raw_bytes.decode(enc)
                break
            except UnicodeDecodeError:
                continue

        if not text and raw_bytes:
            
            text = raw_bytes.decode('utf-8', errors='ignore')

        
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        
        
        text = text.replace('\x00', '')

        
        
        text = re.sub(r'[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        text = text.replace('\xa0', ' ')
        return text

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

    def _replace_function(self, old_start_idx):
        """Replace entire function/class from historical version into live file.
        Works for Python, JavaScript, TypeScript, C, Java, Go, Rust, etc."""
        if old_start_idx not in getattr(self, 'code_blocks', {}):
            return

        old_end_idx = self.code_blocks[old_start_idx]

        
        func_lines = []
        for j in range(old_start_idx, old_end_idx + 1):
            text, status, _ = self.old_lines[j]
            if status not in ("blank_del", "blank_add", "header"):
                func_lines.append(text)

        if not func_lines:
            return

        
        first_line = func_lines[0].strip()
        name_match = re.search(r'(function |def |async |class |const |let |var )?(\w+)', first_line)
        if not name_match:
            return
        func_name = name_match.group(2)

        
        new_start = None
        for j in range(len(self.new_lines)):
            t, st, _ = self.new_lines[j]
            if st in ("context", "added") and func_name in t:
                
                if any(kw in t for kw in ('function', 'def ', 'class ', 'const ', 'let ', 'var ')):
                    new_start = j
                    break

        if new_start is None:
            print(f"[StitchViewer] Could not find function '{func_name}' in current file.")
            return

        
        new_end = new_start
        if new_start in getattr(self, 'code_blocks', {}):
            new_end = self.code_blocks[new_start]
        else:
            
            path = getattr(self, 'active_file_path', '')
            ext = os.path.splitext(path)[1].lower() if path else ''
            is_brace = ext in {'.js', '.jsx', '.ts', '.tsx', '.c', '.cpp', '.java', '.cs', '.go', '.rs'}

            if is_brace:
                brace_depth = 0
                started = False
                for j in range(new_start, len(self.new_lines)):
                    t, st, _ = self.new_lines[j]
                    if st in ("blank_add", "blank_del"):
                        continue
                    if '{' in t:
                        started = True
                        brace_depth += t.count('{')
                    if '}' in t and started:
                        brace_depth -= t.count('}')
                        if brace_depth <= 0:
                            new_end = j
                            break
            else:
                
                base_indent = len(self.new_lines[new_start][0]) - len(self.new_lines[new_start][0].lstrip())
                for j in range(new_start + 1, len(self.new_lines)):
                    t, st, _ = self.new_lines[j]
                    if st in ("blank_add", "blank_del"):
                        continue
                    curr_indent = len(t) - len(t.lstrip()) if t.strip() else 999
                    if curr_indent <= base_indent and t.strip():
                        new_end = j - 1
                        break
                    new_end = j

        
        new_func_tuples = [(line, "context", None) for line in func_lines]

        
        self.new_lines = self.new_lines[:new_start] + new_func_tuples + self.new_lines[new_end + 1:]

        
        if hasattr(self, 'active_file_path') and self.active_file_path:
            try:
                output_lines = [text for text, status, ln in self.new_lines if status in ("context", "added")]
                with open(self.active_file_path, 'w', encoding='utf-8', newline='\n') as f:
                    f.write("\n".join(output_lines) + "\n")
                self._log(f"Replaced function '{func_name}' from history into live file")
            except Exception as e:
                self._log(f"Replace function failed: {e}")

        
        if hasattr(self, 'current_entry') and self.current_entry:
            self._select_entry(self.current_entry)

    def _get_indent(self, line):
        """Helper for Python indent calculation"""
        return len(line) - len(line.lstrip())

    def _copy_version_to_clipboard(self, entry):
        self.context_menu = None
        if not entry: return

        full_path = entry.get("full_path", "")
        bak_ref = entry.get("backup_reference", "")

        text_to_copy = ""

        
        if full_path and bak_ref:
            bak_path = os.path.join(os.path.dirname(full_path), "ep_backups", bak_ref)
            if os.path.exists(bak_path):
                text_to_copy = self._read_file_text(bak_path)
        
        elif entry.get('is_unversioned', False) and full_path and os.path.exists(full_path):
            text_to_copy = self._read_file_text(full_path)

        if text_to_copy:
            try:
                pyperclip.copy(text_to_copy)
                self._log(f"Copied version {bak_ref if bak_ref else 'LIVE'} to clipboard.")
            except Exception as e:
                self._log(f"Failed to copy version to clipboard: {e}")

    def _restore_code_block(self, b_start, b_end):
        """Reverts a specific code block by reading directly from the source files and swapping the raw lines."""
        self.context_menu = None

        
        old_lns = [item[2] for item in self.old_lines[b_start:b_end+1] if item[2] is not None]

        new_lns = [item[2] for item in self.new_lines[b_start:b_end+1] if item[2] is not None]

        if not old_lns: return
        old_min, old_max = min(old_lns), max(old_lns)

        
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
            for i in range(b_start - 1, -1, -1):
                if self.new_lines[i][2] is not None:
                    insert_idx = self.new_lines[i][2]
                    break
            final_lines = new_file_lines[:insert_idx] + old_block_lines + new_file_lines[insert_idx:]

        
        try:
            with open(self.active_file_path, 'w', encoding='utf-8', newline='\n') as f:
                f.write("\n".join(final_lines) + "\n")
            self._log(f"Successfully restored block lines {old_min}-{old_max} directly from source file.")

            self._select_entry(self.current_entry) 
        except Exception as e:
            self._log(f"Failed to restore block from file: {e}")

    def _copy_code_block(self, b_start, b_end, pane):
        """Copies the contents of a specific code block directly from the raw source file."""
        self.context_menu = None

        
        lines = self.old_lines if pane == "old" else self.new_lines

        valid_lns = [item[2] for item in lines[b_start:b_end+1] if item[2] is not None]

        if not valid_lns: return
        min_ln, max_ln = min(valid_lns), max(valid_lns)

        
        if pane == "old":
            bak_ref = getattr(self, 'current_entry', {}).get("backup_reference", "")
            if not bak_ref: return
            parent_dir = os.path.dirname(getattr(self, 'active_file_path', ''))
            file_path = os.path.join(parent_dir, "ep_backups", bak_ref)
        else:
            file_path = getattr(self, 'active_file_path', '')

        if not file_path or not os.path.exists(file_path):
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

        
        source_lines = _get_raw_lines(file_path)
        if source_lines:
            block_text = "\n".join(source_lines[min_ln - 1 : max_ln])
            try:
                pyperclip.copy(block_text)
                self._log(f"Copied {max_ln - min_ln + 1} lines directly from source file {os.path.basename(file_path)}.")
            except Exception: pass

    def _increment_registry_stat(self, stat_name: str, amount: int = 1) -> None:
        """Securely increments a rolling telemetry stat directly in the central registry."""
        if os.name != 'nt':
            return

        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\StitchViewer")
            try:
                current_val, _ = winreg.QueryValueEx(key, stat_name)
            except OSError:
                current_val = 0
            winreg.SetValueEx(key, stat_name, 0, winreg.REG_DWORD, current_val + amount)
            winreg.CloseKey(key)
        except Exception as e:
            self._log(f"Failed to increment registry stat {stat_name}: {e}")

    def _activate_search(self):
        self.search_active = True
        self.context_menu = None
        self.search_sel_start = 0
        self.search_sel_end = len(self.search_text)
        self.search_cursor_pos = len(self.search_text)

    def _prompt_goto_line(self):
        self.context_menu = None
        line_str = self._show_modal_input("Go To Line", "Enter target line number:")
        if line_str and line_str.isdigit():
            target_ln = int(line_str)
            if getattr(self, 'is_editing', False):
                target_row = max(0, min(len(self.edit_lines) - 1, target_ln - 1))
                self.edit_cursor_row = target_row
                self.edit_cursor_col = len(self.edit_lines[target_row])

                self.edit_selection_start = (target_row, 0) 

                
                diff_y_start = self.title_bar_height + 25

                max_lines = (self.height - diff_y_start - 5) // self.line_height
                v_idx = self.edit_actual_to_visual[target_row]

                if v_idx == -1:
                    for start_i, end_i in getattr(self, 'edit_code_blocks', {}).items():
                        if start_i <= target_row <= end_i:
                            if start_i in getattr(self, 'edit_folded_blocks', set()):
                                self.edit_folded_blocks.remove(start_i)
                            break
                    self._build_edit_visible_indices()
                    v_idx = self.edit_actual_to_visual[target_row]

                if v_idx != -1:
                    self.edit_target_scroll_y = float(max(0, min(len(self.edit_visible_indices) - max_lines, v_idx - (max_lines // 2))))
                    self.edit_scroll_y = int(self.edit_target_scroll_y)
                    self.edit_scroll_y_float = float(self.edit_target_scroll_y)
                self._scroll_editor_to_cursor()
            else:
                found_i = -1
                found_pane = "new"

                for i, (text, status, ln) in enumerate(self.new_lines):
                    if ln == target_ln:
                        found_i = i
                        found_pane = "new"
                        break

                if found_i == -1:
                    for i, (text, status, ln) in enumerate(self.old_lines):
                        if ln == target_ln:
                            found_i = i
                            found_pane = "old"
                            break

                if found_i != -1:
                    if found_i not in self.visible_indices:
                        for start_i, end_i in getattr(self, 'code_blocks', {}).items():
                            if start_i <= found_i <= end_i:
                                if start_i in getattr(self, 'folded_blocks', set()):
                                    self.folded_blocks.remove(start_i)
                                break
                        self._build_visible_indices()

                found_v_idx = -1
                if found_i != -1 and found_i < len(self.actual_to_visual):
                    found_v_idx = self.actual_to_visual[found_i]

                if found_v_idx != -1:
                    max_lines = (self.height - (self.title_bar_height + 25)) // self.line_height
                    target_scroll = max(0, found_v_idx - (max_lines // 2))
                    self.scroll_right_target = float(target_scroll)
                    self.scroll_right = target_scroll
                    self.scroll_right_float = float(target_scroll)

                    
                    self.selection_start = self.visible_indices[found_v_idx]
                    self.selection_end = self.selection_start
                    self.selecting_pane = found_pane

    def _move_selection(self, delta):
        if getattr(self, 'selection_start', None) is None:
            if not getattr(self, 'visible_indices', []): return
            self.selection_start = self.visible_indices[int(getattr(self, 'scroll_right_target', float(self.scroll_right)))]
            self.selection_end = self.selection_start
            self.selecting_pane = "old"

        if getattr(self, 'selection_end', None) is not None:
            curr_v_idx = -1
            if self.selection_end < len(self.actual_to_visual):
                curr_v_idx = self.actual_to_visual[self.selection_end]

            if curr_v_idx != -1:
                new_v_idx = max(0, min(len(self.visible_indices) - 1, curr_v_idx + delta))
                self.selection_end = self.visible_indices[new_v_idx]

                max_lines = (self.height - (self.title_bar_height + 25)) // self.line_height
                scroll_target = getattr(self, 'scroll_right_target', float(self.scroll_right))
                if new_v_idx < scroll_target:
                    self.scroll_right_target = float(new_v_idx)
                elif new_v_idx >= scroll_target + max_lines:
                    self.scroll_right_target = float(new_v_idx - max_lines + 1)

    def _replace_multiple_functions(self, blocks):
        for b_start, b_end in blocks:
            self._replace_function(b_start)

    def _attach_to_compose(self, entry):
        """Sends file to main CodeStitcher Compose Window via a covert clipboard IPC payload."""
        self.context_menu = None
        if not entry: return

        full_path = entry.get("full_path", "")
        bak_ref = entry.get("backup_reference", "")

        target_path = full_path
        if full_path and bak_ref:
            bak_path = os.path.join(os.path.dirname(full_path), "ep_backups", bak_ref)
            if os.path.exists(bak_path):
                target_path = bak_path

        if not target_path or not os.path.exists(target_path):
            self._log("Cannot attach: Invalid or missing file path.")
            return

        
        ipc_payload = f"<<<CODE_STITCHER_IPC_ATTACH_v1>>>|||{target_path}"
        try:
            pyperclip.copy(ipc_payload)
            self._log(f"Sent IPC attachment payload via clipboard: {target_path}")
        except Exception as e:
            self._log(f"Failed to queue IPC attachment via clipboard: {e}")

    def _analyze_edit_code_blocks(self):
        self.edit_code_blocks = {}

        self.edit_block_depths = {}

        if hasattr(self, 'edit_current_fold_level'):
            del self.edit_current_fold_level

        stack = []
        path = getattr(self, 'active_file_path', '')
        ext = os.path.splitext(path)[1].lower() if path else ''
        is_brace_lang = ext in {'.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs',
                                '.c', '.cpp', '.cc', '.cxx', '.h', '.hpp',
                                '.java', '.cs', '.go', '.rs', '.swift', '.kt', '.scala', '.php',
                                '.json', '.css', '.scss', '.less'}
        last_def_line = -1
        for i in range(len(self.edit_lines)):
            line = self.edit_lines[i]
            stripped = line.lstrip()

            
            if not stripped or stripped.startswith('#') or stripped.startswith('//'):
                continue

            
            if is_brace_lang:
                lower = stripped.lower()
                if any(kw in lower for kw in ('function', 'class ', 'struct ', 'interface ', 'enum ', 'namespace ', '=>')) or\
                   (stripped.endswith(')') and '(' in stripped) or\
                   stripped.endswith('='):
                    last_def_line = i

                open_braces = stripped.count('{') + stripped.count('[')
                close_braces = stripped.count('}') + stripped.count(']')

                for _ in range(open_braces):
                    if last_def_line != -1 and (i - last_def_line) <= 2:
                        stack.append((last_def_line, len(stack)))
                        last_def_line = -1
                    else:
                        stack.append((i, len(stack)))

                for _ in range(close_braces):
                    if stack:
                        start, depth = stack.pop()
                        if start not in self.edit_code_blocks:
                            self.edit_code_blocks[start] = i
                            self.edit_block_depths[start] = depth

            
            else:
                indent = len(line) - len(stripped)
                while stack:
                    prev_i, _ = stack[-1]
                    prev_line = self.edit_lines[prev_i]
                    prev_indent = len(prev_line) - len(prev_line.lstrip())

                    if indent <= prev_indent:
                        start, depth = stack.pop()
                        end_val = i - 1
                        while end_val > start and not self.edit_lines[end_val].strip():
                            end_val -= 1
                        if end_val > start:
                            self.edit_code_blocks[start] = end_val
                            self.edit_block_depths[start] = depth
                    else:
                        break
                stack.append((i, len(stack)))

        while stack:
            start, depth = stack.pop()
            end_val = len(self.edit_lines) - 1
            while end_val > start and not self.edit_lines[end_val].strip():
                end_val -= 1
            if end_val > start:
                if not is_brace_lang:
                    self.edit_code_blocks[start] = end_val
                    self.edit_block_depths[start] = depth
                elif start not in self.edit_code_blocks:
                    self.edit_code_blocks[start] = end_val
                    self.edit_block_depths[start] = depth

        keys_to_remove = [k for k, v in self.edit_code_blocks.items() if v <= k]
        for k in keys_to_remove:
            del self.edit_code_blocks[k]
            if k in getattr(self, 'edit_block_depths', {}):
                del self.edit_block_depths[k]

    
    def _build_edit_visible_indices(self):
        self.edit_is_line_folded = [False] * len(self.edit_lines)
        i = 0
        while i < len(self.edit_lines):
            if i in getattr(self, 'edit_folded_blocks', set()):
                self.edit_is_line_folded[i] = False
                end_idx = self.edit_code_blocks.get(i, i)
                for j in range(i + 1, end_idx + 1):
                    if j < len(self.edit_is_line_folded):
                        self.edit_is_line_folded[j] = True
                i = end_idx + 1
            else:
                self.edit_is_line_folded[i] = False
                i += 1

        
        cursor_hidden = False
        if getattr(self, 'edit_cursor_row', -1) != -1 and self.edit_cursor_row < len(self.edit_is_line_folded):
            if self.edit_is_line_folded[self.edit_cursor_row]:
                cursor_hidden = True

        if getattr(self, 'edit_selection_start', None) is not None:
            sel_r = self.edit_selection_start[0]
            if sel_r < len(self.edit_is_line_folded) and self.edit_is_line_folded[sel_r]:
                cursor_hidden = True

        if cursor_hidden:
            blocks_to_remove = set()
            for r in getattr(self, 'edit_folded_blocks', set()):
                end_idx = self.edit_code_blocks.get(r, r)
                if getattr(self, 'edit_cursor_row', -1) != -1 and r < self.edit_cursor_row <= end_idx:
                    blocks_to_remove.add(r)
                if getattr(self, 'edit_selection_start', None) is not None and r < self.edit_selection_start[0] <= end_idx:
                    blocks_to_remove.add(r)

            if blocks_to_remove:
                for r in blocks_to_remove:
                    self.edit_folded_blocks.remove(r)

                
                self.edit_is_line_folded = [False] * len(self.edit_lines)
                i = 0
                while i < len(self.edit_lines):
                    if i in self.edit_folded_blocks:
                        self.edit_is_line_folded[i] = False
                        end_idx = self.edit_code_blocks.get(i, i)
                        for j in range(i + 1, end_idx + 1):
                            if j < len(self.edit_is_line_folded):
                                self.edit_is_line_folded[j] = True
                        i = end_idx + 1
                    else:
                        self.edit_is_line_folded[i] = False
                        i += 1

        self.edit_visible_indices = [i for i in range(len(self.edit_lines)) if not self.edit_is_line_folded[i]]

        self.edit_actual_to_visual = [-1] * len(self.edit_lines)
        for v_idx, i in enumerate(self.edit_visible_indices):
            self.edit_actual_to_visual[i] = v_idx

        
        self.max_edit_width = 0
        for line in self.edit_lines:
            w, _ = self.font.size(line.replace('\t', '    '))
            if w > self.max_edit_width:
                self.max_edit_width = w

        self._update_search(jump=False)

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

    def _get_replace_rects(self):
        right_w = max(1, self.width - self.left_panel_width - self.minimap_width)
        pane_w = max(1, (right_w - self.GAP_WIDTH) // 2)
        pane_old_x = self.left_panel_width
        pane_new_x = pane_old_x + pane_w + self.GAP_WIDTH
        diff_y_start = self.title_bar_height + 25

        t = getattr(self, 'edit_anim_t', 1.0)
        editor_x_end = pane_old_x + 35
        editor_x = int(pane_new_x - (pane_new_x - editor_x_end) * t)
        text_offset = 60 + int(25 * t)

        base_x = editor_x + text_offset + 20
        base_y = diff_y_start + 15

        pw = 300
        ph = 115

        return {
            'panel': pygame.Rect(base_x, base_y, pw, ph),
            'find_box': pygame.Rect(base_x + 65, base_y + 25, 225, 22),
            'rep_box': pygame.Rect(base_x + 65, base_y + 52, 225, 22),
            'btn_next': pygame.Rect(base_x + 10, base_y + 82, 40, 22),
            'btn_prev': pygame.Rect(base_x + 55, base_y + 82, 40, 22),
            'btn_rep': pygame.Rect(base_x + 100, base_y + 82, 55, 22),
            'btn_all': pygame.Rect(base_x + 160, base_y + 82, 35, 22),
            'btn_close': pygame.Rect(base_x + pw - 16, base_y + 6, 12, 12),
            'chk_case': pygame.Rect(base_x + 205, base_y + 88, 10, 10),
            'chk_wrap': pygame.Rect(base_x + 245, base_y + 88, 10, 10),
            'chk_dir': pygame.Rect(base_x + 280, base_y + 88, 10, 10),
        }

    def _do_replace_find_next(self, force_dir=None, from_replace=False):
        query = getattr(self, 'edit_replace_find', "")
        if not query:
            self.edit_replace_msg = ""
            return False

        case_sens = getattr(self, 'edit_replace_case', False)
        wrap = getattr(self, 'edit_replace_wrap', True)
        direction = force_dir if force_dir is not None else getattr(self, 'edit_replace_dir', 1)

        if not case_sens:
            query = query.lower()

        start_r = self.edit_cursor_row
        start_c = self.edit_cursor_col

        
        sel = self._get_editor_selection_range()
        if sel and sel[0] != sel[1]:
            (r1, c1), (r2, c2) = sel
            if direction == 1:
                start_r, start_c = r2, c2
            else:
                start_r, start_c = r1, max(0, c1 - 1)

        def search_lines(r_start, c_start, r_end, dir_step):
            r = r_start
            while 0 <= r < len(self.edit_lines):
                line = self.edit_lines[r]
                check_line = line if case_sens else line.lower()

                if dir_step == 1:
                    idx = check_line.find(query, c_start if r == r_start else 0)
                    if idx != -1:
                        self.edit_selection_start = (r, idx)
                        self.edit_cursor_row = r
                        self.edit_cursor_col = idx + len(query)
                        self._scroll_editor_to_cursor()
                        return True
                else:
                    end_limit = c_start if r == r_start else len(check_line)
                    idx = check_line.rfind(query, 0, end_limit)
                    if idx != -1:
                        self.edit_selection_start = (r, idx)
                        self.edit_cursor_row = r
                        self.edit_cursor_col = idx + len(query)
                        self._scroll_editor_to_cursor()
                        return True

                r += dir_step
                if r == r_end: break
            return False

        found = False
        if direction == 1:
            if search_lines(start_r, start_c, len(self.edit_lines), 1):
                found = True
            elif wrap and search_lines(0, 0, start_r + 1, 1):
                found = True
        else:
            if search_lines(start_r, start_c, -1, -1):
                found = True
            elif wrap and search_lines(len(self.edit_lines)-1, len(self.edit_lines[-1]), start_r - 1, -1):
                found = True

        if not found:
            self.edit_replace_msg = "No matches found."
            return False
        else:
            if not from_replace:
                self.edit_replace_msg = ""
            return True

    def _do_replace_replace(self):
        sel = self._get_editor_selection_range()
        query = getattr(self, 'edit_replace_find', "")
        if not query or not sel:
            self._do_replace_find_next()
            return

        (r1, c1), (r2, c2) = sel
        if r1 != r2:
            self._do_replace_find_next()
            return

        case_sens = getattr(self, 'edit_replace_case', False)
        selected_text = self.edit_lines[r1][c1:c2]

        match = (selected_text == query) if case_sens else (selected_text.lower() == query.lower())

        if match:
            rep_text = getattr(self, 'edit_replace_rep', "")
            self._register_undo_point('force')
            self.edit_lines[r1] = self.edit_lines[r1][:c1] + rep_text + self.edit_lines[r1][c2:]
            self.edit_selection_start = None
            self.edit_cursor_row = r1
            self.edit_cursor_col = c1 + len(rep_text)
            self._run_linter()
            self.edit_replace_msg = "Replaced 1 occurrence."
            self._do_replace_find_next(from_replace=True)
        else:
            self._do_replace_find_next()

    def _do_replace_all(self):
        query = getattr(self, 'edit_replace_find', "")
        if not query: return
        rep_text = getattr(self, 'edit_replace_rep', "")
        case_sens = getattr(self, 'edit_replace_case', False)
        self._register_undo_point('force')
        count = 0

        new_lines = []
        for line in self.edit_lines:
            if not case_sens:
                pattern = re.compile(re.escape(query), re.IGNORECASE)
                new_line, subs = pattern.subn(rep_text.replace('\\', '\\\\'), line)
                count += subs
                new_lines.append(new_line)
            else:
                count += line.count(query)
                new_lines.append(line.replace(query, rep_text))

        if count > 0:
            self.edit_lines = new_lines
            self.edit_selection_start = None
            self._run_linter()
            self.edit_replace_msg = f"Replaced {count} occurrences."
            self._log(f"Replaced {count} occurrences across entire document.")
        else:
            self.edit_replace_msg = "No occurrences found to replace."

    def _draw_commands_help_overlay(self, mx, my):
        
        self.screen.set_clip(None)

        help_lines = [
            "=== Keyboard Shortcuts ===",
            "",
            " General:",
            "  • Ctrl + F            : Find",
            "  • Ctrl + G            : Go to Line",
            "  • Ctrl + C            : Copy Selection",
            "",
            " Diff Viewer:",
            "  • Up/Down, PgUp/PgDn  : Scroll",
            "  • Alt + Up/Down       : Jump to next/prev difference",
            "  • Left / Right        : Navigate History",
            "  • Shift + Arrows      : Move Selection",
            "",
            " Editor:",
            "  • Arrows / Home / End : Move cursor",
            "  • Ctrl + Left/Right   : Word jump",
            "  • Shift + Arrows/Click: Highlight text",
            "  • Ctrl + A            : Select All",
            "  • Ctrl + H            : Find and Replace",
            "  • Ctrl + C / X / V    : Copy / Cut / Paste",
            "  • Tab / Shift+Tab     : Indent / Dedent blocks",
            "  • Ctrl + Z / Y        : Undo / Redo",
            "  • Ctrl + S (or ESC)   : Save & Exit Editor",
        ]

        h = len(help_lines) * 18 + 40
        box_w = 340

        
        box_x = self.left_panel_width + 10
        box_y = self.title_bar_height + 30

        overlay = pygame.Surface((box_w, h), pygame.SRCALPHA)

        
        pygame.draw.rect(overlay, (25, 30, 35, 245), overlay.get_rect(), border_radius=6)
        pygame.draw.rect(overlay, (100, 120, 160, 255), overlay.get_rect(), 2, border_radius=6)

        c_rect = pygame.Rect(box_x + box_w - 22, box_y + 10, 16, 16)
        self.help_close_rect = c_rect
        hover_c = c_rect.collidepoint(mx, my)

        x_surf = self.font_bold.render("×", True, (255, 255, 255))

        for i, line in enumerate(help_lines):
            color = (255, 255, 255) if line.startswith("===") else (200, 220, 240)
            t_surf = self.font.render(line, True, color)
            overlay.blit(t_surf, (15, 15 + i * 18))

        self.screen.blit(overlay, (box_x, box_y))

        
        pygame.draw.rect(self.screen, (230, 40, 40) if hover_c else (70, 70, 75), c_rect, border_radius=3)
        pygame.draw.rect(self.screen, (255, 100, 100) if hover_c else (110, 110, 120), c_rect, 1, border_radius=3)
        self.screen.blit(x_surf, (c_rect.centerx - x_surf.get_width()//2, c_rect.centery - x_surf.get_height()//2 - 1))

    def _adjust_fold_level(self, delta):
        is_edit = getattr(self, 'is_editing', False)
        if is_edit:
            blocks = getattr(self, 'edit_code_blocks', {})
            depths = getattr(self, 'edit_block_depths', {})
            folded = self.edit_folded_blocks
            state_var = 'edit_current_fold_level'
            diff_y_start = self.title_bar_height + 25

            max_lines = (self.height - diff_y_start - 5) // self.line_height
            
            current_scroll = getattr(self, 'edit_target_scroll_y', 0.0)
            center_v_idx = int(current_scroll + max_lines / 2)

            if getattr(self, 'edit_visible_indices', []) and 0 <= center_v_idx < len(self.edit_visible_indices):
                anchor_actual = self.edit_visible_indices[center_v_idx]
            else:
                anchor_actual = -1
        else:
            blocks = getattr(self, 'code_blocks', {})
            depths = getattr(self, 'block_depths', {})
            folded = self.folded_blocks
            state_var = 'current_fold_level'
            diff_y_start = self.title_bar_height + 25

            max_lines = (self.height - diff_y_start) // self.line_height
            
            current_scroll = getattr(self, 'scroll_right_target', 0.0)
            center_v_idx = int(current_scroll + max_lines / 2)

            if getattr(self, 'visible_indices', []) and 0 <= center_v_idx < len(self.visible_indices):
                anchor_actual = self.visible_indices[center_v_idx]
            else:
                anchor_actual = -1

        if not blocks:
            return

        max_depth = max(depths.values()) if depths else 0

        if not hasattr(self, state_var):
            if folded:
                min_folded_depth = min([depths[b] for b in folded if b in depths], default=0)
                setattr(self, state_var, min_folded_depth)
            else:
                setattr(self, state_var, max_depth + 1)

        current_val = getattr(self, state_var)
        current_val += delta
        current_val = max(0, min(current_val, max_depth + 1))
        setattr(self, state_var, current_val)

        folded.clear()

        
        if current_val <= max_depth:
            for start_i, depth in depths.items():
                if depth >= current_val:
                    folded.add(start_i)

        if is_edit:
            
            for start_i in folded:
                end_i = blocks.get(start_i, start_i)
                if start_i < getattr(self, 'edit_cursor_row', -1) <= end_i:
                    self.edit_cursor_row = start_i
                    self.edit_cursor_col = 0
                    self.edit_selection_start = None
                if getattr(self, 'edit_selection_start', None) and start_i < self.edit_selection_start[0] <= end_i:
                    self.edit_selection_start = None

            self._build_edit_visible_indices()

            
            if self.edit_cursor_row < len(self.edit_actual_to_visual) and self.edit_actual_to_visual[self.edit_cursor_row] == -1:
                for r in range(self.edit_cursor_row, -1, -1):
                    if r < len(self.edit_actual_to_visual) and self.edit_actual_to_visual[r] != -1:
                        self.edit_cursor_row = r
                        self.edit_cursor_col = 0

                        self.edit_selection_start = (r, 0)
                        break

            if anchor_actual != -1:
                new_v_idx = -1
                for i in range(anchor_actual, -1, -1):
                    if i < len(self.edit_actual_to_visual) and self.edit_actual_to_visual[i] != -1:
                        new_v_idx = self.edit_actual_to_visual[i]
                        break

                if new_v_idx != -1:
                    new_scroll = new_v_idx - (max_lines / 2.0)
                    max_scroll = max(0, len(self.edit_visible_indices) - max_lines)
                    self.edit_target_scroll_y = float(max(0, min(max_scroll, new_scroll)))
                    self.edit_scroll_y_float = self.edit_target_scroll_y
                    self.edit_scroll_y = int(self.edit_target_scroll_y)
        else:
            
            for start_i in folded:
                end_i = blocks.get(start_i, start_i)
                if getattr(self, 'selection_start', -1) is not None and start_i < self.selection_start <= end_i:
                    self.selection_start = start_i
                    self.selection_end = start_i

            self._build_visible_indices()
            self._update_search()

            
            if getattr(self, 'selection_start', None) is not None:
                if self.selection_start < len(self.actual_to_visual) and self.actual_to_visual[self.selection_start] == -1:
                    for i in range(self.selection_start, -1, -1):
                        if i < len(self.actual_to_visual) and self.actual_to_visual[i] != -1:
                            self.selection_start = i
                            self.selection_end = i
                            break

            if anchor_actual != -1:
                new_v_idx = -1
                for i in range(anchor_actual, -1, -1):
                    if i < len(self.actual_to_visual) and self.actual_to_visual[i] != -1:
                        new_v_idx = self.actual_to_visual[i]
                        break

                if new_v_idx != -1:
                    new_scroll = new_v_idx - (max_lines / 2.0)
                    max_scroll = max(0, len(self.visible_indices) - max_lines)
                    self.scroll_right_target = float(max(0, min(max_scroll, new_scroll)))
                    self.scroll_right_float = self.scroll_right_target
                    self.scroll_right = int(self.scroll_right_target)

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

    def _handle_editor_mouse(self, event, down=True):
        try:
            mx, my = event.pos

            
            if getattr(self, 'edit_replace_active', False):
                rects = self._get_replace_rects()
                if rects['panel'].collidepoint(mx, my):
                    if down:
                        if rects['btn_close'].collidepoint(mx, my):
                            self.edit_replace_active = False
                            self.edit_replace_focus = None
                        elif rects['find_box'].collidepoint(mx, my):
                            self.edit_replace_focus = 0
                        elif rects['rep_box'].collidepoint(mx, my):
                            self.edit_replace_focus = 1
                        elif rects['btn_next'].collidepoint(mx, my):
                            self._do_replace_find_next(1)
                        elif rects['btn_prev'].collidepoint(mx, my):
                            self._do_replace_find_next(-1)
                        elif rects['btn_rep'].collidepoint(mx, my):
                            self._do_replace_replace()
                        elif rects['btn_all'].collidepoint(mx, my):
                            self._do_replace_all()
                        elif rects['chk_case'].collidepoint(mx, my):
                            self.edit_replace_case = not getattr(self, 'edit_replace_case', False)
                        elif rects['chk_wrap'].collidepoint(mx, my):
                            self.edit_replace_wrap = not getattr(self, 'edit_replace_wrap', True)
                        elif rects['chk_dir'].collidepoint(mx, my):
                            self.edit_replace_dir = -getattr(self, 'edit_replace_dir', 1)
                    return True 

            
            if down and getattr(self, 'edit_replace_active', False) and getattr(self, 'edit_replace_focus', None) is not None:
                self.edit_replace_focus = None

            right_w = max(1, self.width - self.left_panel_width - self.minimap_width)
            pane_w = max(1, (right_w - self.GAP_WIDTH) // 2)
            pane_old_x = self.left_panel_width
            pane_new_x = pane_old_x + pane_w + self.GAP_WIDTH
            diff_y_start = self.title_bar_height + 25

            t = getattr(self, 'edit_anim_t', 1.0)
            editor_x_end = pane_old_x + 35
            editor_x = int(pane_new_x - (pane_new_x - editor_x_end) * t)
            editor_w = int(right_w - (editor_x - pane_old_x)) - 20
            text_offset = 60 + int(25 * t)

            
            visible_w = editor_w - text_offset - 15
            max_edit_scroll_x = max(0, getattr(self, 'max_edit_width', 0) - visible_w + 50)
            if max_edit_scroll_x > 0:
                scrollbar_h = 12
                editor_scrollbar_rect = pygame.Rect(editor_x + text_offset, diff_y_start + (self.height - diff_y_start - 5) - scrollbar_h - 5, editor_w - text_offset - 15, scrollbar_h)
                ratio = visible_w / max(1, getattr(self, 'max_edit_width', 0))
                thumb_w = min(50, max(15, int(editor_scrollbar_rect.width * ratio)))
                max_thumb_travel = editor_scrollbar_rect.width - thumb_w
                thumb_x = editor_scrollbar_rect.x + int((self.edit_scroll_x / max_edit_scroll_x) * max_thumb_travel)

                if editor_scrollbar_rect.collidepoint(mx, my):
                    if down:
                        self.is_dragging_editor_scroll_x = True
                        self._editor_scroll_x_offset = mx - thumb_x
                    return True

            is_in_bounds = (editor_x <= mx <= editor_x + editor_w) and (diff_y_start < my < self.height - 5)
            is_dragging = not down and getattr(self, 'edit_is_dragging', False)

            if is_in_bounds or is_dragging:
                
                clamped_my = max(diff_y_start, min(self.height - 6, my))
                scroll_y_float = getattr(self, 'edit_scroll_y_float', float(self.edit_scroll_y))
                start_v_idx = int(scroll_y_float)

                fractional_offset = (scroll_y_float - start_v_idx) * self.line_height
                click_v_idx = start_v_idx + int((clamped_my - diff_y_start + fractional_offset) // self.line_height)

                if 0 <= click_v_idx < len(self.edit_visible_indices):
                    actual_row = self.edit_visible_indices[click_v_idx]

                    
                    if is_in_bounds and not is_dragging and actual_row in getattr(self, 'edit_code_blocks', {}):
                        depth = getattr(self, 'edit_block_depths', {}).get(actual_row, 0)
                        box_x = editor_x + text_offset - 15 + (depth * 10)
                        if box_x - 4 <= mx <= box_x + 14:
                            if down:
                                offset = click_v_idx - scroll_y_float

                                if actual_row in getattr(self, 'edit_folded_blocks', set()):
                                    self.edit_folded_blocks.remove(actual_row)
                                else:
                                    self.edit_folded_blocks.add(actual_row)
                                    
                                    end_idx = getattr(self, 'edit_code_blocks', {}).get(actual_row, actual_row)
                                    if actual_row < getattr(self, 'edit_cursor_row', -1) <= end_idx:
                                        self.edit_cursor_row = actual_row
                                        self.edit_cursor_col = 0
                                        self.edit_selection_start = None
                                    if getattr(self, 'edit_selection_start', None) and actual_row < self.edit_selection_start[0] <= end_idx:
                                        self.edit_selection_start = None

                                self._build_edit_visible_indices()

                                new_v_idx = self.edit_actual_to_visual[actual_row]
                                if new_v_idx != -1:
                                    max_lines = (self.height - diff_y_start - 5) // self.line_height
                                    max_scroll = max(0, len(self.edit_visible_indices) - max_lines)
                                    self.edit_target_scroll_y = min(float(max_scroll), max(0.0, float(new_v_idx) - offset))
                                    self.edit_scroll_y_float = self.edit_target_scroll_y
                                    self.edit_scroll_y = int(self.edit_target_scroll_y)

                            return True

                    
                    if is_in_bounds and not is_dragging and editor_x <= mx < editor_x + text_offset - 55:
                        if down:
                            if not hasattr(self, 'edit_interest_points'):
                                self.edit_interest_points = set()
                            if actual_row in self.edit_interest_points:
                                self.edit_interest_points.remove(actual_row)
                            else:
                                self.edit_interest_points.add(actual_row)
                            self._run_linter()
                        return True

                    
                    elif is_in_bounds and not is_dragging and editor_x + text_offset - 55 <= mx < editor_x + text_offset - 5:
                        if down:
                            self.edit_flash_line_nums = 1.0
                            if hasattr(self, 'edit_interest_points') and self.edit_interest_points:
                                sorted_pts = sorted(list(self.edit_interest_points))
                                next_pt = None
                                for pt in sorted_pts:
                                    if pt > self.edit_cursor_row:
                                        next_pt = pt
                                        break
                                if next_pt is None:
                                    next_pt = sorted_pts[0]

                                self.edit_cursor_row = next_pt
                                self.edit_cursor_col = min(len(self.edit_lines[next_pt]), self.edit_cursor_col)

                                max_lines = (self.height - diff_y_start - 5) // self.line_height
                                v_idx = self.edit_actual_to_visual[next_pt]
                                if v_idx != -1:
                                    self.edit_target_scroll_y = max(0, min(len(self.edit_visible_indices) - max_lines, v_idx - (max_lines // 2)))
                                self._scroll_editor_to_cursor()
                        return True

                    
                    is_double_click = False
                    if down and getattr(event, 'type', None) == pygame.MOUSEBUTTONDOWN and getattr(event, 'button', None) == 1:
                        curr_time = time.time()
                        last_time = getattr(self, '_last_editor_click_time', 0.0)
                        last_pos = getattr(self, '_last_editor_click_pos', (0, 0))

                        time_diff = curr_time - last_time

                        if time_diff < 0.02:
                            
                            
                            is_double_click = getattr(self, '_last_was_double_click', False)
                        else:
                            dist = ((mx - last_pos[0])**2 + (my - last_pos[1])**2)**0.5
                            if time_diff < 0.40 and dist < 5:
                                is_double_click = True

                            self._last_was_double_click = is_double_click
                            self._last_editor_click_time = curr_time

                            self._last_editor_click_pos = (mx, my)

                    line_raw = self.edit_lines[actual_row]
                    rel_x = mx - editor_x - text_offset + self.edit_scroll_x

                    
                    raw_col = 0
                    for i in range(len(line_raw)):
                        prefix = line_raw[:i].replace('\t', '    ')
                        char_str = "    " if line_raw[i] == '\t' else line_raw[i]
                        current_px = self.font.size(prefix)[0]
                        char_w = self.font.size(char_str)[0]
                        if rel_x < current_px + (char_w / 2.0):
                            break
                        raw_col += 1

                    if is_double_click:
                        c_start = raw_col
                        if raw_col < len(line_raw) and line_raw[raw_col].isspace():
                            while c_start > 0 and line_raw[c_start-1].isspace():
                                c_start -= 1
                            c_end = raw_col
                            while c_end < len(line_raw) and line_raw[c_end].isspace():
                                c_end += 1
                        else:
                            while c_start > 0 and (line_raw[c_start-1].isalnum() or line_raw[c_start-1] == '_'):
                                c_start -= 1
                            c_end = raw_col
                            while c_end < len(line_raw) and (line_raw[c_end].isalnum() or line_raw[c_end] == '_'):
                                c_end += 1

                        if c_start == c_end and len(line_raw) > 0:
                            c_end = min(len(line_raw), c_start + 1)

                        self.edit_selection_start = (actual_row, c_start)
                        self.edit_cursor_row = actual_row
                        self.edit_cursor_col = c_end
                        self._scroll_editor_to_cursor()
                        return True

                    if down:
                        mods = pygame.key.get_mods()
                        if mods & pygame.KMOD_SHIFT:
                            if getattr(self, 'edit_selection_start', None) is None:
                                self.edit_selection_start = (self.edit_cursor_row, self.edit_cursor_col)
                        else:
                            self.edit_selection_start = None
                    else:
                        if getattr(self, 'edit_selection_start', None) is None:
                            self.edit_selection_start = (self.edit_cursor_row, self.edit_cursor_col)

                    self.edit_cursor_row = actual_row
                    self.edit_cursor_col = raw_col

                    
                    
                    if is_in_bounds:
                        self._scroll_editor_to_cursor()
                    elif is_dragging and mx > editor_x + editor_w:
                        self.edit_scroll_x = min(max_edit_scroll_x, self.edit_scroll_x + 10)
                    elif is_dragging and mx < editor_x + text_offset:
                        self.edit_scroll_x = max(0, self.edit_scroll_x - 10)

        except Exception as e:
            self._log(f"Error in _handle_editor_mouse: {e}\n{traceback.format_exc()}")

    def _show_modal_input(self, title: str, prompt: str, default_text: str = "", show_case_checkbox: bool = False):
        """Draws a custom, blocking input dialog over the Pygame UI for precise jumping."""
        bg_surface = self.screen.copy()
        dim_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dim_surface.fill((0, 0, 0, 180))
        bg_surface.blit(dim_surface, (0, 0))

        box_w = 340
        box_h = 100
        if show_case_checkbox:
            box_h += 30

        box_x = (self.width - box_w) // 2

        box_y = (self.height - box_h) // 2
        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        input_rect = pygame.Rect(box_x + 15, box_y + 55, box_w - 30, 26)

        chk_rect = pygame.Rect(box_x + 15, box_y + 90, 12, 12) if show_case_checkbox else None
        case_sensitive = False

        input_text = default_text
        cursor = len(input_text)
        sel_start = 0
        sel_end = len(input_text)

        clock = pygame.time.Clock()

        while True:
            mx, my = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return ("", False) if show_case_checkbox else ""
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if show_case_checkbox and chk_rect and chk_rect.collidepoint(mx, my):
                        case_sensitive = not case_sensitive
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return ("", False) if show_case_checkbox else ""
                    elif event.key == pygame.K_RETURN:
                        return (input_text, case_sensitive) if show_case_checkbox else input_text
                    input_text, cursor, sel_start, sel_end, _ = self._process_text_input_event(event, input_text, cursor, sel_start, sel_end)

            self.screen.blit(bg_surface, (0, 0))
            pygame.draw.rect(self.screen, (35, 35, 40), box_rect, border_radius=6)
            pygame.draw.rect(self.screen, (100, 100, 110), box_rect, 1, border_radius=6)

            title_surf = self.font_bold.render(title, True, (200, 200, 200))
            self.screen.blit(title_surf, (box_x + 15, box_y + 10))

            prompt_surf = self.font.render(prompt, True, (150, 150, 150))
            self.screen.blit(prompt_surf, (box_x + 15, box_y + 35))

            pygame.draw.rect(self.screen, (20, 20, 25), input_rect, border_radius=3)
            pygame.draw.rect(self.screen, (80, 80, 90), input_rect, 1, border_radius=3)

            disp_clip = pygame.Surface((input_rect.width - 10, input_rect.height), pygame.SRCALPHA)
            s = min(sel_start, sel_end)
            e = max(sel_start, sel_end)

            s_px = self.font.size(input_text[:s])[0]
            e_px = self.font.size(input_text[:e])[0]
            c_px = self.font.size(input_text[:cursor])[0]

            tx = 0
            if c_px > disp_clip.get_width() - 5:
                tx = disp_clip.get_width() - c_px - 5

            if s != e:
                pygame.draw.rect(disp_clip, (60, 100, 160), (tx + s_px, 2, e_px - s_px, input_rect.height - 4))

            txt_surf = self.font.render(input_text, True, (255, 255, 255))
            disp_clip.blit(txt_surf, (tx, (input_rect.height - txt_surf.get_height())//2))

            if s == e and time.time() % 1.0 < 0.5:
                pygame.draw.line(disp_clip, (255, 255, 255), (tx + c_px, 4), (tx + c_px, input_rect.height - 4))

            self.screen.blit(disp_clip, (input_rect.x + 5, input_rect.y))

            if show_case_checkbox:
                pygame.draw.rect(self.screen, (25, 30, 35), chk_rect, border_radius=2)
                pygame.draw.rect(self.screen, (100, 120, 150), chk_rect, 1, border_radius=2)
                if case_sensitive:
                    pygame.draw.line(self.screen, (150, 200, 255), (chk_rect.x + 2, chk_rect.centery), (chk_rect.centerx, chk_rect.bottom - 2), 2)
                    pygame.draw.line(self.screen, (150, 200, 255), (chk_rect.centerx, chk_rect.bottom - 2), (chk_rect.right - 2, chk_rect.top + 2), 2)
                lbl_surf = self.font.render("Case sensitive", True, (180, 190, 210))
                self.screen.blit(lbl_surf, (chk_rect.right + 8, chk_rect.centery - lbl_surf.get_height()//2))

            pygame.display.flip()
            clock.tick(60)

    def _draw_editor_pane(self, base_x, y_start, pane_w, pane_h):
        try:
            base_x = int(base_x)
            y_start = int(y_start)
            pane_w = int(pane_w)
            pane_h = int(pane_h)

            pygame.draw.rect(self.screen, (20, 22, 28), (base_x, y_start, pane_w, pane_h))
            max_lines = max(1, pane_h // self.line_height)

            sel = self._get_editor_selection_range()
            t = getattr(self, 'edit_anim_t', 1.0)

            
            text_offset = 60 + int(25 * t)

            
            scroll_y_float = getattr(self, 'edit_scroll_y_float', float(self.edit_scroll_y))
            start_v_idx = int(scroll_y_float)

            fractional_offset = (scroll_y_float - start_v_idx) * self.line_height

            
            panel_clip = pygame.Rect(base_x, y_start, pane_w, pane_h)
            text_clip = pygame.Rect(base_x + text_offset, y_start, max(1, pane_w - text_offset - 15), max(1, pane_h - 20))

            for v_idx in range(start_v_idx, min(len(self.edit_visible_indices), start_v_idx + max_lines + 2)):
                actual_idx = self.edit_visible_indices[v_idx]
                line_text = self.edit_lines[actual_idx]
                y = y_start + int((v_idx - start_v_idx) * self.line_height - fractional_offset)
                self.screen.set_clip(panel_clip)

                is_func_start = actual_idx in getattr(self, 'edit_code_blocks', {})
                if actual_idx == self.edit_cursor_row:
                    pygame.draw.rect(self.screen, (55, 65, 90), (base_x, y, pane_w, self.line_height))
                elif is_func_start and t > 0.1:
                    pygame.draw.rect(self.screen, (28, 32, 42), (base_x, y, pane_w, self.line_height))

                
                margin_x = base_x + text_offset - 10

                line_color = (int(70 * t), int(70 * t), int(85 * t))
                has_fold_box = actual_idx in getattr(self, 'edit_code_blocks', {}) and getattr(self, 'edit_block_depths', {}).get(actual_idx, 0) == 0

                if not has_fold_box:
                    pygame.draw.line(self.screen, line_color, (margin_x, y), (margin_x, y + self.line_height), 1)
                else:
                    box_y_center = y + (self.line_height // 2)
                    pygame.draw.line(self.screen, line_color, (margin_x, y), (margin_x, box_y_center - 6), 1)
                    pygame.draw.line(self.screen, line_color, (margin_x, box_y_center + 6), (margin_x, y + self.line_height), 1)

                
                if hasattr(self, 'edit_interest_points') and actual_idx in self.edit_interest_points and t > 0.1:
                    pygame.draw.circle(self.screen, (80, 220, 100), (base_x + text_offset - 65, y + self.line_height // 2), 5)

                
                if t > 0.05:
                    is_line_selected = actual_idx == self.edit_cursor_row
                    if sel:
                        (r1, c1), (r2, c2) = sel
                        if r1 <= actual_idx <= r2:
                            is_line_selected = True

                    ln_color = (240, 240, 240) if is_line_selected else (100, 100, 120)
                    ln_surf = self.font.render(str(actual_idx + 1), True, ln_color)
                    self.screen.blit(ln_surf, (base_x + text_offset - 50, y + 2))

                self.screen.set_clip(text_clip)

                if sel:
                    (r1, c1), (r2, c2) = sel
                    if r1 <= actual_idx <= r2:
                        sc1 = c1 if actual_idx == r1 else 0
                        sc2 = c2 if actual_idx == r2 else len(line_text)

                        prefix = line_text[:sc1].replace('\t', '    ')
                        sel_text = line_text[sc1:sc2].replace('\t', '    ')

                        px1, _ = self.font.size(prefix)
                        px2, _ = self.font.size(sel_text)

                        if r1 != r2 and actual_idx != r2:
                            px2 += 10

                        sel_rect = pygame.Rect(base_x + text_offset - self.edit_scroll_x + px1, y, max(1, px2), self.line_height)
                        pygame.draw.rect(self.screen, (60, 80, 140), sel_rect)

                line_fg = (235, 195, 115) if is_func_start else (220, 220, 220)
                t_surf = self._render_syntax_line(line_text, line_fg)

                
                q = getattr(self, 'search_text', '').lower()
                if q and len(q) >= 1:
                    match_idx = line_text.lower().find(q)
                    if match_idx != -1:
                        prefix = line_text[:match_idx].replace('\t', '    ')
                        match_str = line_text[match_idx:match_idx+len(q)].replace('\t', '    ')
                        px_w, _ = self.font.size(prefix)
                        m_w = max(1, self.font.size(match_str)[0])

                        hl_surf = pygame.Surface((m_w, max(1, self.line_height)), pygame.SRCALPHA)

                        is_active_match = False
                        if getattr(self, 'search_results', []) and getattr(self, 'search_current_idx', -1) >= 0:
                            if actual_idx == self.search_results[self.search_current_idx]:
                                is_active_match = True

                        if is_active_match:
                            hl_surf.fill((255, 120, 0, 255))
                            pygame.draw.rect(hl_surf, (255, 200, 0), hl_surf.get_rect(), 1)
                        else:
                            hl_surf.fill((200, 200, 0, 255))

                        match_text_surf = self.font.render(match_str, True, (20, 20, 25))
                        hl_surf.blit(match_text_surf, (0, 0))

                        t_surf_copy = pygame.Surface(t_surf.get_size(), pygame.SRCALPHA)
                        t_surf_copy.blit(t_surf, (0, 0))
                        t_surf_copy.blit(hl_surf, (px_w, 0))
                        t_surf = t_surf_copy

                
                q_rep = getattr(self, 'edit_replace_find', "")
                case_sens = getattr(self, 'edit_replace_case', False)
                if getattr(self, 'edit_replace_active', False) and q_rep:
                    idx = line_text.find(q_rep) if case_sens else line_text.lower().find(q_rep.lower())
                    if idx != -1:
                        prefix = line_text[:idx].replace('\t', '    ')
                        match_str = line_text[idx:idx+len(q_rep)].replace('\t', '    ')
                        px_w, _ = self.font.size(prefix)
                        m_w = max(1, self.font.size(match_str)[0])

                        hl_surf = pygame.Surface((m_w, max(1, self.line_height)), pygame.SRCALPHA)

                        
                        is_active_match = False
                        if sel and sel[0] != sel[1]:
                            if sel[0][0] == actual_idx and sel[0][1] == idx and sel[1][1] == idx + len(q_rep):
                                is_active_match = True

                        if is_active_match:
                            hl_surf.fill((120, 220, 100, 255))
                            pygame.draw.rect(hl_surf, (150, 255, 150), hl_surf.get_rect(), 1)
                        else:
                            hl_surf.fill((100, 150, 80, 255))

                        match_text_surf = self.font.render(match_str, True, (20, 20, 25))
                        hl_surf.blit(match_text_surf, (0, 0))

                        t_surf_copy = pygame.Surface(t_surf.get_size(), pygame.SRCALPHA)
                        t_surf_copy.blit(t_surf, (0, 0))
                        t_surf_copy.blit(hl_surf, (px_w, 0))
                        t_surf = t_surf_copy

                self.screen.blit(t_surf, (base_x + text_offset - self.edit_scroll_x, y + 2))

                
                err_msg = next((msg for r, msg in getattr(self, 'edit_linter_errors', []) if r == actual_idx), None)
                if err_msg and t > 0.5:
                    text_w, _ = self.font.size(line_text.replace('\t', '    '))
                    start_x = int(base_x + text_offset - self.edit_scroll_x)
                    end_x = int(start_x + max(40, min(text_w, pane_w - text_offset - 40)))

                    points = []
                    for z_x in range(start_x, end_x, 4):
                        z_y = y + self.line_height - (1 if (z_x // 4) % 2 == 0 else 3)
                        points.append((z_x, z_y))
                    if len(points) > 1:
                        pygame.draw.lines(self.screen, (240, 80, 80), False, points, 2)

                    q_rect = pygame.Rect(end_x + 8, y + 2, 16, self.line_height - 4)
                    pygame.draw.rect(self.screen, (200, 60, 60), q_rect, border_radius=3)
                    q_surf = self.font_bold.render("?", True, (255, 255, 255))
                    self.screen.blit(q_surf, (q_rect.centerx - q_surf.get_width()//2, q_rect.centery - q_surf.get_height()//2))

                    mx, my = pygame.mouse.get_pos()
                    if q_rect.collidepoint(mx, my):
                        self._linter_tooltip = (mx, my, err_msg)

                if actual_idx == self.edit_cursor_row and (time.time() % 0.8 < 0.4):
                    pre_text = line_text[:self.edit_cursor_col].replace('\t', '    ')
                    px_w, _ = self.font.size(pre_text)
                    cursor_x = base_x + text_offset + px_w - self.edit_scroll_x
                    pygame.draw.line(self.screen, (255, 60, 60), (cursor_x, y + 2), (cursor_x, y + self.line_height - 2), 4)

            self.screen.set_clip(None)

            
            flash_val = getattr(self, 'edit_flash_line_nums', 0.0)
            if flash_val > 0.0 and t > 0.1:
                flash_alpha = int(180 * flash_val)
                flash_surf = pygame.Surface((45, max(1, pane_h)), pygame.SRCALPHA)
                flash_surf.fill((255, 255, 200, flash_alpha))
                self.screen.blit(flash_surf, (base_x + text_offset - 55, y_start))

            for v_idx in range(start_v_idx, min(len(self.edit_visible_indices), start_v_idx + max_lines + 2)):
                actual_idx = self.edit_visible_indices[v_idx]
                if actual_idx in getattr(self, 'edit_code_blocks', {}):
                    y = y_start + int((v_idx - start_v_idx) * self.line_height - fractional_offset)
                    depth = getattr(self, 'edit_block_depths', {}).get(actual_idx, 0)
                    box_x = base_x + text_offset - 15 + (depth * 10)
                    box_rect = pygame.Rect(box_x, y + (self.line_height // 2) - 4, 9, 9)
                    is_folded = actual_idx in getattr(self, 'edit_folded_blocks', set())
                    pygame.draw.rect(self.screen, (150, 150, 150), box_rect, 1)
                    pygame.draw.line(self.screen, (200, 200, 200), (box_rect.left + 2, box_rect.centery), (box_rect.right - 3, box_rect.centery))
                    if is_folded:
                        pygame.draw.line(self.screen, (200, 200, 200), (box_rect.centerx, box_rect.top + 2), (box_rect.centerx, box_rect.bottom - 3))

            
            visible_w = pane_w - text_offset - 15
            max_edit_scroll_x = max(0, getattr(self, 'max_edit_width', 0) - visible_w + 50)
            if max_edit_scroll_x > 0:
                scrollbar_h = 12
                editor_scrollbar_rect = pygame.Rect(base_x + text_offset, y_start + pane_h - scrollbar_h - 5, pane_w - text_offset - 15, scrollbar_h)
                ratio = visible_w / max(1, getattr(self, 'max_edit_width', 0))
                thumb_w = min(50, max(15, int(editor_scrollbar_rect.width * ratio)))
                max_thumb_travel = editor_scrollbar_rect.width - thumb_w
                thumb_x = editor_scrollbar_rect.x + int((self.edit_scroll_x / max_edit_scroll_x) * max_thumb_travel)

                
                track_surf = pygame.Surface((editor_scrollbar_rect.width, editor_scrollbar_rect.height), pygame.SRCALPHA)
                track_surf.fill((18, 18, 18, 51))
                self.screen.blit(track_surf, (editor_scrollbar_rect.x, editor_scrollbar_rect.y))

                
                thumb_surf = pygame.Surface((thumb_w, editor_scrollbar_rect.height), pygame.SRCALPHA)
                thumb_surf.fill((255, 255, 255, 51))
                pygame.draw.rect(thumb_surf, (200, 200, 200, 51), (0, 0, thumb_w, editor_scrollbar_rect.height), 1)
                self.screen.blit(thumb_surf, (thumb_x, editor_scrollbar_rect.y))

            
            flash = getattr(self, 'edit_save_btn_flash', 0.0)
            border_r = min(255, int(220 * t) + int(100 * flash))
            border_g = int(40 * t)
            border_b = int(40 * t)
            thickness = max(2, int(2 + (3 * flash)))
            pygame.draw.rect(self.screen, (border_r, border_g, border_b), (base_x, y_start, self.width - base_x - 1, pane_h), thickness)

            
            if getattr(self, 'edit_replace_active', False):
                rects = self._get_replace_rects()

                
                p_rect = rects['panel']
                pygame.draw.rect(self.screen, (40, 45, 55), p_rect, border_radius=6)
                pygame.draw.rect(self.screen, (100, 120, 150), p_rect, 1, border_radius=6)

                title = self.font_bold.render("Find & Replace", True, (220, 230, 255))
                self.screen.blit(title, (p_rect.x + 10, p_rect.y + 10))

                
                msg = getattr(self, 'edit_replace_msg', "")
                if msg:
                    msg_surf = self.font.render(msg, True, (255, 200, 100))
                    self.screen.blit(msg_surf, (p_rect.right - msg_surf.get_width() - 35, p_rect.y + 10))

                
                c_rect = rects['btn_close']
                mx, my = pygame.mouse.get_pos()
                hover_c = c_rect.collidepoint(mx, my)
                pygame.draw.rect(self.screen, (200, 60, 60) if hover_c else (150, 50, 50), c_rect, border_radius=2)
                x_surf = self.font_bold.render("×", True, (255, 255, 255))
                self.screen.blit(x_surf, (c_rect.centerx - x_surf.get_width()//2, c_rect.centery - x_surf.get_height()//2 - 1))

                
                for box_name, var_name, lbl, focus_idx in [
                    ('find_box', 'edit_replace_find', 'Find:', 0),
                    ('rep_box', 'edit_replace_rep', 'Replace:', 1)
                ]:
                    b_rect = rects[box_name]
                    is_focused = getattr(self, 'edit_replace_focus', None) == focus_idx

                    lbl_surf = self.font.render(lbl, True, (180, 190, 210))
                    self.screen.blit(lbl_surf, (b_rect.x - lbl_surf.get_width() - 5, b_rect.centery - lbl_surf.get_height()//2))

                    pygame.draw.rect(self.screen, (25, 30, 35), b_rect, border_radius=3)
                    pygame.draw.rect(self.screen, (120, 150, 200) if is_focused else (80, 90, 110), b_rect, 1, border_radius=3)

                    txt = getattr(self, var_name, "")

                    txt_clip = pygame.Surface((b_rect.width - 10, b_rect.height), pygame.SRCALPHA)
                    txt_surf = self.font.render(txt, True, (255, 255, 255))

                    c, s, e = getattr(self, 'edit_replace_cursors', [(len(txt), 0, 0), (len(txt), 0, 0)])[focus_idx]
                    c = min(len(txt), max(0, c))
                    s = min(len(txt), max(0, s))
                    e = min(len(txt), max(0, e))

                    sel_s = min(s, e)
                    sel_e = max(s, e)

                    c_px = self.font.size(txt[:c])[0]
                    s_px = self.font.size(txt[:sel_s])[0]
                    e_px = self.font.size(txt[:sel_e])[0]

                    tw = txt_surf.get_width()
                    tx = 0
                    if is_focused and c_px > txt_clip.get_width() - 5:
                        tx = txt_clip.get_width() - c_px - 5

                    if is_focused and sel_s != sel_e:
                        pygame.draw.rect(txt_clip, (60, 100, 160), (tx + s_px, 2, e_px - s_px, b_rect.height - 4))

                    txt_clip.blit(txt_surf, (tx, (b_rect.height - txt_surf.get_height())//2))

                    if is_focused and sel_s == sel_e and (time.time() % 1.0 < 0.5):
                        cx = tx + c_px
                        pygame.draw.line(txt_clip, (255, 255, 255), (cx, 4), (cx, b_rect.height - 4))

                    self.screen.blit(txt_clip, (b_rect.x + 5, b_rect.y))

                
                for btn_name, lbl in [('btn_next', 'Next'), ('btn_prev', 'Prev'), ('btn_rep', 'Replace'), ('btn_all', 'All')]:
                    b_rect = rects[btn_name]
                    hover = b_rect.collidepoint(mx, my)
                    pygame.draw.rect(self.screen, (70, 90, 120) if hover else (50, 70, 90), b_rect, border_radius=3)
                    pygame.draw.rect(self.screen, (100, 130, 170), b_rect, 1, border_radius=3)
                    t_surf = self.font.render(lbl, True, (240, 245, 255))
                    self.screen.blit(t_surf, (b_rect.centerx - t_surf.get_width()//2, b_rect.centery - t_surf.get_height()//2))

                
                case_val = getattr(self, 'edit_replace_case', False)
                wrap_val = getattr(self, 'edit_replace_wrap', True)
                dir_val = getattr(self, 'edit_replace_dir', 1)

                for chk_name, val, lbl in [('chk_case', case_val, 'Match Case'), ('chk_wrap', wrap_val, 'Wrap')]:
                    c_rect = rects[chk_name]
                    pygame.draw.rect(self.screen, (25, 30, 35), c_rect, border_radius=2)
                    pygame.draw.rect(self.screen, (100, 120, 150), c_rect, 1, border_radius=2)
                    if val:
                        pygame.draw.line(self.screen, (150, 200, 255), (c_rect.x + 2, c_rect.centery), (c_rect.centerx, c_rect.bottom - 2), 2)
                        pygame.draw.line(self.screen, (150, 200, 255), (c_rect.centerx, c_rect.bottom - 2), (c_rect.right - 2, c_rect.top + 2), 2)
                    l_surf = self.font.render(lbl, True, (180, 190, 210))
                    self.screen.blit(l_surf, (c_rect.right + 5, c_rect.centery - l_surf.get_height()//2))

                
                d_rect = rects['chk_dir']
                pygame.draw.rect(self.screen, (25, 30, 35), d_rect, border_radius=2)
                pygame.draw.rect(self.screen, (100, 120, 150), d_rect, 1, border_radius=2)

                if dir_val == 1:
                    pygame.draw.polygon(self.screen, (150, 200, 255), [(d_rect.x+2, d_rect.y+3), (d_rect.right-2, d_rect.y+3), (d_rect.centerx, d_rect.bottom-3)])
                else:
                    pygame.draw.polygon(self.screen, (150, 200, 255), [(d_rect.x+2, d_rect.bottom-3), (d_rect.right-2, d_rect.bottom-3), (d_rect.centerx, d_rect.y+3)])

                dl_surf = self.font.render("Dir", True, (180, 190, 210))
                self.screen.blit(dl_surf, (d_rect.right + 5, d_rect.centery - dl_surf.get_height()//2))

            
            elif getattr(self, 'edit_search_summary_active', False):
                sw = pane_w // 2
                sh = min(300, 45 + len(self.edit_search_summary_results) * 25)
                sx = base_x + pane_w - sw - 20
                sy = y_start + 10

                self.edit_search_summary_rect = pygame.Rect(sx, sy, sw, sh)
                pygame.draw.rect(self.screen, (35, 35, 40), self.edit_search_summary_rect, border_radius=5)
                pygame.draw.rect(self.screen, (100, 150, 200), self.edit_search_summary_rect, 1, border_radius=5)

                title = self.font_bold.render(f"Find All: '{self.search_text}' ({len(self.edit_search_summary_results)} hits)", True, (200, 220, 255))
                self.screen.blit(title, (sx + 10, sy + 10))
                pygame.draw.line(self.screen, (100, 150, 200), (sx, sy + 35), (sx + sw, sy + 35))

                list_y = sy + 40
                scroll = getattr(self, 'edit_search_summary_scroll', 0)

                max_visible = (sh - 45) // 25
                visible_res = self.edit_search_summary_results[scroll:scroll+max_visible]
                mx, my = pygame.mouse.get_pos()

                for i, (row_idx, line_text) in enumerate(visible_res):
                    item_rect = pygame.Rect(sx + 5, list_y + i*25, sw - 10, 25)
                    if item_rect.collidepoint(mx, my):
                        pygame.draw.rect(self.screen, (60, 80, 120), item_rect, border_radius=3)

                    ln_surf = self.font_bold.render(f"{row_idx + 1}:", True, (150, 150, 150))
                    self.screen.blit(ln_surf, (item_rect.x + 5, item_rect.y + 5))

                    txt = line_text.strip().replace('\t', '    ')

                    max_chars = (sw - 70) // max(1, self.font.size("A")[0])
                    if len(txt) > max_chars: txt = txt[:max_chars-3] + "..."
                    txt_surf = self.font.render(txt, True, (220, 220, 220))
                    self.screen.blit(txt_surf, (item_rect.x + ln_surf.get_width() + 10, item_rect.y + 5))

                if len(self.edit_search_summary_results) > max_visible:
                    track_rect = pygame.Rect(sx + sw - 8, sy + 40, 4, sh - 45)
                    pygame.draw.rect(self.screen, (50, 50, 55), track_rect)
                    ratio = max_visible / len(self.edit_search_summary_results)
                    thumb_h = max(10, int(track_rect.height * ratio))
                    thumb_y = track_rect.y + int((scroll / (len(self.edit_search_summary_results) - max_visible)) * (track_rect.height - thumb_h))
                    pygame.draw.rect(self.screen, (100, 100, 110), (track_rect.x, thumb_y, 4, thumb_h))

            elif getattr(self, 'edit_search_summary_results', []):
                bw, bh = 180, 19
                bx = base_x + pane_w - bw - 20
                by = y_start + 5
                self.edit_search_btn_rect = pygame.Rect(bx, by, bw, bh)
                mx, my = pygame.mouse.get_pos()
                hover = self.edit_search_btn_rect.collidepoint(mx, my)
                pygame.draw.rect(self.screen, (60, 80, 120) if hover else (40, 50, 70), self.edit_search_btn_rect, border_radius=4)
                pygame.draw.rect(self.screen, (100, 150, 200), self.edit_search_btn_rect, 1, border_radius=4)
                lbl = self.font.render("Previous search results", True, (255, 255, 255))
                self.screen.blit(lbl, (bx + (bw - lbl.get_width())//2, by + 5))
        except Exception as e:
            self._log(f"Error in _draw_editor_pane: {e}\n{traceback.format_exc()}")

    def _activate_replace(self):
        self.context_menu = None
        self.edit_replace_active = True
        self.edit_replace_focus = 0 
        self.edit_replace_msg = ""

        if not hasattr(self, 'edit_replace_find'): self.edit_replace_find = ""
        if not hasattr(self, 'edit_replace_rep'): self.edit_replace_rep = ""
        if not hasattr(self, 'edit_replace_case'): self.edit_replace_case = False
        if not hasattr(self, 'edit_replace_wrap'): self.edit_replace_wrap = True
        if not hasattr(self, 'edit_replace_dir'): self.edit_replace_dir = 1

        self.edit_replace_cursors = [(len(self.edit_replace_find), 0, len(self.edit_replace_find)), (len(self.edit_replace_rep), 0, len(self.edit_replace_rep))]

        sel = self._get_editor_selection_range()
        if sel and sel[0] != sel[1]:
            (r1, c1), (r2, c2) = sel
            if r1 == r2:
                self.edit_replace_find = self.edit_lines[r1][c1:c2]
                self.edit_replace_cursors[0] = (len(self.edit_replace_find), 0, len(self.edit_replace_find))

    def _handle_editor_keydown(self, event):
        mods = pygame.key.get_mods()
        ctrl = mods & pygame.KMOD_CTRL
        shift = mods & pygame.KMOD_SHIFT

        
        if (ctrl and event.key == pygame.K_q) or (ctrl and event.key == pygame.K_w) or (event.mod & pygame.KMOD_ALT and event.key == pygame.K_F4):
            self.running = False
            return

        
        if ctrl and event.key == pygame.K_h:
            self._activate_replace()
            return

        
        if getattr(self, 'edit_replace_active', False) and getattr(self, 'edit_replace_focus', None) is not None:
            focus = self.edit_replace_focus
            if event.key == pygame.K_ESCAPE:
                self.edit_replace_active = False
                self.edit_replace_focus = None
                return
            elif event.key == pygame.K_TAB:
                self.edit_replace_focus = 1 - focus
                return
            elif event.key == pygame.K_RETURN:
                if mods & pygame.KMOD_SHIFT:
                    self._do_replace_find_next(-1)
                else:
                    self._do_replace_find_next(1)
                return
            else:
                text = self.edit_replace_find if focus == 0 else self.edit_replace_rep
                c, s, e = getattr(self, 'edit_replace_cursors', [(len(self.edit_replace_find), 0, len(self.edit_replace_find)), (len(self.edit_replace_rep), 0, len(self.edit_replace_rep))])[focus]
                text, c, s, e, handled = self._process_text_input_event(event, text, c, s, e)
                if handled:
                    if focus == 0: self.edit_replace_find = text
                    else: self.edit_replace_rep = text
                    self.edit_replace_cursors[focus] = (c, s, e)
                    return
            return 

        
        if event.key == pygame.K_ESCAPE:
            self.edit_save_btn_flash = 1.0
            self.edit_show_discard_btn = True
            return

        
        if (ctrl and event.key == pygame.K_x) or (shift and event.key == pygame.K_DELETE):
            try:
                self._register_undo_point('force')
                sel = self._get_editor_selection_range()
                if sel:
                    (r1, c1), (r2, c2) = sel
                    
                    r1 = max(0, min(len(self.edit_lines) - 1, r1))
                    r2 = max(0, min(len(self.edit_lines) - 1, r2))
                    c1 = max(0, min(len(self.edit_lines[r1]), c1))
                    c2 = max(0, min(len(self.edit_lines[r2]), c2))

                    if r1 == r2:
                        text = self.edit_lines[r1][c1:c2]
                    else:
                        text_parts = [self.edit_lines[r1][c1:]]
                        for r in range(r1+1, r2):
                            text_parts.append(self.edit_lines[r])
                        text_parts.append(self.edit_lines[r2][:c2])
                        text = "\n".join(text_parts)
                    try:
                        pyperclip.copy(text)
                    except Exception as e:
                        self._log(f"Editor cut copy failed: {e}")
                    self._delete_editor_selection()
                else:
                    if 0 <= self.edit_cursor_row < len(self.edit_lines):
                        line_text = self.edit_lines[self.edit_cursor_row]
                        try:
                            pyperclip.copy(line_text + "\n")
                        except Exception as e:
                            self._log(f"Editor cut copy failed: {e}")
                        if len(self.edit_lines) > 1:
                            del self.edit_lines[self.edit_cursor_row]
                            self._shift_editor_folds(self.edit_cursor_row, -1)
                            self.edit_cursor_row = min(len(self.edit_lines) - 1, self.edit_cursor_row)
                            self.edit_cursor_col = 0
                        else:
                            self.edit_lines[0] = ""
                            self.edit_cursor_col = 0
                self._run_linter()
                self._scroll_editor_to_cursor()
            except Exception as e:
                self._log(f"Exception in Cut operation: {e}\n{traceback.format_exc()}")
            return

        
        if ctrl and event.key == pygame.K_g:
            self._prompt_goto_line()
            return

        
        if ctrl and event.key == pygame.K_f:
            initial_query = ""
            sel = self._get_editor_selection_range()
            if sel and sel[0][0] == sel[1][0]:
                r, c1 = sel[0]
                _, c2 = sel[1]
                if c1 != c2:
                    initial_query = self.edit_lines[r][c1:c2]

            if not initial_query:
                initial_query = getattr(self, 'search_text', '')

            res = self._show_modal_input("Find all in File", "Enter search term:", initial_query, show_case_checkbox=True)
            if res:
                q, case_sens = res
                if q:
                    self.search_text = q

                    self.edit_search_summary_results = []
                    if case_sens:
                        for i, line in enumerate(self.edit_lines):
                            if q in line:
                                self.edit_search_summary_results.append((i, line))
                    else:
                        q_low = q.lower()
                        for i, line in enumerate(self.edit_lines):
                            if q_low in line.lower():
                                self.edit_search_summary_results.append((i, line))
                    self.edit_search_summary_active = True
                    self.edit_search_summary_scroll = 0
            return

        prev_cursor = (self.edit_cursor_row, self.edit_cursor_col)
        row = self.edit_cursor_row
        col = self.edit_cursor_col
        lines = self.edit_lines

        
        if ctrl and event.key == pygame.K_z:
            if shift: self._redo_editor_state()
            else: self._undo_editor_state()
            self._last_undo_group_type = None  
            self._run_linter()
            return
        if ctrl and event.key == pygame.K_y:
            self._redo_editor_state()
            self._last_undo_group_type = None  
            self._run_linter()
            return

        
        if ctrl and event.key == pygame.K_a:
            self.edit_selection_start = (0, 0)
            self.edit_cursor_row = len(self.edit_lines) - 1
            self.edit_cursor_col = len(self.edit_lines[-1])
            self._scroll_editor_to_cursor()
            return

        
        if (ctrl and event.key == pygame.K_c) or (ctrl and event.key in (pygame.K_INSERT, pygame.K_KP0)):
            sel = self._get_editor_selection_range()
            if sel:
                (r1, c1), (r2, c2) = sel
                if r1 == r2:
                    text = self.edit_lines[r1][c1:c2]
                else:
                    text_parts = [self.edit_lines[r1][c1:]]
                    for r in range(r1+1, r2): text_parts.append(self.edit_lines[r])
                    text_parts.append(self.edit_lines[r2][:c2])
                    text = "\n".join(text_parts)
                try:
                    pyperclip.copy(text)
                except Exception as e:
                    self._log(f"Editor copy failed: {e}")
            else:
                try:
                    pyperclip.copy(self.edit_lines[self.edit_cursor_row] + "\n")
                except Exception as e:
                    self._log(f"Editor copy failed: {e}")
            return

        
        if (ctrl and event.key == pygame.K_v) or (shift and event.key in (pygame.K_INSERT, pygame.K_KP0)):
            self._register_undo_point('force')
            self._delete_editor_selection()
            row = self.edit_cursor_row
            col = self.edit_cursor_col
            try:
                paste_text = pyperclip.paste() or ""

                if paste_text:
                    paste_text = paste_text.replace('\r\n', '\n').replace('\r', '\n')
                    p_lines = paste_text.split('\n')
                    if len(p_lines) == 1:
                        lines[row] = lines[row][:col] + p_lines[0] + lines[row][col:]
                        self.edit_cursor_col += len(p_lines[0])
                    else:
                        head = lines[row][:col]
                        tail = lines[row][col:]
                        lines[row] = head + p_lines[0]
                        for i, pl in enumerate(p_lines[1:], 1):
                            lines.insert(row + i, pl)
                        lines.insert(row + len(p_lines) - 1, p_lines[-1] + tail)
                        self._shift_editor_folds(row + 1, len(p_lines) - 1)
                        self.edit_cursor_row += len(p_lines) - 1
                        self.edit_cursor_col = len(p_lines[-1])
                self._run_linter()
                self._scroll_editor_to_cursor()
            except Exception as e:
                self._log(f"Editor Paste operation failed gracefully: {e}\n{traceback.format_exc()}")
            return

        
        is_nav_key = event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT,
                                   pygame.K_HOME, pygame.K_END, pygame.K_PAGEUP, pygame.K_PAGEDOWN)
        if is_nav_key:
            if shift:
                if self.edit_selection_start is None:
                    self.edit_selection_start = prev_cursor
            else:
                self.edit_selection_start = None

        
        v_idx = self.edit_actual_to_visual[row] if row < len(self.edit_actual_to_visual) else 0

        if event.key == pygame.K_UP:
            new_v_idx = max(0, v_idx - 1)
            self.edit_cursor_row = self.edit_visible_indices[new_v_idx]
            self.edit_cursor_col = min(len(lines[self.edit_cursor_row]), col)

        elif event.key == pygame.K_DOWN:
            new_v_idx = min(len(self.edit_visible_indices) - 1, v_idx + 1)
            self.edit_cursor_row = self.edit_visible_indices[new_v_idx]
            self.edit_cursor_col = min(len(lines[self.edit_cursor_row]), col)

        elif event.key == pygame.K_LEFT:
            if ctrl:
                self.edit_cursor_row, self.edit_cursor_col = self._get_next_word_pos(row, col, -1)
            else:
                if col > 0:
                    self.edit_cursor_col -= 1
                elif row > 0:
                    new_v_idx = max(0, v_idx - 1)
                    self.edit_cursor_row = self.edit_visible_indices[new_v_idx]
                    self.edit_cursor_col = len(lines[self.edit_cursor_row])

        elif event.key == pygame.K_RIGHT:
            if ctrl:
                self.edit_cursor_row, self.edit_cursor_col = self._get_next_word_pos(row, col, 1)
            else:
                if col < len(lines[row]):
                    self.edit_cursor_col += 1
                elif row < len(lines) - 1:
                    new_v_idx = min(len(self.edit_visible_indices) - 1, v_idx + 1)
                    self.edit_cursor_row = self.edit_visible_indices[new_v_idx]
                    self.edit_cursor_col = 0

        elif event.key == pygame.K_HOME:
            if ctrl:
                self.edit_cursor_row = 0
                self.edit_cursor_col = 0
            else:
                self.edit_cursor_col = 0

        elif event.key == pygame.K_END:
            if ctrl:
                self.edit_cursor_row = len(lines) - 1
                self.edit_cursor_col = len(lines[-1])
            else:
                self.edit_cursor_col = len(lines[self.edit_cursor_row])

        elif event.key == pygame.K_PAGEUP:
            new_v_idx = max(0, v_idx - 20)
            self.edit_cursor_row = self.edit_visible_indices[new_v_idx]
            self.edit_cursor_col = min(len(lines[self.edit_cursor_row]), col)

        elif event.key == pygame.K_PAGEDOWN:
            new_v_idx = min(len(self.edit_visible_indices) - 1, v_idx + 20)
            self.edit_cursor_row = self.edit_visible_indices[new_v_idx]
            self.edit_cursor_col = min(len(lines[self.edit_cursor_row]), col)

        
        elif event.key == pygame.K_BACKSPACE:
            if not self._delete_editor_selection():
                if ctrl:
                    self._register_undo_point('backspacing')
                    r, c = self._get_next_word_pos(row, col, -1)
                    if r == row:
                        lines[row] = lines[row][:c] + lines[row][col:]
                        self.edit_cursor_col = c
                    elif r < row:
                        self._register_undo_point('force')
                        lines[r] = lines[r][:c] + lines[row][col:]
                        del lines[r+1:row+1]
                        self.edit_cursor_row = r
                        self.edit_cursor_col = c
                else:
                    if col > 0:
                        self._register_undo_point('backspacing')
                        lines[row] = lines[row][:col-1] + lines[row][col:]
                        self.edit_cursor_col -= 1
                    elif row > 0:
                        self._register_undo_point('force')
                        prev_len = len(lines[row-1])
                        lines[row-1] += lines[row]
                        lines.pop(row)
                        self._shift_editor_folds(row, -1)
                        self.edit_cursor_row -= 1
                        self.edit_cursor_col = prev_len
            self._run_linter()

        
        elif event.key == pygame.K_DELETE:
            if not self._delete_editor_selection():
                if ctrl:
                    self._register_undo_point('deleting')
                    r, c = self._get_next_word_pos(row, col, 1)
                    if r == row:
                        lines[row] = lines[row][:col] + lines[row][c:]
                    elif r > row:
                        self._register_undo_point('force')
                        lines[row] = lines[row][:col] + lines[r][c:]
                        del lines[row+1:r+1]
                else:
                    if col < len(lines[row]):
                        self._register_undo_point('deleting')
                        lines[row] = lines[row][:col] + lines[row][col+1:]
                    elif row < len(lines) - 1:
                        self._register_undo_point('force')
                        lines[row] += lines[row+1]
                        lines.pop(row+1)
                        self._shift_editor_folds(row + 1, -1)
            self._run_linter()

        
        elif event.key == pygame.K_RETURN:
            self._register_undo_point('force')
            self._delete_editor_selection()
            row = self.edit_cursor_row
            col = self.edit_cursor_col

            tail = lines[row][col:]
            lines[row] = lines[row][:col]

            indent = len(lines[row]) - len(lines[row].lstrip())
            base_indent = lines[row][:indent]

            lines.insert(row + 1, base_indent + tail)
            self._shift_editor_folds(row + 1, 1)
            self.edit_cursor_row += 1
            self.edit_cursor_col = len(base_indent)
            self._run_linter()

        
        elif event.key == pygame.K_TAB:
            self._register_undo_point('force')
            sel = self._get_editor_selection_range()

            if sel:
                r1, r2 = sel[0][0], sel[1][0]
            else:
                r1, r2 = row, row

            is_multi_line = (r1 != r2)
            has_folded_block = any(r in getattr(self, 'edit_folded_blocks', set()) for r in range(r1, r2 + 1))

            if is_multi_line or has_folded_block:
                expanded_r2 = r2
                for r in range(r1, r2 + 1):
                    if r in getattr(self, 'edit_folded_blocks', set()):
                        block_end = self.edit_code_blocks.get(r, r)
                        if block_end > expanded_r2:
                            expanded_r2 = block_end
                r2 = expanded_r2

                for r in range(r1, r2 + 1):
                    if shift:
                        if lines[r].startswith("    "): lines[r] = lines[r][4:]
                        elif lines[r].startswith("\t"): lines[r] = lines[r][1:]
                    else:
                        lines[r] = "    " + lines[r]

                if shift:
                    if self.edit_selection_start:
                        self.edit_selection_start = (self.edit_selection_start[0], max(0, self.edit_selection_start[1] - 4))
                    self.edit_cursor_col = max(0, self.edit_cursor_col - 4)
                else:
                    if self.edit_selection_start:
                        self.edit_selection_start = (self.edit_selection_start[0], self.edit_selection_start[1] + 4)
                    self.edit_cursor_col += 4
            else:
                if shift:
                    if lines[row][:col].endswith("    "):
                        lines[row] = lines[row][:col-4] + lines[row][col:]
                        self.edit_cursor_col -= 4
                    elif lines[row][:col].endswith("\t"):
                        lines[row] = lines[row][:col-1] + lines[row][col:]
                        self.edit_cursor_col -= 1
                else:
                    self._delete_editor_selection()
                    row = self.edit_cursor_row
                    col = self.edit_cursor_col
                    lines[row] = lines[row][:col] + "    " + lines[row][col:]
                    self.edit_cursor_col += 4
            self._run_linter()

        
        else:
            if event.unicode.isprintable() and len(event.unicode) > 0:
                g_type = 'space' if event.unicode in (' ', '\t') else 'typing'
                self._register_undo_point(g_type)
                self._delete_editor_selection()
                row = self.edit_cursor_row
                col = self.edit_cursor_col
                lines[row] = lines[row][:col] + event.unicode + lines[row][col:]
                self.edit_cursor_col += len(event.unicode)
                self._run_linter()

        self._scroll_editor_to_cursor()

    def _handle_keydown_event(self, event):
        mods = pygame.key.get_mods()

        
        if getattr(self, 'search_active', False):
            if not hasattr(self, 'search_cursor_pos') or self.search_cursor_pos > len(self.search_text):
                self.search_cursor_pos = len(self.search_text)
            if not hasattr(self, 'search_sel_start'):
                self.search_sel_start = 0
            if not hasattr(self, 'search_sel_end'):
                self.search_sel_end = 0

            if event.key == pygame.K_RETURN:
                if self.search_results:
                    if mods & pygame.KMOD_SHIFT:
                        self.search_current_idx = (self.search_current_idx - 1) % len(self.search_results)
                    else:
                        self.search_current_idx = (self.search_current_idx + 1) % len(self.search_results)
                    self._jump_to_search_result()
                return
            elif event.key == pygame.K_ESCAPE:
                self.search_active = False
                return
            elif event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_PAGEUP, pygame.K_PAGEDOWN):
                self.search_active = False
                
                pass
            else:
                self.search_text, self.search_cursor_pos, self.search_sel_start, self.search_sel_end, handled = self._process_text_input_event(
                    event, self.search_text, self.search_cursor_pos, self.search_sel_start, self.search_sel_end
                )
                if handled:
                    self._update_search()
                    return

        
        if getattr(self, 'is_editing', False):
            self._handle_editor_keydown(event)
            return

        
        if event.key == pygame.K_ESCAPE:
            self.running = False
        elif event.key == pygame.K_PAGEUP:
            mx, my = pygame.mouse.get_pos()
            pane = self._get_pane_for_x(mx)
            if pane == "left":
                self.scroll_left = max(0, self.scroll_left - 20)
            else:
                if event.mod & pygame.KMOD_SHIFT:
                    self._move_selection(-20)
                else:
                    if not hasattr(self, 'scroll_right_target'): self.scroll_right_target = float(self.scroll_right)
                    self.scroll_right_target = max(0.0, self.scroll_right_target - 20.0)
        elif event.key == pygame.K_PAGEDOWN:
            mx, my = pygame.mouse.get_pos()
            pane = self._get_pane_for_x(mx)
            if pane == "left":
                max_l = max(0, len(self.render_list) - ((self.height - (self.title_bar_height + 25) - 25) // self.tree_row_height))
                self.scroll_left = max(0, min(max_l, self.scroll_left + 20))
            else:
                if event.mod & pygame.KMOD_SHIFT:
                    self._move_selection(20)
                else:
                    if not hasattr(self, 'scroll_right_target'): self.scroll_right_target = float(self.scroll_right)

                    max_lines = (self.height - (self.title_bar_height + 25)) // self.line_height
                    self.scroll_right_target = min(float(max(0, len(self.visible_indices) - max_lines)), self.scroll_right_target + 20.0)
        elif event.key == pygame.K_UP:
            if event.mod & pygame.KMOD_ALT:
                self._jump_to_next_diff(-1)
            elif event.mod & pygame.KMOD_SHIFT:
                self._move_selection(-1)
            else:
                if not hasattr(self, 'scroll_right_target'): self.scroll_right_target = float(self.scroll_right)
                self.scroll_right_target = max(0.0, self.scroll_right_target - 1.0)
        elif event.key == pygame.K_DOWN:
            if event.mod & pygame.KMOD_ALT:
                self._jump_to_next_diff(1)
            elif event.mod & pygame.KMOD_SHIFT:
                self._move_selection(1)
            else:
                if not hasattr(self, 'scroll_right_target'): self.scroll_right_target = float(self.scroll_right)

                max_lines = (self.height - (self.title_bar_height + 25)) // self.line_height
                max_r = max(0, len(self.visible_indices) - max_lines)
                self.scroll_right_target = min(float(max_r), self.scroll_right_target + 1.0)
        elif event.key == pygame.K_HOME:
            if event.mod & pygame.KMOD_SHIFT:
                self._move_selection(-len(self.visible_indices))
            else:
                self.scroll_right_target = 0.0
        elif event.key == pygame.K_END:
            max_lines = (self.height - (self.title_bar_height + 25)) // self.line_height
            max_r = max(0, len(self.visible_indices) - max_lines)
            if event.mod & pygame.KMOD_SHIFT:
                self._move_selection(len(self.visible_indices))
            else:
                self.scroll_right_target = float(max_r)
        elif event.key == pygame.K_LEFT:
            if not hasattr(self, 'scroll_right_x_target'):
                self.scroll_right_x_target = float(self.scroll_right_x)
            self.scroll_right_x_target = max(0.0, self.scroll_right_x_target - 80.0)
        elif event.key == pygame.K_RIGHT:
            right_w = max(1, self.width - self.left_panel_width - self.minimap_width)
            pane_w = max(1, (right_w - self.GAP_WIDTH) // 2)
            visible_w = pane_w - 65
            max_scroll_x = max(0, getattr(self, 'max_right_width', 0) - visible_w + 50)
            if not hasattr(self, 'scroll_right_x_target'):
                self.scroll_right_x_target = float(self.scroll_right_x)
            self.scroll_right_x_target = min(float(max_scroll_x), self.scroll_right_x_target + 80.0)
        elif event.key == pygame.K_f and (event.mod & pygame.KMOD_CTRL):
            self._activate_search()
        elif event.key == pygame.K_g and (event.mod & pygame.KMOD_CTRL):
            self._prompt_goto_line()
        elif (event.key == pygame.K_c and (event.mod & pygame.KMOD_CTRL)) or (event.key == pygame.K_INSERT and (event.mod & pygame.KMOD_CTRL)):
            self._copy_selection()

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

    def _jump_to_search_result(self):
        if not self.search_results: return

        target_idx = self.search_results[self.search_current_idx]

        if getattr(self, 'is_editing', False):
            self.edit_cursor_row = target_idx
            q = getattr(self, 'search_text', '').lower()
            match_col = self.edit_lines[target_idx].lower().find(q)
            self.edit_cursor_col = max(0, match_col)

            
            if match_col != -1:
                self.edit_selection_start = (target_idx, match_col)
                self.edit_cursor_col = match_col + len(q)

            
            self._build_edit_visible_indices()

            unfolded = False
            for start_i, end_i in getattr(self, 'edit_code_blocks', {}).items():
                if start_i <= target_idx <= end_i:
                    if start_i in getattr(self, 'edit_folded_blocks', set()):
                        self.edit_folded_blocks.remove(start_i)
                        unfolded = True

            if unfolded or not getattr(self, 'edit_visible_indices', []):
                self._build_edit_visible_indices()

            diff_y_start = self.title_bar_height + 25

            max_lines = (self.height - diff_y_start - 5) // self.line_height
            v_idx = self.edit_actual_to_visual[target_idx] if target_idx < len(self.edit_actual_to_visual) else -1
            if v_idx != -1:
                self.edit_target_scroll_y = float(max(0, min(len(self.edit_visible_indices) - max_lines, v_idx - (max_lines // 2))))
            self._scroll_editor_to_cursor()
        else:
            unfolded = False
            for start_i, end_i in getattr(self, 'code_blocks', {}).items():
                if start_i <= target_idx <= end_i:
                    if start_i in getattr(self, 'folded_blocks', set()):
                        self.folded_blocks.remove(start_i)
                        unfolded = True

            if unfolded or not getattr(self, 'visible_indices', []):
                self._build_visible_indices()

            v_idx = self.actual_to_visual[target_idx] if target_idx < len(self.actual_to_visual) else -1
            if v_idx != -1:
                diff_y_start = self.title_bar_height + 25

                max_lines = (self.height - diff_y_start) // self.line_height
                max_scroll = max(0, len(self.visible_indices) - max_lines)
                target_scroll = float(max(0, min(max_scroll, v_idx - (max_lines // 2))))
                self.scroll_right_target = target_scroll
                self.scroll_right_float = target_scroll
                self.scroll_right = int(target_scroll)

    def _copy_current_file_to_clipboard(self):
        self.context_menu = None
        if getattr(self, 'is_editing', False):
            clean_lines = self.edit_lines[:-4] if len(self.edit_lines) >= 4 else self.edit_lines
            text = "\n".join(clean_lines) + "\n"
            try:
                pyperclip.copy(text)
                self._log("Copied current edited text to clipboard.")
            except Exception as e:
                self._log(f"Failed to copy edited text to clipboard: {e}")
        else:
            if hasattr(self, 'active_file_path') and self.active_file_path:
                text = self._read_file_text(self.active_file_path)
                if text:
                    try:
                        pyperclip.copy(text)
                        self._log("Copied current file to clipboard.")
                    except Exception as e:
                        self._log(f"Failed to copy current file to clipboard: {e}")

    def _attach_current_file_to_compose(self):
        self.context_menu = None
        if getattr(self, 'is_editing', False):
            if hasattr(self, 'active_file_path') and self.active_file_path:
                try:
                    clean_lines = self.edit_lines[:-4] if len(self.edit_lines) >= 4 else self.edit_lines
                    with open(self.active_file_path, 'w', encoding='utf-8', newline='\n') as f:
                        f.write("\n".join(clean_lines) + "\n")
                    self._log("Saved editor changes to disk before attaching.")
                except Exception as e:
                    self._log(f"Failed to save editor changes before attach: {e}")

        if hasattr(self, 'active_file_path') and self.active_file_path:
            self._attach_to_compose({'full_path': self.active_file_path, 'backup_reference': ""})

    def _copy_editor_function(self, block):
        """Copies the physical lines of a specific code block from the editor directly to the clipboard."""
        self.context_menu = None
        b_start, b_end = block
        if 0 <= b_start < len(self.edit_lines) and 0 <= b_end < len(self.edit_lines):
            
            clean_lines = self.edit_lines[b_start : min(len(self.edit_lines) - 4, b_end + 1)]
            if clean_lines:
                try:
                    pyperclip.copy("\n".join(clean_lines))
                    self._log(f"Copied editor function scope (Lines {b_start+1}-{b_end+1}) to clipboard.")
                except Exception as e:
                    self._log(f"Failed to copy editor function: {e}")

    def _handle_mouse_motion_event(self, event):
        mx, my = event.pos
        pane = self._get_pane_for_x(mx)

        if getattr(self, 'is_editing', False):
            if getattr(self, 'is_dragging_editor_scroll_x', False):
                if not pygame.mouse.get_pressed()[0]:
                    self.is_dragging_editor_scroll_x = False
                else:
                    right_w = max(1, self.width - self.left_panel_width - self.minimap_width)
                    pane_w = max(1, (right_w - self.GAP_WIDTH) // 2)
                    pane_old_x = self.left_panel_width
                    pane_new_x = pane_old_x + pane_w + self.GAP_WIDTH
                    t = getattr(self, 'edit_anim_t', 1.0)
                    editor_x_end = pane_old_x + 35
                    editor_x = int(pane_new_x - (pane_new_x - editor_x_end) * t)
                    editor_w = int(right_w - (editor_x - pane_old_x)) - 20
                    text_offset = 25 + int(40 * t)
                    visible_w = editor_w - text_offset - 15
                    max_edit_scroll_x = max(0, getattr(self, 'max_edit_width', 0) - visible_w + 50)

                    scrollbar_h = 12
                    diff_y_start = self.title_bar_height + 25
                    pane_h = self.height - diff_y_start - 5
                    editor_scrollbar_rect = pygame.Rect(editor_x + text_offset, diff_y_start + pane_h - scrollbar_h - 5, editor_w - text_offset - 15, scrollbar_h)

                    ratio = visible_w / max(1, getattr(self, 'max_edit_width', 0))
                    thumb_w = min(50, max(15, int(editor_scrollbar_rect.width * ratio)))
                    max_thumb_travel = editor_scrollbar_rect.width - thumb_w

                    travel_ratio = (mx - editor_scrollbar_rect.x - getattr(self, '_editor_scroll_x_offset', thumb_w / 2)) / max(1, max_thumb_travel)
                    self.edit_scroll_x = max(0, min(max_edit_scroll_x, int(travel_ratio * max_edit_scroll_x)))
            elif getattr(self, 'edit_is_dragging', False):
                if not pygame.mouse.get_pressed()[0]:
                    self.edit_is_dragging = False
                else:
                    self._handle_editor_mouse(event, down=False)
            elif self.is_dragging_minimap:
                self._scroll_to_minimap(my)
            elif getattr(self, '_is_dragging', False) and getattr(self, 'hwnd', None) and os.name == 'nt':
                pt = wintypes.POINT()
                ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
                new_x = pt.x - getattr(self, '_drag_offset_x', 0)
                new_y = pt.y - getattr(self, '_drag_offset_y', 0)
                ctypes.windll.user32.SetWindowPos(self.hwnd, 0, new_x, new_y, 0, 0, 0x0001 | 0x0004)
            return

        if getattr(self, 'is_dragging_scroll_x', False):
            if not pygame.mouse.get_pressed()[0]:
                self.is_dragging_scroll_x = False
            else:
                right_w = max(1, self.width - self.left_panel_width - self.minimap_width)
                pane_w = max(1, (right_w - self.GAP_WIDTH) // 2)
                pane_old_x = self.left_panel_width
                pane_new_x = pane_old_x + pane_w + self.GAP_WIDTH
                visible_w = pane_w - 65
                max_scroll_x = max(0, getattr(self, 'max_right_width', 0) - visible_w + 50)

                scrollbar_width = pane_w - 65
                ratio = visible_w / max(1, getattr(self, 'max_right_width', 0))
                thumb_w = min(50, max(15, int(scrollbar_width * ratio)))
                max_thumb_travel = scrollbar_width - thumb_w

                travel_ratio = (mx - (pane_new_x + 60) - getattr(self, '_scroll_x_drag_offset', thumb_w / 2)) / max(1, max_thumb_travel)
                self.scroll_right_x = max(0, min(max_scroll_x, int(travel_ratio * max_scroll_x)))

        if pane in ("old", "new") and my > (self.title_bar_height + 25):
            scroll_r_float = getattr(self, 'scroll_right_float', float(self.scroll_right))
            start_v_idx = int(scroll_r_float)

            fractional_offset = (scroll_r_float - start_v_idx) * self.line_height
            v_idx = start_v_idx + int((my - (self.title_bar_height + 25) + fractional_offset) // self.line_height)

            if 0 <= v_idx < len(self.visible_indices):
                self.hovered_line_idx = self.visible_indices[v_idx]
                self.hovered_line_pane = pane
            else:
                self.hovered_line_idx = None
                self.hovered_line_pane = None
        else:
            self.hovered_line_idx = None
            self.hovered_line_pane = None

        if getattr(self, '_is_dragging', False) and getattr(self, 'hwnd', None) and os.name == 'nt':
            pt = wintypes.POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
            new_x = pt.x - getattr(self, '_drag_offset_x', 0)
            new_y = pt.y - getattr(self, '_drag_offset_y', 0)
            ctypes.windll.user32.SetWindowPos(self.hwnd, 0, new_x, new_y, 0, 0, 0x0001 | 0x0004)

     
        if hasattr(self, '_mouse_down_origin') and self._mouse_down_origin:
            ox, oy = self._mouse_down_origin

            dist = ((mx - ox)**2 + (my - oy)**2)**0.5
            if dist > 5 and not self.is_dragging_minimap:
                self.is_selecting = True

        if getattr(self, 'is_selecting', False) and pane in ("old", "new") and my > (self.title_bar_height + 25):
            scroll_r_float = getattr(self, 'scroll_right_float', float(self.scroll_right))
            start_v_idx = int(scroll_r_float)

            fractional_offset = (scroll_r_float - start_v_idx) * self.line_height
            v_idx = start_v_idx + int((my - (self.title_bar_height + 25) + fractional_offset) // self.line_height)

            v_idx = max(0, min(v_idx, len(self.visible_indices) - 1))
            if len(self.visible_indices) > 0:
                self.selection_end = self.visible_indices[v_idx]

    def _handle_mouse_button_up_event(self, event):
        if event.button == 1:
            self.is_selecting = False
            self._is_dragging = False
            self.is_dragging_minimap = False
            self._mouse_down_origin = None
            self.edit_is_dragging = False
            self.is_dragging_scroll_x = False
            self.is_dragging_editor_scroll_x = False

    def _handle_mouse_wheel_event(self, event):
        mx, my = pygame.mouse.get_pos()
        pane = self._get_pane_for_x(mx)

        if getattr(self, 'is_editing', False) and getattr(self, 'edit_search_summary_active', False) and getattr(self, 'edit_search_summary_rect', pygame.Rect(0,0,0,0)).collidepoint(mx, my):
            sh = min(300, 45 + len(self.edit_search_summary_results) * 25)

            max_visible = (sh - 45) // 25
            max_s = max(0, len(self.edit_search_summary_results) - max_visible)
            self.edit_search_summary_scroll = max(0, min(max_s, getattr(self, 'edit_search_summary_scroll', 0) - event.y))
            return

       

if __name__ == "__main__":
    
    appdata = os.environ.get('APPDATA', '')
    if appdata:
        log_dir = os.path.join(appdata, "CodeStitcher")
        os.makedirs(log_dir, exist_ok=True)
    else:
        if getattr(sys, "frozen", False) or "__compiled__" in globals():
            log_dir = os.path.dirname(os.path.abspath(sys.executable))
        else:
            log_dir = os.path.dirname(os.path.abspath(__file__))

    log_path = os.path.join(log_dir, "stitch_viewer_debug.log")

    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] --- STITCH VIEWER PROCESS EXECUTING ---\n")
            f.write(f"[{time.strftime('%H:%M:%S')}] sys.argv: {sys.argv}\n")
    except Exception:
        pass

    try:
        if "--from-stitcher" not in sys.argv:
            try:
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(f"[{time.strftime('%H:%M:%S')}] FATAL: --from-stitcher flag missing. Execution aborted.\n")
            except: pass
            sys.exit(0)

        
        def _get_arg(flag, type_conv=str, default=None):
            try:
                if flag in sys.argv:
                    return type_conv(sys.argv[sys.argv.index(flag) + 1])
            except (IndexError, ValueError):
                pass
            return default

        parent_pid_arg = _get_arg("--parent-pid", int)

        monitors = []
        for i, arg in enumerate(sys.argv):
            if arg == "--monitor" and i + 1 < len(sys.argv):
                monitors.append(sys.argv[i+1])

        pos_x, pos_y = None, None
        pos_str = _get_arg("--pos")
        if pos_str and "," in pos_str:
            pos_x, pos_y = pos_str.split(",", 1)

        height = _get_arg("--height")
        font_name = _get_arg("--font")
        font_size = _get_arg("--font-size")
        is_pro_arg = "--pro" in sys.argv

        app = StitchViewerApp(
            parent_pid=parent_pid_arg,
            monitors=monitors,
            pos_x=pos_x,
            pos_y=pos_y,
            height=height,
            font_name=font_name,
            font_size=font_size,
            is_pro=is_pro_arg
        )
        app.run()

    except BaseException as e:
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] FATAL UNCAUGHT EXCEPTION:\n{traceback.format_exc()}\n")
        except: pass
