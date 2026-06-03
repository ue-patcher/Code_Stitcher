
### Technical Manual & Operational Guide

---

## 1. Core Functional Features

The Ultimate Elastic Patcher operates as an event-driven system console that interacts with your file system and clipboard. 

### 📋 Clipboard Monitoring
* **Trigger:** `F9` (Arm/Disarm)
* **Behavior:** When armed, the system polls the clipboard. If valid patch patterns (such as Aider search/replace blocks, unified diffs, or code snippets) are detected, they are processed. Non-code text or trivial commands are ignored.

### 🎯 Tactical Alignment Mode
* **Trigger:** `Shift + F9` (Tactical Arm)
* **Behavior:** Bypasses automatic placement decisions. For every clipboard transaction, it presents an interactive layout allowing you to manually route the patch, select targets, and shift code positions line-by-line.

### 🔒 State-Lock (Filelock)
* **Trigger:** `F8`
* **Behavior:** Locks the patcher to a single target file, skipping codebase-wide search routines. Useful when working with multiple files sharing similar method names.

### 📝 Integrated LLM Compose Workspace
* **Trigger:** `F7`
* **Behavior:** A built-in modal text editor replacing external dialog boxes to compose and format LLM requests.
  * **Add File/Dir:** Select and attach files/directories directly to the prompt.
  * **Log Toggle:** Attach console logs of failed patch runs to request corrections from the LLM.
  * **Custom Instructions:** Edit the custom instruction template appended to clipboard payloads.
  * **Restore:** Recalls the previous session's text and files in the event of an accidental close.

### 🗃️ Auditing & History Logging
* **Behavior:** When `CONF_AUDIT_LOG = True` is set, all write operations are recorded:
  * **Flat File Audit Log (`ep_patch.log`):** Timestamps, target paths, actions, and unified diff previews.
  * **JSON Transaction History (`ep_history.json`):** Tracks exact pre- and post-patch states and backup references.

### 🔄 Session-Wide Undo & Redo
* **Trigger:** `Ctrl + Z` / `Ctrl + Y`
* **Behavior:** Non-destructive state engine. Undoing a patch restores the file to its pre-patch state and pushes the change to a forward-history (Redo) stack. Redoing retrieves files from the `.redo/` directory.

### 🔍 Live Diff Viewer Integration
* **Trigger:** `F11`
* **Behavior:** Connects with the companion utility `ep_diff_viewer.exe` to display live side-by-side visual diffs, tracking files before and after modifications.

---

## 2. Technical Mechanics (How It Works)

### 2.1. Normalization & Sanity Scrubbing

```
[Raw Clipboard] ➔ [Purge Unicode Garbage] ➔ [Strip Citations & Line Numbers] ➔ [Heal Line-Wraps] ➔ [Extract Code Block]
```

<details>
<summary><b>Click to expand normalization stages</b></summary>

1. **Garbage Character Purging:** Converts non-breaking spaces (`\xa0`, `\u202f`), mathematical spaces, zero-width spaces (`\u200b`), byte order marks (`\ufeff`), and line separators (`\u2028`, `\u2029`) into standard spaces or deletes them.
2. **Citation Block Removal:** Strips web interface citation markers (e.g., `[cite: 1]`, `【4†source】`) to prevent syntax errors.
3. **Line Number Deletion:** Parses and removes copied line numbers (e.g., `12 | def my_func():` or `45: const x = 1`).
4. **Line-Wrap Healing:** Merges lines that were wrapped mid-statement by web browsers (e.g., lines ending with an open quote followed by an indented line).
5. **Text Extraction:** Separates conversational text from code blocks using markdown backticks (```) or structural syntax keywords.

</details>

---

### 2.2. Language Lexing & Syntax Profiles

The patcher uses semantic language mapping to determine how blocks of code are structured. It classifies languages into three profiles:

* **Indent-Based Profiles** *(e.g., Python, Nim, GDScript)*: Uses visual indents to find scope boundaries. It handles decorators (lines starting with `@`) and docstrings without breaking the block.
* **Brace-Based Profiles** *(e.g., JavaScript, TypeScript, C++, Java, Rust, Go)*: Uses bracket-counting to find where classes and methods end, making it less dependent on indentation.
* **Keyword-Based Profiles** *(e.g., Ruby, Lua, Shell)*: Determines scope using keywords like `end`, `then`, or `fi`.

#### The Masking Pipeline

To prevent comments or strings from interfering with scope detection (such as a `#` inside a string, or a curly brace in a JS template literal), the engine masks these regions:

```python
# Raw Python line:
print("def fake_function():")  # This is a comment containing }

# Masked view in parser memory:
print("                     ")  # 
```

* **Python Masking:** Tracks single-line quotes, multiline triple quotes (`"""` and `'''`), and line comments. All text inside strings or comments is replaced with spaces in the parser's memory to avoid incorrect matches on class or function definitions.
* **Brace-Based Masking:** Tracks block comments (`/* ... */`), inline comments (`//`), string literals, and template literals, masking them out before the bracket-matching engine evaluates scope depth.

---

### 2.3. The Fuzzy Sequence Matching Engine

When a candidate patch is parsed, the engine locates the target area in the file using a weighted similarity calculation:

#### 1. Line Weight Calculation
Trivial lines (like `else:`, `}`, or `return`) are given low weights (1.0). Complex statements containing unique variables, assignments, or method calls are assigned higher weights:

$$\text{Weight} = 1.0 + \left( \frac{\text{Length of Normalized Line}}{30} \right)$$

This helps prevent common structural lines from causing false-positive matches.

#### 2. Fuzzy Ratio Mapping & Gap Penalties
Each line in the file is compared against the normalized candidate line. If the engine has to skip lines in the target file to find a match, it applies a gap penalty:

$$\text{Adjusted Confidence} = \text{Base Match Score} - (\text{Skipped Lines} \times 0.15)$$

This penalty ensures that if a search block is matched across a widely dispersed set of lines, it is rejected unless an explicit truncation marker (ellipsis) is present.

#### 3. Multi-Match Resolution
If multiple locations return identical high confidence scores:
* For **Structured Diffs** (Unified or Aider patches), it clamps the match to the location closest to the expected line number to avoid duplicate modifications.
* For **Drop-In Patches**, it applies the modification to all identical locations in reverse order (bottom-to-top) so that file line offsets stay correct.

---

### 2.4. Accordion Stitching (Handling Truncation)

If a patch contains placeholders like `// ... rest of code` or `# existing logic`, the Accordion Stitcher is activated to merge the new code with the old.

```
          TARGET FILE BLOCK                  TRUNCATED LLM PATCH
       +--------------------+               +--------------------+
       |  def process():    |               |  def process():    |
       |      init_env()    |               |      # ...         |
       |      read_data()   | =======>      |      update_val()  |
       |      write_data()  |  (Stitcher)   |      # ...         |
       |      clean_up()    |               +--------------------+
       +--------------------+
```

1. **Hole Detection:** Scans for lines matching common truncation indicators (e.g., `...`, `ellipsis`, `existing logic`, `omitted`).
2. **Dominant Indentation Delta:** Calculates the difference in indentation between the matching lines in the target file and the patch, using the most common difference to align the rest of the patch:
   $$\Delta_{\text{indent}} = \text{Indent}_{\text{patch}} - \text{Indent}_{\text{file}}$$
3. **Anchor Mapping:** Matches the code before (Head Anchor) and after (Tail Anchor) the truncation marker to the target file's code.
4. **Content Restoration:** Replaces the truncation markers by pulling the original lines from the target file, adjusting their indentation by $\Delta_{\text{indent}}$ so they line up correctly.
5. **Inline Truncation Cleanup:** Parses, strips comment markers, and normalizes truncation markers written inline at the end of a line (such as `import os # ...`) to ensure clean syntax.

---

### 2.5. Safety, Formatting & Code Hygiene Pipelines

```
[Raw Patch] ➔ [Bracket Parity Check] ➔ [Tab/NBSP Scrub] ➔ [Dupe Resolution] ➔ [Import Hoisting] ➔ [Disk Write]
```

* **Bracket Parity Verification:** Counts braces, brackets, and parentheses in the modified buffer, logging a console warning if a mismatch is found to help prevent compilation errors.
* **Duplicate Function Resolution:** If a patch introduces a function that already exists in the same scope, the patcher identifies both versions, presents a side-by-side comparison in the console, and prompts you to select which version to keep.
* **Import Hoisting:** Hoists imports written inline inside the new method bodies to the top of the file, keeping your import statements organized.
* **Vertical Spacing & Tab Normalization:**
  * Converts hard tabs to 4 spaces (configurable).
  * Scrubs stray non-breaking spaces.
  * Compresses excessive blank lines (more than two consecutive empty lines).
  * Ensures a single blank line separates top-level classes and methods.

---

## 3. User Workflows & Operational Guides

### 3.1. Standard Mode Workflow (Copy-and-Apply)

The standard workflow is designed for quick, hands-off patching:

1. **Launch the Patcher:** Open `elastic_patcher.exe`. Ensure the console loads your project paths under "Monitoring folder(s)".
2. **Arm the System:** Press `F9`. The status line will change to `ARMED - Now Monitoring Clipboard`.
3. **Generate the Patch:** In your AI assistant, request a modification. Copy the resulting code block or diff output.
4. **Automatic Processing:** The patcher detects the copy event, normalizes the text, identifies the target file, applies the changes in memory, runs syntax/safety checks, and writes the update to disk.
5. **Review:** Your editor will reload the updated file. If you need to roll back the change, press `Ctrl + Z` in the patcher window.

---

### 3.2. Tactical Alignment Workflow

Use Tactical Mode when a patch lacks clear anchoring context or needs precise, manual placement:

1. **Activate Tactical Arm:** Press `Shift + F9`. The console will display `TACTICAL ARMED - Interactive Routing Enabled`.
2. **Copy the Patch:** Copy the code snippet to your clipboard.
3. **Choose the Strategy:** The patcher will display a menu of available strategies:
   * `1`: Smart Drop-In (fuzzy-matches methods).
   * `2`: Full Class Overwrite.
   * `3`: Full File Overwrite.
   * `4`: Headless Snippet (launches manual alignment).
4. **Interactive Alignment:** Selecting `4` launches the interactive split-frame view:
   * Hold `Up/Down Arrow` to shift the patch block line-by-line.
   * Use `PageUp/PageDown` to jump the block by ten lines.
   * Press `+` or `-` to expand or contract the number of lines being replaced.
   * Press `Left/Right Arrow` to cycle through alternative structural anchors.
5. **Commit:** Press `Enter` to write the changes to disk, or `Escape` to cancel.

---

### 3.3. Structural Collision & Duplicate Resolution

When a patch introduces a method name that already exists in multiple classes or files, the patcher walks you through a resolution process:

1. **Collision Warning:** The console alerts you: `DUPLICATE TARGETS - <method_name>`.
2. **Target List:** The console lists all files and classes where the method was found, along with a similarity score:
   ```
    1. views.py   -> SCOPE: UserProfileView (45% similarity | +12 lines)
    2. views.py   -> SCOPE: AdminDashboardView (12% similarity | -4 lines)
    n. New File
    m. Manual Filename Entry
    s. Skip Candidate
   ```
3. **Selection:**
   * Enter the number of the correct target scope to apply the patch.
   * Press `s` to skip, or `0` to cancel the entire operation.
4. **Placement of New Functions:** If you select a file where the method does not yet exist, you will be prompted on where to insert it:
   * `t`: Insert at the top of the file/class scope.
   * `b`: Append to the bottom of the file/class scope.
   * `p`: Insert directly after a neighboring method from the patch.

---

### 3.4. Session Versioning: Undo, Redo, and Walkbacks

The patcher keeps a local history of changes so you can roll back unwanted edits or recover previous file states:

| Action | Shortcut | Description |
| :--- | :--- | :--- |
| **Undo Patch** | `Ctrl + Z` | Restores files modified in the last batch to their pre-patch state and moves the patch to the Redo buffer. |
| **Redo Patch** | `Ctrl + Y` | Re-applies the reverted changes from the Redo buffer. |
| **Manual Walkback** | `F8` / `History` | Select from a list of monitored files and restore them to a specific historical checkpoint. |

---

### 3.5. Custom Instructions & Prompting Templates

To get the cleanest, most patch-compatible code from your AI assistant, you can customize the instructions appended to your clipboard requests:

1. Press `F7` to open the LLM Compose modal, and select `Instruct` (or press `Shift + F11` from the main console) to edit the instruction template.
2. Add specific guidelines for formatting code output, such as:
   ```markdown
   - Provide complete, untruncated functions.
   - Avoid using placeholders, inline omissions, or comments like '# rest of code'.
   - Use Aider-style search/replace blocks for targeted updates:
     <<<<<<< SEARCH
     <original_code>
     =======
     <new_code>
     >>>>>>> REPLACE
   ```
3. When you copy a request from the Compose modal, these instructions are automatically appended to your prompt, helping to ensure the assistant returns a cleanly structured, easily matchable patch.

---

## 4. Troubleshooting & System Diagnostics

* **Patcher does not intercept copied text**
  * *Cause:* Global hotkey hooks may be blocked by administrative privileges, or the console window is not armed.
  * *Resolution:* Ensure the window status is `ARMED`. Try running the patcher as an Administrator if your IDE is running with elevated privileges. Alternatively, disable `CONF_GLOBAL_HOTKEY` in `ep_settings.ini` to rely on standard clipboard polling.

* **Code blocks align to the wrong class scope**
  * *Cause:* The patcher matched a method name that exists in multiple classes within the same file.
  * *Resolution:* Use Filelock (`F8`) to isolate the target file, or add a scope comment hint directly in your patch before copying it:
    ```python
    # CLASS: UserProfileView
    def get_context_data(self):
        ...
    ```

* **Brackets or braces are mismatched after a patch**
  * *Cause:* The LLM returned a truncated block that was stitched incorrectly, or the patch had syntax errors.
  * *Resolution:* Press `Ctrl + Z` to undo the write. Review the diff using the Live Diff Viewer (`F11`). Try copying the block again, or use Tactical Mode (`Shift + F9`) to adjust the insertion boundaries manually.

* **Console displays rendering lags or latency**
  * *Cause:* GPU-accelerated rendering is hitting driver conflicts.
  * *Resolution:* Edit your settings file and set `USE_GPU = False` and `PREFER_OPENGL = False` to fallback to software rendering.

* **Patcher immediately processes text when copying from its own window**
  * *Cause:* The auto-disarm listener failed to catch the copy event.
  * *Resolution:* The patcher is designed to automatically disarm on internal copy events. If this fails, press `F9` to disarm manually before copying text from the console.
  
_Head to https://sharples3.gumroad.com/l/elastic-patcher to unlock the pro version with unlimited folder monitoring and recursive search._
