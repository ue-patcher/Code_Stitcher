# 🧵 AI Code Stitcher & Stitch Viewer

[![GitHub stars](https://img.shields.io/github/stars/ue-patcher/Code_Stitcher?style=flat-square&logo=github)](https://github.com/ue-patcher/Code_Stitcher)
[![GitHub release](https://img.shields.io/github/v/release/ue-patcher/Code_Stitcher?style=flat-square)](https://github.com/ue-patcher/Code_Stitcher/releases)
[![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](LICENSE)
[![Made with Python](https://img.shields.io/badge/made%20with-python-blue?style=flat-square&logo=python)](https://www.python.org/)

> **The ultimate bridge between AI code generation and your local codebase.** Paste AI-generated code from Claude, ChatGPT, DeepSeek, Cursor, Aider, or any LLM—AI Code Stitcher intelligently applies it to the correct locations in your project. It just works.

---

## 🚀 Quick Start

**[Download Latest Release](https://github.com/ue-patcher/Code_Stitcher/releases)** → Run installer → Start stitching

```bash
# Windows
code_stitcher_setup_v2.71.exe

# macOS / Linux
python -m code_stitcher
```

---

## Why AI Code Stitcher?

When working with AI code generation tools, the workflow is tedious:
- ❌ Copy output from Claude/ChatGPT
- ❌ Hunt for the right insertion point in your codebase
- ❌ Manually fix indentation
- ❌ Deal with LLM hallucinations (`// ... existing code ...`)
- ❌ Track changes across your project

**AI Code Stitcher automates all of this.** Keep coding while the tool handles integration.

---

## ✨ Key Features

### 🎯 Format Agnostic
- **Unified Diffs** – Apply patches from standard diff formats
- **Aider Patches** – Direct integration with Aider-generated code
- **Drop-in Replacements** – Paste complete updated functions
- **Headless Snippets** – Just the code, no formatting needed
- **LLM-Friendly** – Works with output from Claude, ChatGPT, DeepSeek, Cursor, Code, and more

### 🔧 Auto-Healing
- Fixes mangled brackets caused by LLM formatting errors
- Auto-resolves missing imports and dependencies
- Corrects broken indentation automatically
- Removes common LLM hallucinations (`// ... existing code ...`)

### ⚡ Instant Rollbacks
- Press **`Ctrl+Z`** to undo the last patch
- Press **`Ctrl+Y`** to redo
- Full `.bak` backup system maintained internally
- Never lose code—always have a safe fallback

### 👀 Visual Review & Editing
- **Side-by-side diff viewer** to inspect every change
- **Granular revert controls** – Accept or reject individual changes
- **Live text editor** – Fix typos and adjust code on the fly
- **Change history tree** – See every AI injection applied during your session
- **Context view** – Collapse to see only modified functions

---

## 📋 Components

### 1. Code Stitcher (Terminal Orchestrator)
*The intelligent background engine.*

Runs as an interactive terminal application that monitors your clipboard and applies AI-generated code to your codebase.

#### How it Works
1. **Clipboard Monitoring** – When "Armed" (F9), actively watches for code blocks
2. **Intelligent Parsing** – Strips conversational text and isolates actual code
3. **Context Resolution** – Identifies whether it's a diff, patch, class, or new function
4. **Auto-Stitching** – Finds insertion points, aligns indentation, writes safely
5. **Smart Cleanup** – Removes LLM hallucinations and formatting artifacts

#### Essential Hotkeys
| Hotkey | Action | Description |
|--------|--------|-------------|
| **F9** | Arm / Disarm | Toggle clipboard monitoring on/off |
| **Shift + F9** | Tactical Arm | Intercept clipboard, manually choose injection point |
| **F8** | Filelock | Lock output to specific file (disable guessing) |
| **F7** | Compose | Draft prompts with attached file context |
| **F11** | Launch Viewer | Open Stitch Viewer for review & editing |
| **Ctrl+Z** | Undo | Revert last patch |
| **Ctrl+Y** | Redo | Reapply last patch |

---

### 2. Stitch Viewer (Pygame GUI)
*The visual interface for review, revert, and refinement.*

A blazing-fast, Git-like UI for reviewing exactly what the Stitcher applied to your files.

#### How it Works
Launched via **F11** from the Stitcher, it reads the hidden `ep_backups` folder and displays your codebase's history in a clean side-by-side diff layout.

#### Key Features
- **Side-by-Side Diff** – Compare historical (Old) and live (New) versions
  - Deletions highlighted in **red**
  - Additions highlighted in **green**
- **Granular Revert Controls** – Click arrows (`→`) or crosses (`×`) to accept/reject individual changes
- **Live Text Editor** – Click "Edit Current File" to transition into full editor mode
  - Fix typos, adjust variables
  - Press **ESC** to save
- **RegEdit-style History Tree** – Chronological file organization
  - Expand any file to see every AI injection ("Run") applied during your session
- **Context View** – Collapse entire file to see only changed functions in summary cards

#### Screenshot
![AI Code Stitcher - Stitch Viewer](https://github.com/user-attachments/assets/253658c6-023f-422c-81b5-769e0eef2459)

---

## 🎬 Workflow Example

1. You're coding in your IDE and want AI assistance
2. Open Claude, ChatGPT, DeepSeek, or Cursor in another window
3. Ask for code changes (e.g., "Refactor my auth module")
4. AI returns the updated code
5. **Copy the AI output**
6. **Press F9** in Code Stitcher (Arm)
7. **Paste** (Ctrl+V) – AI Code Stitcher detects and processes it
8. Code is automatically injected into the correct file with perfect indentation
9. **Press F11** to review changes in Stitch Viewer
10. Accept changes with a click or revert problematic edits
11. **Press Ctrl+Z** if needed to rollback

---

## 🛠️ Supported AI Tools & LLMs

Works seamlessly with output from:
- **ChatGPT** (OpenAI)
- **Claude** (Anthropic)
- **DeepSeek**
- **Cursor**
- **GitHub Copilot**
- **Aider**
- **Code Llama**
- Any LLM that outputs code

---

## 📥 Installation

### Windows
1. Download the latest `.exe` from [Releases](https://github.com/ue-patcher/Code_Stitcher/releases)
2. Run the installer
3. Accept security warnings (see note below)
4. Launch from Start menu or create desktop shortcut

### macOS / Linux
```bash
git clone https://github.com/ue-patcher/Code_Stitcher.git
cd Code_Stitcher
pip install -r requirements.txt
python code_stitcher.py
```

### ⚠️ Windows Defender SmartScreen Warning
You may see a "potentially dangerous" warning. This is **normal** for new software with limited install base. We assure you:
- ✅ No spyware
- ✅ No malware
- ✅ Open source for inspection
- ✅ No telemetry collection

---

## 🎓 Getting Started

### First Time Setup
1. Launch **AI Code Stitcher**
2. Configure folders to monitor (your project directories)
3. The tool builds a lightweight index of your codebase
4. Press **F9** to arm clipboard monitoring
5. Start copying AI-generated code—the rest is automatic

### Tips for Best Results
- **Keep code blocks simple** – Large monolithic changes work better than tiny snippets
- **Use Filelock (F8)** if the tool guesses wrong insertion points
- **Review in Stitch Viewer (F11)** before committing changes to version control
- **Use Tactical Arm (Shift+F9)** for complex injections where you want control

---

## 🔄 Version Control Integration

AI Code Stitcher maintains its own `.bak` backup system independent of Git. You can:
- Use **F11** Stitch Viewer to review changes before committing
- Revert individual edits with granular controls
- Commit clean, reviewed changes to version control

---

## 🐛 Troubleshooting

### Tool doesn't detect my code
- Ensure **F9** is enabled (terminal shows "ARMED")
- Check clipboard actually contains code (not just text)
- Use **F8 Filelock** to manually specify target file

### Indentation looks wrong
- AI Code Stitcher auto-fixes most indentation—review in **F11 Stitch Viewer**
- Use the live editor to manually adjust if needed
- Press **Ctrl+Z** to undo and retry

### Code applied to wrong location
- Press **Ctrl+Z** to undo
- Use **Shift+F9 Tactical Arm** next time to manually choose insertion point
- Or use **F8 Filelock** to lock to a specific file

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Report Issues
Found a bug? Have a feature idea? Open an [Issue](https://github.com/ue-patcher/Code_Stitcher/issues) with:
- What you were trying to do
- What happened instead
- Your OS and Python version
- The code snippet that caused the issue (if applicable)

### Feature Requests
Have an idea? [Start a Discussion](https://github.com/ue-patcher/Code_Stitcher/discussions) first to see if others want it too!

---

## 💬 Community & Support

- **Discussions** – Ask questions and share ideas: [Discussions](https://github.com/ue-patcher/Code_Stitcher/discussions)
- **Issues** – Report bugs: [Issues](https://github.com/ue-patcher/Code_Stitcher/issues)
- **Website** – Learn more: [aicodestitcher.com](https://aicodestitcher.com)

---

## 📄 License

AI Code Stitcher is released under the [MIT License](LICENSE). See LICENSE file for details.

By downloading and installing this tool, you agree to the standard software terms and conditions.

---

## 🌟 Show Your Support

If you find AI Code Stitcher helpful:
- ⭐ **Star this repository** on GitHub
- 🐦 **Share it** with other developers
- 💬 **Leave feedback** in [Discussions](https://github.com/ue-patcher/Code_Stitcher/discussions)
- 🐛 **Report bugs** to help us improve

---

## 🚀 What's Next?

- 🎯 **Advanced pattern matching** for complex code structures
- 🔗 **IDE integrations** (VS Code, JetBrains extensions)
- 🌐 **Web-based collaboration** for team development
- 📊 **Analytics dashboard** to track AI-assisted development metrics

[View Roadmap →](https://github.com/ue-patcher/Code_Stitcher/discussions/categories/roadmap)

---

**Made with ❤️ for developers who use AI to code faster.**
