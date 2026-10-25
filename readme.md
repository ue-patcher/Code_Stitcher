<div align="center">

# _AI CODE STITCHER_

**The AST-aware bridge between large language models and a local codebase.**

Copy an LLM reply, or pipe a terminal. Stitcher strips the chatter, finds the file, matches indentation, unrolls truncations, and writes a rollback snapshot.

[![Release](https://img.shields.io/badge/release-v3.58-0B6BCB?style=flat-square)](https://aicodestitcher.com)
[![Engines](https://img.shields.io/badge/engines-Unreal%20%7C%20Unity%20%7C%20Godot-C2410C?style=flat-square)](https://aicodestitcher.com)
[![CLI](https://img.shields.io/badge/cli-Python%203-3776AB?style=flat-square)](https://aicodestitcher.com)
[![Desktop](https://img.shields.io/badge/desktop-Windows%20x64%20%7C%20SDL2-24292F?style=flat-square)](https://aicodestitcher.com)

[Overview](#overview) | [Release notes](#whats-new-in-v358) | [Terminal Bridge (CLI)](#terminal-bridge-cli) | [How it works](#how-it-works) | [Architecture](#architecture) | [Keybindings](#keybindings) | [Changelog](#changelog)

</div>

---

## Overview

An LLM reply is not a patch. It arrives wrapped in prose, fenced in markdown, and often cut short with `// ... rest of your code goes here ...`. Applying it means finding the file, the scope, the indent, the brackets, and the imports by hand.

Stitcher removes that step.

Leave the desktop runtime running. Copy any LLM response, or pipe stdout into `stitch`. The engine reads structure, matches the file's indent style, resolves fuzzy anchors, unrolls truncations, and writes to disk. Every write stores a local snapshot (`Ctrl+Z`), and the side-by-side diff is one key away (`F10`).

| Without Stitcher | With Stitcher |
| :--- | :--- |
| Hunt the file, paste, fix indent, balance brackets | Clipboard or pipe lands on the matching scope |
| Truncations and `... existing code ...` left behind as comments | Accordion stitch expands them against disk |
| A bad apply turns into a git scramble | Instant `.bak` rollback, visual revert by line or hunk |
| Autonomous agents guess blindly at file layouts | Agents use `stitch analyze` to get exact AST mapping |

---

## What's new in v3.58

### Ternary Inline-Expression Grammar Protection
The Universal Grammar Checker has been upgraded to ignore control-flow branch keywords (`else`, `elif`, `except`, `catch`, `finally`) unless they are strictly followed by a colon (`:`). This eliminates false-positive structural rejections on inline Python ternary operators (`... if ... else ...`) and multi-line method arguments.

### Deep Hint Scourer & Anti-Hallucination Filter
The file-hint extraction pipeline features a multi-pass `HintScourer`. The engine scours conversational prose, markdown headers, Aider pre-lines, and code comments with strict language consistency (Python code will **never** match stray `.c` or `.h` hallucinations). Integrated entropy and consonant-cluster filters eliminate random keyboard-mashing and hallucinated file names from hijacking the patcher.

### Internal Aider Hunk Target Switching
The Aider/Unified parser scours *inside* `<<<<<<< SEARCH` and `======= REPLACE` blocks for embedded `# File: path/to/file` headers. When an LLM bunches multiple file targets into a single diff stream without standard pre-headers, the parser dynamically switches file contexts and flushes pending hunks to disk on the fly.

### Plaintext & Conversational Multi-File Batching
Added a zero-indent **Plaintext Boundary Injector**. When copying multi-file patches without markdown code fences, the processor identifies conversational file headers (`Update gun.gd:`, `// player.gd`) and injects block boundaries on the fly—bringing plain-text batch copy reliability to parity with markdown blocks.

---

## Terminal Bridge (CLI)

`stitch_cli.py` talks to the running desktop runtime over non-blocking localhost IPC. It provides powerful tools for standard terminal users and autonomous LLM agents.

| Command | Purpose |
| :--- | :--- |
| `stitch attach [FILES...]` | Attach project files into the Compose window (`F7`) |
| `stitch patch <file> [patch]`| Bypass the auto-router and apply a patch directly to a precise file |
| `stitch analyze <file>` | Zero-dependency AST parser returning a JSON map of the file layout |
| `stitch stream` | Stream live engine activity and AST diagnostics to the terminal |
| `<cmd> \| stitch patch ...` | Pipe patches, diffs, or LLM output directly to disk |

### Practical Workflows & Examples

**1. Attach context for the composer**
```powershell
stitch attach src\player.gd src\combat\hitbox.gd
```

**2. Autonomous Agent file introspection**
Agents can query the structure of a file to get total line counts, class counts, function counts, and exact start/end line numbers for every code block in JSON format.
```powershell
stitch analyze src/core/engine.py
```
*(Returns: `{"total_lines": 412, "metrics": {"num_classes": 2, "num_functions": 14}, "classes": [...], "functions": [...]}`)*

**3. Autonomous Agent target forcing**
Bypass the fuzzy finder and force a patch to apply to a specific file.
```powershell
cat my_patch.txt | stitch patch src/core/engine.py
```

**4. Pipe a local model straight to disk**
```powershell
ollama run codellama "Add input validation to update_user in user_service.py" | stitch
```

**5. Watch writes, sanity checks, and confidence**
```powershell
stitch stream
```

---

## How it works

| Step | Phase | Description |
| :---: | :--- | :--- |
| 1 | Arm | `F9`, or a pipe into `stitch`. |
| 2 | Capture | Copy from the browser or IDE, or pipe stdout. |
| 3 | Place | Classifies the block (Aider patch, unified diff, drop-in method, headless snippet) and resolves file plus offset. |
| 4 | Apply | Placeholders reconcile, indent adapts, seams are checked, and the write is snapshotted. Review opens the adjuster with the best candidate already set. |

---

## Architecture

| Component | Responsibility |
| :--- | :--- |
| Code Stitcher | Memory index, syntax trees, clipboard/IPC watch, adjuster, indent normalize, accordion stitch, seam guard, AST check, `.bak` under `.ep_backups/`. |
| Stitch Viewer | SDL2 side-by-side diff, revert by line / block / hunk, inline edit on `Esc`, ephemeral session bookmarks, session timeline. Independent of Git. |
| Stitch CLI | `stitch_cli.py`. Agentic AST introspection (JSON), direct patching, and local model stdout piping into the desktop engine. |

### Engine subsystems

| Subsystem | Responsibility |
| :--- | :--- |
| Clipboard and IPC watcher | Memory and localhost sockets. |
| Interactive Adjuster | Move the anchor, cycle candidates, merge declarations, check brackets, then write. |
| Indent normalizer | Matches the file and resolves Aider hunk indent deltas. |
| Accordion stitcher | Expands `// ... existing code ...` against disk. |
| Seam hazard guard | Shared container leaks, split brackets, indent cliffs. |
| AST validator | Syntax check before commit. |
| Snapshot engine | Instant `.bak` files under hidden `.ep_backups/`. |

---

## Keybindings

### Global

| Key | Action | Description |
| :--- | :--- | :--- |
| `F9` | Arm / Disarm | Toggle the background clipboard listener. |
| `Shift+F9` | Tactical Arm | Intercept a copy and confirm the destination. |
| `F8` | Filelock | Pin AST targeting to one file. |
| `F7` | Compose | Open the prompt composer with context attached. |
| `F10` | Viewer | Open the SDL2 diff viewer. |
| `Ctrl+Z` | Rollback | Revert the last injection from the local snapshot. |
| `Ctrl+Y` | Redo | Re-apply a reverted injection. |

### Interactive Adjuster

Active when alignment is sent to review.

| Key | Action | Description |
| :--- | :--- | :--- |
| `Up` / `Down` | Shift target | Move the insert or overwrite anchor by one line. |
| `Left` / `Right` | Cycle candidates | Jump between ranked match locations. |
| `<` / `>` | Indent | Nudge the snippet in indentation steps (tabs or spaces matching target). |
| `[` / `]` | Start seam | Expand or contract the top of the cut (auto-snaps to statement limits). |
| `-` / `+` | End seam | Expand or contract the bottom of the cut (auto-snaps to statement limits). |
| `m` | Smart merge | Keep disk declarations and variables the model omitted. |
| `u` | Unhide / fold | Expand a folded preview (over 45 lines). |
| `o` | Diff / pure | Colorized diff or raw source. |
| `s` | Search | Jump to an anchor in the target file. |
| `e` | Edit snippet | Inline edit before commit. |
| `Enter` | Commit | Write the aligned patch. |
| `Esc` | Skip | Drop this snippet and continue. |
| `0` | Cancel all | Abort the whole operation. |

---

## Changelog

<details open>
<summary><strong>v3.19 to v3.58</strong></summary>

**v3.58**
- **Ternary Inline-Expression Grammar Protection:** Updated the Universal Grammar Checker to ignore branch keywords (`else`, `elif`, etc.) unless strictly followed by a colon (`:`), stopping false-positive rejections on Python inline ternary operators (`... if ... else ...`).
- **Deep Hint Scourer Engine:** Overhauled hint extraction into a unified, multi-pass engine that scours conversational text, markdown tags, and comments while filtering out keyboard mashing and high-entropy hallucinations.
- **Language-Consistent Validation:** Patches strictly cross-reference code syntax with file extensions; Python code will never accidentally match `.c` or `.h` hallucinations unless verified on disk.
- **In-Hunk File Resolution:** Aider and Unified diff parsers actively scan for `# File:` directives *inside* search/replace bodies, automatically re-routing hunks to separate files mid-stream.
- **Plaintext Multi-File Slicing:** Added a Plaintext Boundary Injector that detects conversational file headers in raw unformatted text, matching the multi-file batch reliability of markdown fences.
- **Clean-Slate Arming:** Pressing `F9` or `Shift+F9` performs a physical clipboard wipe and internal memory purge to prevent old clipboard code from triggering unintended patches.
- **Tolerant File Boundaries:** Multi-file slice parsers now tolerate conversational trailing prose on boundary headers (e.g., `--- START OF FILE player.gd --- easy huh?`).

**v3.56**
- **Robust Requests Migration:** Fully replaced all legacy `urllib` code across the entire codebase with the modern `requests` library, eliminating weird SSL handshake drops and Windows proxy connection quirks.
- **Root-Domain Streamlining:** Migrated telemetry, lease checking, and pings directly to `https://aicodestitcher.com`, simplifying routing and resolving edge-case SSL subdomain mismatches.

**v3.55**
- **Multi-Line AST Bracket Intelligence:** The AST grammar checker now perfectly respects multiline bracketed constructs (`[`, `{`, `(`). It suspends indentation-cliff enforcement while inside open data structures, resolving false-positive rejections on unindented arrays/dicts.
- **Strict HTTPS Validation:** Replaced all hardcoded, plaintext HTTP IPs with secure HTTPS domains. The auto-updater now enforces strict SSL verification, killing arbitrary RCE vulnerabilities from MITM attacks.
- **Path Traversal Lockdown:** Upgraded target resolution to use `os.path.commonpath`, preventing malicious or hallucinated clipboard paths (`../`) from overwriting system files outside the active workspace.
- **Win32 UI Deadlock Fix:** Implemented `CoInitialize` wrapper for secondary background threads attempting to spawn Tkinter modals, stopping deep COM deadlocks while the main Pygame loop is rendering.
- **OS Resource Safety:** All Windows Registry operations spanning massive codebase scans are now enclosed in secure context managers, resolving handle leaks.
- **Empty File Atomic Backups:** Headless snippets routed into empty placeholder files now correctly trigger the atomic `.bak` snapshot system before writing.

**v3.54**
- **CLI Subcommand Architecture:** Converted the terminal bridge to use robust subcommands (`attach`, `patch`, `analyze`, `stream`).
- **Agentic File Introspection:** `stitch analyze <file>` now returns exact line counts, class counts, and function start/end boundary line numbers in JSON format.
- **Agentic Direct Patching:** `stitch patch <file>` safely overrides the fuzzy finder and anchors the patch directly to the target file.
- **Accordion Tail Guards:** A new `CRITICAL TAIL GUARD` prevents the headless accordion stitcher from stretching down to swallow unrelated trailing control flow logic (`if`, `return`, `break`) that was missing from the patch.
- **Aider Destruction Guards:** Added a `CRITICAL DESTRUCTION GUARD` that aggressively penalizes the fuzzy match confidence if the patch attempts to silently delete a core control flow keyword without an ellipsis marker.
- **Clipboard Trigger Fix:** Repaired an issue where the clipboard watcher could mistakenly trigger while disarmed if an active snippet overwrite incidentally swallowed the `self.armed` check.

**v3.53**
- **Godot Tab Normalization:** All snippet insertion pipelines (`_inject_new_function_into_file`, `_apply_candidate_blocks`, `_align_headless_snippet`) detect `.gd` extensions and existing tab usage to emit native `\t` indentation.
- **Godot Inline Property Accessors:** Updated `accessor_pat` in `_heal_godot_property_indentation` to match single-line setters/getters (e.g. `set(v): value = v`).
- **GDScript Preprocessing Pipeline Integration:** Linked `_heal_godot_property_indentation` directly into the GDScript workflow rather than restricting it to Python.
- **Interactive Tab Adjustments:** Manual nudging (`<` / `>`) in `_rescue_hunk_interactive`, `_interactive_headless_shift`, and `_render_headless_interactive_frame` calculates native tab levels for Godot and tabbed files.
- **Variable Annotation Bounding:** `find_block_end` skips `@export` and `@onready` variable declarations during decorator scanning, preventing properties with colons from swallowing following statements.
- **Docstring-Preserving Scanner:** The post-patch abnormality scanner converts leading whitespace into tabs for GDScript files without modifying formatting inside multiline strings.

**v3.51**
- **Universal Polyglot Grammar Verification:** Integrated `_universal_grammar_check`, providing AST-grade bracket, block, and scope validation for Python, GDScript, C++, C#, JS, TS, Rust, and Go without external compilers.
- **Syntax Doctor Error Translation:** Translates raw AST SyntaxErrors into conversational English diagnostics pointing to missing colons, unbalanced brackets, or clipped `try` blocks.
- **First-Line Indentation Recovery:** Added `_heal_mangled_first_line_indentation` to catch and align web browser copy-paste slips where the initial line drops leading whitespace.
- **Duplicate Block Cleanup:** Scans for and flags duplicate function or class declarations across target scopes, offering a single-key selector to keep the preferred version.
- **Pure-Memory In-App Modal Dialogs:** Replaced system dialog popups with GPU-rendered in-terminal text input modals for licensing and prompts.
- **UDP Telemetry Broadcaster:** Localhost UDP broadcasting on port 49152 enables non-blocking CLI log mirroring and status streaming.

**v3.50**
- **Monospace Render Metric Integrity:** Stripped synthetic bold ANSI codes from `C_MATCH` in `_render_headless_interactive_frame`, completely eliminating horizontal character expansion in preview overlays.
- **Clipboard Fracture Auto-Healer:** Added `_heal_clipboard_indentation` to `PythonSyntaxStrategy`, recovering child indentation stripped by browser clipboards.
- **Structured Aider Diff Clamping:** Removed inadvertent flag clearance in `_apply_single_hunk`; Aider hunks clamp strictly to target line offsets.
- **Sibling Branch Indentation Alignment:** `_align_headless_snippet` automatically matches indentation for snippets starting with `elif`, `else`, `except`, `finally`, and `case` against existing file branches.
- **Orphan Block Swallowing:** `_find_headless_accordion_candidates` extends replacement boundaries downward to swallow orphaned sibling control blocks and avoid AST indentation mismatches.
- **Granular Decimal Percentages:** Percentage outputs display exact `.1f` float precision (e.g. `99.6%`), preventing misleading 100% rounding.
- **Stitch Viewer (v2.92):** Added universal line-wide `Shift+Tab` unindenting and persistent multiline docstring syntax highlighting in solid bright gold/yellow (`C_DOC`).

**v3.49**
- **Raw Overwrite Shield:** Full file replacements and explicit tactical overwrites bypass snippet repair, indentation healers, and post-patch sanitizers for 1:1 disk writes.
- **Context-Aware File Hint Isolation:** Filenames occurring in prose or string literals are ignored; hints must appear on line-zero comment headers or explicit directives.
- **Nesting-Preserving GDScript Accessor Healing:** Overhauled property accessor healing to leave clean code untouched and preserve relative `if`/`for`/`match` nesting when adjusting accessors.
- **Large Data Structure Anchoring:** Dictionaries and lookup maps spanning 6+ lines inside methods match declarations in place instead of appending duplicate blocks to file ends.
- **Aider Indentation Auto-Alignment:** Structured diff hunks detect scope indentation discrepancies and offer automated multi-space realignment before commit.

**v3.48**
- **Lexical Seam Auto-Snapping:** Adjuster seam modification bounds snap cleanly to natural statement boundaries and enclosed blocks.
- **Unreal Slate DSL Support:** Grammar step-overs for Slate UI trees (`SNew`, slot operators) and C++20 `requires` clauses prevent false indentation collapse.
- **Topological Multi-File Coalescing:** Multi-file response streams are resolved and applied in dependency order.
- **Binary IPC Framing:** `stitch_cli.py` uses optimized binary serialization, significantly reducing IPC latency on multi-megabyte streams.
- **Stitch Viewer Viewport Sync:** Proportional scrolling for uneven diff files and hunk-jumping hotkeys (`J` / `K`).

**v3.45 - v3.47**
- **Tiered Target Disambiguation:** In-code hints are strictly cross-referenced against the memory index and symbol ground-truth.
- **Godot Property Healing:** Auto-detects and rigidly aligns setter/getter accessors on `@export` and `@onready` blocks.
- **Granular Rollback Logs:** `Ctrl+Z` and `Ctrl+Y` report the specific functions, methods, and classes reverted.
- **Top-of-File Import Hoisting:** Bypasses parenthetical import blocks; missing imports prepend safely below shebangs and docstrings.
- **Ephemeral Bookmarks:** Removed persistent `bookmarks.json` disk caching; bookmarks are maintained strictly in memory and flush automatically when changing files.

**v3.44**
- Direct-to-adjuster routing for ambiguous snippets.
- Patch / Diff expansion toggle (`u`) for large previews.
- Post-patch scanner drops duplicate LLM comments.

**v3.43**
- Seam hazard detection on headless placement: sibling widget leaks, unclosed multiline expressions, indent cliffs.
- `except`, `catch`, and `finally` added to universal grammar parent classification.

**v3.41 - v3.42**
- Double brackets ending in reserved-word hints no longer misclassify during AST extraction.
- Tactical Arm override flags cleared reliably upon disarming.

**v3.39 - v3.40**
- Protocol prefixes (`res://`, `user://`) stripped safely in header analyzers.
- Headless alignment 12-space drift removed.

**v3.37 - v3.38**
- `stitch_cli.py`: stdin piping, file attach, UDP stream telemetry.
- Non-interactive CLI guards against ambiguous prompt stalls.

**v3.35 - v3.36:** Engine syntax defenses: Godot `@onready` / `@export`, Unreal `UCLASS` / `UPROPERTY` / `UFUNCTION`, Unity serialized attributes.

**v3.34:** Structural step-over for `class_name`, `extends`, `@tool`, `#pragma once`.

**v3.31:** Multi-directory monitoring on free tiers. Tactical short-block accordion stitching.

**v3.29:** Core moved to `pygame-ce`. Headless snippet handling rewritten.

**v3.26:** Snippet selection UI and diff viewer performance.

**v3.21:** GDScript multi-file markdown replacements for small scripts.

**v3.19:** Triple-quote tolerance and nested block parsing.

</details>
