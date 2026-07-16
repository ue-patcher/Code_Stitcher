# Part 2 of diff_viewer_final.py
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

