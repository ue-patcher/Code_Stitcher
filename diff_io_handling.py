# Part 4 of diff_viewer_final.py
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

def _get_entry_id(self, entry):
    return entry.get("timestamp", "") + entry.get("backup_reference", "")

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

def _replace_multiple_functions(self, blocks):
    for b_start, b_end in blocks:
        self._replace_function(b_start)

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

