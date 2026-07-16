# Part 7 of diff_viewer_final.py
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

def _get_editor_selection_range(self):
    if not getattr(self, 'edit_selection_start', None):
        return None
    r1, c1 = self.edit_selection_start
    r2, c2 = self.edit_cursor_row, self.edit_cursor_col

    if r1 > r2 or (r1 == r2 and c1 > c2):
        return ((r2, c2), (r1, c1))
    return ((r1, c1), (r2, c2))

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

def _handle_mouse_button_up_event(self, event):
    if event.button == 1:
        self.is_selecting = False
        self._is_dragging = False
        self.is_dragging_minimap = False
        self._mouse_down_origin = None
        self.edit_is_dragging = False
        self.is_dragging_scroll_x = False
        self.is_dragging_editor_scroll_x = False

