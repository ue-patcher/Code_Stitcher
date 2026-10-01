<div align="center">

# AI CODE STITCHER

**The automated, AST-aware bridge between Large Language Models and local codebases.**

[![Release](https://img.shields.io/badge/release-v3.38-007ACC.svg?style=flat-square)](https://aicodestitcher.com)

[![Engine Support](https://img.shields.io/badge/engines-Unreal%20%7C%20Unity%20%7C%20Godot-orange.svg?style=flat-square)](https://aicodestitcher.com)[![CLI Support](https://img.shields.io/badge/cli-Python%203%20(Cross--Platform)-4B8BBE.svg?style=flat-square)](https://aicodestitcher.com)[![Desktop](https://img.shields.io/badge/platform-Windows%20x64%20%7C%20SDL2-555555.svg?style=flat-square)](https://aicodestitcher.com)


<p align="center">
  <a href="#why-use-it">Why Use It</a> •
  <a href="#whats-new">What's New in v3.38</a> •
  <a href="#cli-bridge">CLI Bridge</a> •
  <a href="#how-it-works">How It Works</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#keybindings">Keybindings</a> •
  <a href="#changelog">Changelog</a>
</p>

---
[Watch a demo of AI CODESTITCHER in actual use using GODOT on YouTube](https://www.youtube.com/watch?v=YOUR_VIDEO_ID)
</div>


<a id="why-use-it"></a>
## Why Use It

Using LLMs to write software usually comes with tedious busywork:
1. You prompt an LLM for changes and receive code wrapped in conversational pleasantries, markdown blocks, and truncated shortcuts (`// ... rest of your code goes here ...`).
2. You have to hunt down the matching file on disk, navigate to the correct scope, paste the snippet, fix indentations, balance brackets, and resolve broken imports manually.

**AI Code Stitcher completely eliminates this friction.** 

Leave it running in the background. Hit copy on any LLM response, or pipe terminal output directly into the new `stitch` CLI. Stitcher analyzes the AST structure, matches your file’s indentation style, resolves fuzzy anchors, safely unrolls truncation, and commits changes cleanly to disk. Every write creates an automatic local rollback snapshot (`Ctrl + Z`), with visual side-by-side diff inspection always one keystroke away (`F10`).


---
<a id="whats-new"></a>
## What's New in v3.38?

### Universal Disarm & State Leak Prevention
* **True `F9` Panic Button:** Pressing `F9` while Armed (in either Normal or Tactical mode) now universally disarms the engine. Previously, pressing `F9` while in Tactical mode would fail to disarm and instead silently convert the session to Normal mode, leaking override flags (like `_force_full_file`) and causing safety prompts to be dangerously bypassed.
* **Safe Prompt Defaults:** Full-file replacement confirmation prompts now safely default to `[N]` (No) to prevent accidental code overwrites from stray `Enter` key presses.
* **Strict Flag Consumption:** Tactical override flags are now aggressively consumed and wiped upon use, permanently preventing them from leaking into subsequent patch operations.

### Continuous Syntax & Bracket Parsing
* **Multi-line String Parity Fix:** Completely rewrote the string masker inside the Universal Grammar Checker. It now uses a continuous character scanner instead of resetting line-by-line. This fixes spurious syntax errors where brackets (`{}`, `[]`, `()`) inside multi-line strings, JS/TS template literals (`` ` ``), or line continuations (`\`) would falsely trigger and corrupt the bracket parity stack.


---
<a id="cli-bridge"></a>
## Terminal Bridge (`stitch` CLI)

The CLI companion script (`stitch_cli.py`) communicates directly with the running Code Stitcher desktop runtime over non-blocking localhost IPC.

```bash
Usage:
  stitch [FILES/FOLDERS...]       Attach project files into the Compose Window (F7)
  <command> | stitch             Pipe patches, diffs, or LLM code directly to disk
  stitch --stream                Live-stream engine activity and AST diagnostics
  stitch --help, -h              Display the built-in guide
```

### Common Workflows

#### 1. Attach context files to your LLM Composer
Send files or folders straight from your terminal into the desktop prompt composer:
```bash
stitch src/player.gd src/combat/hitbox.gd
```

#### 2. Pipe local LLM output directly to disk
Pipe raw streaming output from local models directly to your codebase:
```bash
ollama run codellama "Add input validation to update_user in user_service.py" | stitch
```

#### 3. Pipe Git patches directly into the engine
Apply unstaged changes or branch diffs through Stitcher's fuzzy AST healing pipeline:
```bash
git diff main | stitch
```

#### 4. Monitor live engine operations
Watch engine writes, AST sanity checks, and confidence ratings in real-time:
```bash
stitch --stream
```


---
<a id="how-it-works"></a>
## How It Works

```text
  [ Chat LLM / CLI / Git ]
             │
      (Copy or Pipe)
             ▼
  ┌────────────────────────────────────────────────────────┐
  │                   AI CODE STITCHER                     │
  │  • Strips conversational wrapper noise                 │
  │  • Identifies target file from memory index            │
  │  • Normalizes tabs, spaces, and CRLF parity            │
  │  • Accordion-stitches lazy truncations (...)           │
  │  • Runs pre-commit AST verification                    │
  └────────────────────────────────────────────────────────┘
             │
    (Automatic Backup)
             ▼
  [ Disk Write & Local Snapshot (.bak) ]
```

1. **Arm the Engine:** Press `F9` (or pipe via `stitch`).
2. **Capture Any Output:** Copy code from your browser/IDE, or pipe stdout directly from terminal utilities.
3. **AST Detection & Placement:** The engine scans code structure (Aider patch, unified diff, drop-in method, or headless snippet) to determine the exact file and line offset.
4. **Auto-Clean & Apply:** Placeholders are reconciled, indentation is adapted, and changes are safely written to disk with an automatic rollback snapshot.


---
<a id="architecture"></a>
## Architecture

The ecosystem consists of three unified components:

### 1. Code Stitcher (Engine Orchestrator)
Lightweight runtime managing memory monitoring, syntax trees, and file modifications.
* **Clipboard & IPC Watcher:** Real-time scanner monitoring memory and localhost sockets for incoming blocks.
* **Indent Normalizer:** Harmonizes indentation (e.g., converting 8-space LLM drift to clean 4-space targets).
* **Accordion Stitcher:** Automatically expands lazy ellipsis comments (`// ... existing code ...`) by anchoring against existing disk logic.
* **AST Validator:** Runs syntax checks prior to committing changes to protect projects from syntax errors.
* **Snapshot Engine:** Creates instant `.bak` snapshots in hidden `.ep_backups/` directories.

### 2. Stitch Viewer (GUI Inspector)
Hardware-accelerated SDL2 diff interface providing visual reviews independent of Git.
* **Side-by-Side Diff View:** Real-time visual comparison between original snapshots and patched results.
* **Granular Reverts:** Visual controls to discard individual lines, blocks, or hunks.
* **Integrated Inline Editor:** Press `Esc` while viewing a file to adjust lines directly.
* **Session Timeline:** Complete visual history of all file modifications in your session.

### 3. Stitch CLI (`stitch_cli.py`)
Cross-platform command-line tool bridging local shell workflows, Git pipelines, and local AI runtimes directly into the Stitcher engine.


---
<a id="keybindings"></a>
## Keybindings

| Key | Action | Description |
| :--- | :--- | :--- |
| `F9` | **Arm / Disarm** | Toggle the background clipboard listener on or off. |
| `Shift + F9` | **Tactical Arm** | Intercept copied code and prompt for explicit destination confirmation. |
| `F8` | **Filelock** | Pin AST targeting strictly to a designated file. |
| `F7` | **Compose** | Open the prompt composer with automated context attachments. |
| `F10` | **Launch Viewer** | Open the hardware-accelerated visual diff viewer. |
| `Ctrl + Z` | **Rollback** | Instantly revert the most recent file injection using local snapshots. |
| `Ctrl + Y` | **Redo** | Re-apply a previously reverted file injection. |


---
<a id="changelog"></a>
## Version History

<details open>
<summary><b>Changelog (v3.17 – v3.38)</b></summary>

* **v3.38:**
  * Fixed Tactical Arm state leak where pressing `F9` failed to disarm and instead leaked override flags into Normal mode.
  * Rewrote AST string/comment masker to use continuous character scanning, fixing false-positive bracket parity errors on multi-line strings and template literals.
  * Full-file replacement confirmation prompts now safely default to `[N]`.
* **v3.37:**
  * Fixed Godot `res://` and `user://` URI prefixes polluting class extraction and producing spurious scope hints.
  * Added protocol stripping and expanded reserved keyword filters in comment and header scope analyzers.
  * Corrected indentation calculations in headless snippet alignment to prevent 12-space indent drift.
  * Restored full multi-candidate interactive review loop (`#1`, `#2`, `#3`) when snippet match confidence requires user confirmation.
* **v3.36:**
  * Added cross-platform `stitch_cli.py` companion tool with piping support (`stdin`), file attachments, and live UDP stream telemetry.
  * Enabled recursive folder monitoring across all directories for the free Personal Edition.
* **v3.35:**
  * Hardened non-interactive CLI safeguards against ambiguous prompt stalls.
* **v3.34:**
  * Game Engine syntax defenses (Godot `@onready`/`@export` multi-line parsing, Unreal `UCLASS`/`UPROPERTY`/`UFUNCTION` macros, Unity serialized attributes).
  * `func` signature protection against deep dedentation collapse.
* **v3.33:**
  * Reduced idle CPU load by yielding UI loops to OS threads.
  * Structural protection stepping over engine headers (`class_name`, `extends`, `@tool`, `#pragma once`).
* **v3.30:** Multi-directory monitoring for free tiers; tactical short-block accordion stitching.
* **v3.28:** Core migration to `pygame-ce`; rewritten headless snippet handling.
* **v3.25:** Snippet selection UI improvements and diff viewer performance tuning.
* **v3.20:** Added GDScript multi-file markdown replacements for small script files.
* **v3.17:** Triple-quote string tolerance updates and nested block parsing refinements.

</details>
```
