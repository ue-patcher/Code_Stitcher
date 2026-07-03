# AI Code Stitcher & Stitch Viewer

[![GitHub stars](https://img.shields.io/github/stars/ue-patcher/Code_Stitcher?style=flat-square&logo=github)](https://github.com/ue-patcher/Code_Stitcher)
[![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](LICENSE)

**The ultimate bridge between AI code generation and your local codebase.** Paste AI-generated code from Claude, ChatGPT, DeepSeek, Cursor, Aider, or any LLM—AI Code Stitcher intelligently applies it to the correct locations in your existing codebase.

---

## Download Now

### Windows (Latest Release v2.71)

[Download Installer](https://github.com/ue-patcher/Code_Stitcher/releases/download/v2.71/code_stitcher_setup_v2.71.exe)

Simply run the installer and start stitching.

---

## The Problem

When working with AI code generation tools, the workflow is tedious:

- Copy output from Claude/ChatGPT
- Hunt for where it belongs in your codebase
- Manually fix indentation
- Deal with LLM hallucinations (`// ... existing code ...`)
- Track changes across your project

**AI Code Stitcher automates all of this.** Keep coding while the tool handles integration.

---

## How It Works

AI Code Stitcher has two components:

1. **Code Stitcher** - A terminal application that monitors your clipboard and intelligently applies AI code to your project
2. **Stitch Viewer** - A visual diff viewer for reviewing, accepting, or reverting changes

### The Workflow

1. Ask Claude, ChatGPT, or another LLM for code
2. Copy the AI output
3. Press **F9** in Code Stitcher to arm it
4. Paste the code with Ctrl+V
5. The tool automatically finds where it belongs, fixes indentation, and applies it
6. Press **F11** to review changes in Stitch Viewer
7. Accept or reject individual edits with a click

---

## Features

### Format Agnostic
- Unified Diffs
- Aider Patches
- Drop-in replacements
- Headless snippets
- Works with Claude, ChatGPT, DeepSeek, Cursor, GitHub Copilot, Aider, Code Llama, and any LLM

### Auto-Healing
- Fixes mangled brackets caused by LLM formatting errors
- Auto-resolves missing imports and dependencies
- Corrects broken indentation automatically
- Removes common LLM hallucinations

### Instant Rollbacks
- Press Ctrl+Z to undo the last patch
- Press Ctrl+Y to redo
- Full .bak backup system maintained internally

### Visual Review & Editing
- Side-by-side diff viewer to inspect every change
- Granular revert controls - Accept or reject individual changes
- Live text editor - Fix typos and adjust code on the fly
- Change history tree - See every AI injection applied during your session
- Context view - Collapse to see only modified functions

---

## Code Stitcher: Terminal Application

Runs as an interactive terminal application. You configure which folders to monitor, and it builds a lightweight index of your codebase.

### How It Works

1. **Clipboard Monitoring** - When "Armed" (F9), actively watches for code blocks
2. **Intelligent Parsing** - Strips conversational text and isolates actual code
3. **Context Resolution** - Identifies whether it's a diff, patch, class, or new function
4. **Auto-Stitching** - Finds insertion points, aligns indentation, writes safely
5. **Smart Cleanup** - Removes LLM hallucinations and formatting artifacts

### Essential Hotkeys

| Hotkey | Action | Description |
|--------|--------|-------------|
| F9 | Arm / Disarm | Toggle clipboard monitoring on/off |
| Shift + F9 | Tactical Arm | Intercept clipboard, manually choose injection point |
| F8 | Filelock | Lock output to specific file (disable guessing) |
| F7 | Compose | Draft prompts with attached file context |
| F11 | Launch Viewer | Open Stitch Viewer for review & editing |
| Ctrl+Z | Undo | Revert last patch |
| Ctrl+Y | Redo | Reapply last patch |

---

## Stitch Viewer: Visual Interface

A blazing-fast, Git-like UI for reviewing exactly what the Stitcher applied to your files.

### How It Works

Launched via F11 from the Stitcher, it reads the hidden `ep_backups` folder and displays your codebase's history in a clean side-by-side diff layout.

### Features

- **Side-by-Side Diff** - Compare historical (Old) and live (New) versions. Deletions in red, additions in green.
- **Granular Revert Controls** - Click arrows or crosses to accept/reject individual changes
- **Live Text Editor** - Transition the right-hand panel into a full editor. Fix typos, adjust variables, press ESC to save.
- **History Tree** - Chronological file organization. Expand any file to see every AI injection ("Run") applied during your session.
- **Context View** - Collapse entire file to see only changed functions in summary cards

---

## Installation

### Windows

1. Download the installer from the release link above
2. Run code_stitcher_setup_v2.71.exe
3. Windows Defender SmartScreen may appear (normal for new apps) - click "More info" then "Run anyway"
4. Follow the installation wizard
5. Launch from Start menu

### macOS / Linux

Support is planned. Check back for updates or [join our discussions](https://github.com/ue-patcher/Code_Stitcher/discussions).

### Windows Defender SmartScreen Warning

You may see a warning that the app is "potentially dangerous." This is normal for new software with a limited install base. AI Code Stitcher contains:

- No spyware
- No malware
- Open source for inspection
- No telemetry collection

---

## Getting Started

1. Launch AI Code Stitcher
2. Configure folders to monitor (your project directories)
3. The tool builds a lightweight index of your codebase
4. Press F9 to arm clipboard monitoring
5. Start copying AI-generated code

### Tips

- Keep code blocks reasonably sized - large monolithic changes work better than tiny snippets
- Use Filelock (F8) if the tool guesses wrong insertion points
- Review in Stitch Viewer (F11) before committing changes to version control
- Use Tactical Arm (Shift+F9) for complex injections where you want more control

---

## Troubleshooting

### Tool doesn't detect my code

- Ensure F9 is enabled (terminal shows "ARMED")
- Check your clipboard actually contains code, not just text
- Use F8 Filelock to manually specify target file

### Indentation looks wrong

- AI Code Stitcher auto-fixes most indentation - review in F11 Stitch Viewer
- Use the live editor to manually adjust if needed
- Press Ctrl+Z to undo and retry

### Code applied to wrong location

- Press Ctrl+Z to undo
- Use Shift+F9 Tactical Arm next time to manually choose insertion point
- Or use F8 Filelock to lock to a specific file

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Report Issues

Found a bug? Have a feature idea? Open an [Issue](https://github.com/ue-patcher/Code_Stitcher/issues) with:

- What you were trying to do
- What happened instead
- Your OS and Python version
- The code snippet that caused the issue (if applicable)

### Feature Requests

Have an idea? [Start a Discussion](https://github.com/ue-patcher/Code_Stitcher/discussions) to see if others want it too.

---

## Community & Support

- **Discussions** - Ask questions and share ideas: [GitHub Discussions](https://github.com/ue-patcher/Code_Stitcher/discussions)
- **Issues** - Report bugs: [GitHub Issues](https://github.com/ue-patcher/Code_Stitcher/issues)
- **Website** - Learn more: [aicodestitcher.com](https://aicodestitcher.com)

---

## License

AI Code Stitcher is released under the [MIT License](LICENSE).

By downloading and installing this tool, you agree to the standard software terms and conditions.

---

## Roadmap

- IDE integrations (VS Code, JetBrains extensions)
- macOS and Linux support
- Web-based collaboration features
- Advanced pattern matching for complex code structures
- Analytics dashboard for AI-assisted development metrics

[View Full Roadmap](ROADMAP.md)

---

## What's Coming

We're working on expanding platform support and IDE integrations. [Check out our discussions](https://github.com/ue-patcher/Code_Stitcher/discussions/categories/roadmap) to vote on features or share your ideas.
