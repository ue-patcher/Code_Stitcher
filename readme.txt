🛠️ The Elastic Patcher (v2.12)
The Heuristic "Man-in-the-Middle" AI Alignment Tool
"Stop letting AI fumble your code. Start welding logic."
📑 Table of Contents
The Philosophy (Why an "Exoskeleton" is better than an "Agent")


1. The Philosophy: An Exoskeleton, Not an Agent
The current trend in AI development is the "Autonomous Agent." The industry is obsessed with building black-box systems that attempt to replace the developer—systems that take a prompt, "think" for a minute, and then vomit a massive pile of code back into your editor.
The Elastic Patcher rejects this.
We believe that you cannot replace the developer because the developer is the only one who truly understands intent. When you use an autonomous agent, you aren't a coder anymore—you’re a supervisor for a lazy intern who is prone to setting the building on fire every twenty minutes.
The "Intern" Problem (Why Agents Fumble)
If you’ve used Grok, GPT, or Claude for complex refactoring, you’ve seen the Truncation Trap. To save compute costs, the LLM will provide a "fix" that looks like this:

code
JavaScript
// ... existing logic ...
function fixBug() {
   // the new code here
}
// ... rest of file ...

If you copy-paste that, your file is dead. If an "Agent" handles that, it might realize the mistake—or it might blindly delete 500 lines of your production logic. You spend more time supervising the AI than you do building your product.

The Exoskeleton Approach

The Elastic Patcher is not an agent. It is a local, high-precision Exoskeleton for your brain.
It is a "Man-in-the-Middle" tool designed for developers who want to move at 10x speed without giving up the pilot’s seat.
The AI is the Parts Supplier: You use the LLM to generate the logic "part"—the specific function, the method, or the fix.
You are the Pilot: You decide where that part goes and if it’s high-quality enough to touch your disk.
The Patcher is the Assembly Line: Expansive heuristic logic handles the "heavy lifting" of surgical integration. It calculates indents, identifies scopes (even in messy HTML files), and welds the new logic into your existing file without you ever having to manually highlight a single line of code.
Why "Man-in-the-Middle" Wins:
Zero-Latency Development: You don't wait for a slow agent to "plan" and "execute." You copy a snippet, hit F9, and it’s done. You stay in the flow state.
The Laziness Firewall: The Patcher assumes the AI is trying to fumble the ball. It measures the "Code Signal" in your clipboard. If the AI hands you a hollow skeleton full of ... placeholders, the Patcher slams the door, protecting your codebase from corruption.
Token Efficiency: Why send a 1,000-line file back and forth to an LLM to change one method? With the Patcher, you only care about the snippet.
Stop being a supervisor. Start being a pilot. The Elastic Patcher turns the LLM into a high-powered parts factory, and turns you into the fastest logic-welder in the trenches.



2. Core Features: The Engine of Alignment
The Elastic Patcher isn’t just a script; it’s a heavyweight heuristic engine designed to handle the "violence" of real-world AI fumbles.
🛡️ The Laziness Firewall (Truncation Defense)
The #1 killer of AI-assisted code is the "Lazy Model." LLMs frequently try to save tokens by outputting hollow skeletons filled with // ... rest of code placeholders. If you copy-paste these into your project, you destroy your work.
Signal-to-Hole Calculation: The Patcher analyzes every clipboard entry. It calculates the ratio of functional code to "structural voids" (ellipses, snip comments, placeholders).
Automatic Rejection: If the "Code Signal" falls below a safety threshold (e.g., 95%), the Patcher slams the door. It refuses to apply the patch, protects your hard drive, and automatically copies a scolding prompt to your clipboard to force the LLM to provide a full, untruncated response.
🪗 Accordion Stitching Engine
Most patchers require a "Unified Diff" format or the full file context to work. The Elastic Patcher handles "Headless Snippets."
Fuzzy Anchoring: If you copy a random chunk of logic without a function name or class header, the Accordion Engine uses local fuzzy logic and similarity math to "anchor" the snippet to your existing code.
Dynamic Alignment: It intelligently compresses or expands the insertion point to match the surrounding logic. It handles the "carpentry" of the code so you don't have to worry about finding the exact line number.
🧬 Polyglot Scope Identification
The Patcher understands the "Final Boss" of programming: Indentation. It uses specialized syntax strategies to identify where logic belongs across diverse environments:
Python Strategy: High-precision indentation tracking. It understands dunder methods, decorators, and nested classes.
Brace-Based Strategy: Robust handling of JS, TS, C++, C#, Java, and Rust. It uses brace-depth counters to find the physical end of blocks, ignoring whitespace.
The HTML Boundary Fix: Unlike standard editors, the Patcher is "HTML Aware." It can surgically identify a class Particle indented deep inside a <script> tag in an .html file, update its methods, and respect the </script> boundary so code never "leaks" out into the <body>.
✂️ Class Decomposition (Surgical Updates)
When an LLM provides a replacement for a 500-line class but only includes 3 updated methods, standard tools often overwrite the entire class—deleting the other 497 lines of logic.
The Surgeon Logic: The Patcher detects if a class already exists on disk. Instead of replacing the class, it decomposes the snippet into individual methods.
Atomic Updates: It surgically replaces only the methods that have changed and appends any new ones, leaving your existing, un-modified logic completely untouched.
💾 The ep_backups Milestone System
Safety is paramount. Every time a patch touches your disk, the engine creates a localized backup in a hidden ep_backups/ directory.
Milestone Stability: The system calculates "Milestone Stability"—tracking how long your code has survived without a crash.
Instant Walkback: Using F11, you can visually browse the history of every single change made to a file and restore any previous version with a single keystroke. It’s like an infinite Undo button that survives even if your IDE crashes.



🛡️ The Laziness Firewall: Truncation Defense

The greatest threat to a stable codebase isn’t a bug—it’s LLM Truncation. To
save compute costs and "penny-pinch" tokens, modern AI models (like Grok, GPT-4,
and Claude) often get "lazy." They will generate a fix for your logic, but
hollow out the rest of the function with comments like // ... rest of code here
or # unchanged logic.

If you copy-paste that snippet, you aren't just adding a fix; you are deleting
your production logic.

The Elastic Patcher includes a heavyweight Laziness Firewall that assumes the AI
is trying to fumble the ball. It acts as a structural bouncer between your
clipboard and your hard drive.

🧠 How the Math Works: Code Signal vs. Holes

Every time you copy a snippet and ARM the Patcher, the engine performs a
Structural Density Analysis:

  - The Signal: It identifies actual, functional lines of logic (definitions,
    assignments, operations).
  - The Voids (Holes): It scans for conversational truncation markers,
    including:
      - Ellipses (..., …)
      - Snip markers ([snip], [rest of code])
      - Conversational laziness (// remains unchanged, # same as above)
      - HTML/CSS specific voids (<!-- ... -->, /* same styles */)

🧱 The Door-Slam Effect

If the Patcher detects that the Code Signal has dropped below a safe threshold
(e.g., your snippet is only 10% code and 90% placeholders), it slams the door
shut.

1.  Automatic Rejection: The injection process is instantly aborted. Your file
    on disk remains 100% untouched and safe.
2.  Audio/Visual Warning: You receive an ANSI-colored "REJECTED" log and an
    audio "Failure" cue.
3.  The Scold Loop: The Patcher automatically loads a specialized "Untruncated
    Demand" prompt into your clipboard. You can immediately Alt-Tab back to the
    LLM, hit Ctrl+V, and yell at the AI to stop being lazy and provide the full
    function body.

🕹️ User-in-the-Loop Override

We recognize that sometimes a tiny snippet is all you want. If the Patcher flags
a truncation, it doesn't just die—it gives you a [y/N] Prompt.

  - If you know the snippet is safe, you can force it through the Accordion
    Stitcher to attempt a rescue.
  - If you realize the AI was being a "lazy asshole," you hit N, and the
    firewall has successfully saved your day.

Stop proofreading the AI's placeholders. Let the Firewall defend your disk.



🪗 The Accordion Stitching Engine

Standard patching tools (like git apply) are rigid. They require perfect
"Unified Diff" headers, exact line numbers, and specific context lines. But AI
isn’t a version control system—it’s a conversational logic generator. LLMs often
hand you "Headless Snippets": chunks of code that are missing headers, class
names, or proper indentation.

The Accordion Stitching Engine is designed to handle this chaos. It treats your
code like a flexible instrument, "stretching" or "compressing" the logic to weld
new snippets into your existing files with mathematical precision.

🎯 Fuzzy Fingerprinting (Anchoring)

When you copy a headless snippet, the Accordion Engine doesn't look for line
numbers—it looks for a Structural Fingerprint.

  - Anchor Search: It analyzes the unique sequence of logic in your snippet and
    scans your target file for the closest matching pattern.
  - Context Awareness: It ignores noise like comments and varying whitespace to
    find the actual "meat" of the logic, ensuring the patch hits the target even
    if the file has shifted since the LLM last saw it.

🧵 Logical Stitching (Healing the Holes)

If an LLM provides a patch that is 90% full code but has a small "lazy" gap
(e.g., a single // ... unchanged line), the Accordion Engine switches into
Stitch Mode:

  - Preservation: It identifies the "holes" in the snippet.
  - Reconstruction: Instead of deleting the logic in those holes, it surgically
    "stitches" your original code back into the gap while applying the new
    updates around it.
  - Verticality Check: It ensures the resulting file maintains "Vertical
    Integrity"—preventing the engine from accidentally bloating the file or
    causing a structural collapse.

🕹️ The Interactive Shift (Fine-Tuning the Weld)

Sometimes the math is a tie between two possible locations. Instead of guessing
and breaking your build, the Patcher launches the Interactive Shift UI:

  - Visual Alignment: You see a live preview of the snippet placed inside your
    file.
  - Shift Control: Use the Arrow Keys to slide the snippet up or down
    line-by-line, or cycle between different candidate locations.
  - Commit with Confidence: You only hit Enter when the logic is visually
    aligned perfectly.

The Accordion Engine turns "guessing where to paste" into a high-speed assembly
line. You provide the parts; the engine handles the carpentry.




🧬 Polyglot Scope Identification

One of the biggest failures of standard AI "copy-pasting" is Scope Blindness. An
LLM might generate a perfect method for a class, but it has no idea where that
class begins or ends in your local file. If you paste it in the wrong place, you
break the indentation, orphan your logic, or leak code into the global scope.

The Elastic Patcher uses a Polyglot Syntax Engine that understands the
structural "physics" of different languages. It doesn't just look for text; it
identifies boundaries.

🐍 The Python Strategy: Conquering the "Final Boss"

Python is the "Final Boss" of heuristic patching because its logic depends
entirely on invisible whitespace.

  - Indent Tracking: The Patcher uses high-precision visual indentation
    tracking. It knows that a def at 4 spaces belongs to a class at 0 spaces.
  - Dunder & Decorator Awareness: It understands that @property or @staticmethod
    are part of the function they precede, ensuring they are moved or replaced
    as a single atomic unit.
  - Main Guard Protection: It recognizes the if __name__ == "__main__": block as
    a terminal barrier, preventing it from accidentally "slurping" your
    entry-point logic into a class body.

🔗 The Brace Strategy: Physical Boundaries (JS, TS, C++, C#, Java)

In brace-based languages, whitespace is a suggestion, but braces { } are the
law.

  - Brace-Depth Counters: Instead of guessing where a function ends based on
    line breaks, the Patcher uses a real-time depth counter. It walks the code
    until the brackets balance out, ensuring it captures the full physical body
    of the logic, no matter how many nested callbacks or closures are inside.
  - Poly-Definition Detection: It recognizes standard functions, arrow functions
    (const x = () =>), and class methods equally, allowing it to surgically
    target any modern JS/TS pattern.

🌐 The HTML "Boundary Fix"

Most tools treat an .html file as a single giant string. The Elastic Patcher
treats it as a Container.

  - Script-Block Isolation: If you have a class Particle indented deep inside a
    <script> tag, the Patcher is the only tool that can see it. It calculates
    the "Inner Indent" of the script block and adjusts the patch to match.
  - The </script> Firewall: The engine explicitly searches for HTML boundaries.
    It prioritizes inserting new global functions inside the script tags,
    ensuring code never "leaks" out past the </body> or </html> tags—a common
    mistake made by LLMs and basic agents.

✂️ Class Decomposition: Surgery vs. The Nuke

Standard tools usually "Nuke" a class—if the LLM provides an updated version,
the tool overwrites the entire 500-line block. If the LLM was lazy and
skipped 10 methods, those methods are now gone forever.

  - Decomposition Engine: When the Patcher sees a class in your clipboard, it
    checks if that class already exists on your disk.
  - Method-Level Patching: Instead of overwriting the class, it decomposes the
    snippet into its constituent methods. It then surgically replaces the
    changed methods and appends the new ones into the existing class body.

The Patcher speaks the language of your file. You don't have to worry about
where a class ends—the engine already balanced the braces for you.



3. The "Man-in-the-Middle" Workflow

The Elastic Patcher operates on a "Man-in-the-Middle" (MITM) philosophy. In a
world of slow, autonomous agents, the MITM workflow keeps the human developer in
the pilot’s seat. You don't "send a task" and wait—you conduct the AI like a
high-speed parts supplier.

The goal is Zero-Latency Development: moving from an LLM fix to a
production-ready file commit in under three seconds.

🛡️ Normal Arm (F9): The High-Speed Freeway

The standard workflow is designed for high-confidence, surgical updates.

1.  Prompt: You ask the LLM for a specific function or a method fix.
2.  Copy: You copy the resulting code block (or the entire LLM response).
3.  ARM (F9): You hit F9 to arm the patcher.
4.  Auto-Integration: The Patcher instantly scans your directories, identifies
    the target file, calculates the scope (Global vs. Class), aligns the
    indentation, and welds the code into place.
5.  Audio Confirmation: A "Success" cue tells you the code is on disk. You never
    had to switch tabs to your editor or look for a line number.

🎯 Tactical Arm (Shift+F9): The Surgeon’s Scalpel

When you are dealing with complex refactors or ambiguous snippets, the Tactical
Arm provides interactive routing.

1.  Strategy Selection: After hitting Shift+F9, the Patcher asks you how to
    handle the logic:
      - Smart Drop-in: Surgically replace matching blocks.
      - Full File Overwrite: For when you want to nuke the whole file.
      - Headless Snippet: Force the engine to anchor a random chunk of code.
2.  Scope Targeting: If the function is new, the Patcher lists potential files
    based on "Block Affinity" scores. You pick the target (e.g., 1.
    physics_sim.py) and then pick the scope (e.g., 2. class Particle).
3.  Real-time Logic Welding: The Patcher handles the physical insertion while
    you make the high-level decisions.

🕹️ The Manual Shift UI: Fine-Tuning the Weld

Heuristics are 95% accurate, but sometimes your code is too messy for a perfect
guess. If the Patcher finds multiple possible locations for a "Headless
Snippet," it launches the Manual Shift UI:

  - Visual Preview: You see a live, color-coded preview of exactly where the
    snippet will land, including 5 lines of context above and below.
  - Line Shifting: Use the UP / DOWN Arrows to slide the snippet line-by-line
    through your file.
  - Candidate Cycling: Use LEFT / RIGHT Arrows to jump between different
    structural matches (e.g., jumping from the draw method in class Star to the
    draw method in class Nebula).
  - Commit: Hit Enter to weld the logic only when it looks 100% correct.

⚡ The Zero-Latency Loop

This workflow turns you into a logic conductor:

1.  Compose (F7): Use the Patcher's internal editor to quickly draft a prompt,
    attach relevant local files, and include your Patcher logs.
2.  Send: Hit To Clipboard and paste to your LLM.
3.  Patch: Copy the AI's part, hit F9, and continue coding.

By eliminating the need to manually navigate files, find line numbers, or fix
"pasted-in" indentation, the Elastic Patcher keeps you in the flow state while
the AI does the grunt work. You aren't "supervising" an agent; you are armed
with an exoskeleton.


🛡️ Normal Arm (F9) vs. 🎯 Tactical Arm (Shift+F9)

The Elastic Patcher provides two distinct levels of engagement. You choose the
mode based on the complexity of the snippet and how much you trust the LLM’s
current output.

🛡️ Normal Arm (F9): The Heuristic Freeway

"Just weld it where it belongs."

The Normal Arm is designed for maximum velocity. It utilizes the full power of
the 6,500-line heuristic engine to make decisions on your behalf. This is the
mode you will use for 90% of your development.

  - Workflow: Copy code from LLM \rightarrow Hit F9.
  - Behavior:
      - The Patcher instantly analyzes the snippet's language and structure.
      - It identifies the Target File using block-affinity and filename hints.
      - It determines the Scope (e.g., automatically placing a method inside
        class Particle while ignoring a global draw function elsewhere).
      - It handles Indentation Alignment and executes the commit.
  - Best For: Existing function updates, full class replacements, clear bug
    fixes, and high-confidence LLM outputs.
  - Safety: If the engine finds multiple equally plausible targets, it will
    automatically "downgrade" to a selection menu to ensure you don't overwrite
    the wrong file.

🎯 Tactical Arm (Shift+F9): The Surgeon’s Scalpel

"I'll drive. You just handle the carpentry."

The Tactical Arm is an interactive routing mode. It turns off the "Auto-Pilot"
and puts you in the cockpit of the integration process. This is used when code
is ambiguous, or when you are performing complex architectural shifts.

  - Workflow: Copy code \rightarrow Hit Shift+F9.
  - The Selection Loop:
    1.  Select Strategy: You are prompted to choose the engine.
          - Smart Drop-In: Surgically replace/append blocks.
          - Full File Overwrite: Nuke and replace the whole target.
          - Headless Snippet: Activate fuzzy logic to anchor a random chunk of
            code.
    2.  Select Target File: The Patcher presents a ranked list of candidate
        files based on "Structural Affinity." You pick the winner (e.g., 1.
        main.py, 2. utils.py).
    3.  Select Scope: If the file contains multiple classes or structures, the
        Patcher asks: "Where does this logic go?" You pick the specific class
        body or choose the Global scope.
  - Best For: Injecting brand new functions, handling snippets from "lazy"
    models, dealing with files that have duplicate function names in different
    classes, and sensitive refactoring.
  - Control: This mode ensures that even if the AI fumbles the context, the
    human "Pilot" determines exactly where the new logic is welded.

Summary Table

| Feature         | 🛡️ Normal Arm (F9)                     | 🎯 Tactical Arm (Shift+F9)               |
| :-------------- | :------------------------------------- | :-------------------------------------- |
| **Speed**       | Instant (Zero clicks)                  | Fast (Interactive menus)                |
| **Philosophy**  | AI-Supplier $\rightarrow$ Patcher-Auto | AI-Supplier $\rightarrow$ User-Directed |
| **Routing**     | Heuristic Best Guess                   | User-Validated Selection                |
| **Strategy**    | Auto-Detect                            | Manual Choice                           |
| **Ideal Usage** | Routine updates & fixes                | New logic & ambiguous snippets          |

The Elastic Patcher allows you to switch between these modes instantly. Hit F9
when you’re in the flow; hit Shift+F9 when it’s time for surgery.







🕹️ Manual Shift UI: Fine-Tuning the Weld

Heuristics are incredibly powerful, but codebases are messy. Sometimes an LLM
provides a "Headless Snippet" (a chunk of logic without a function name) that
could plausibly fit in three different places, or perhaps the "Accordion" math
is off by a single line due to unique comment structures.

Instead of guessing—and potentially breaking your build—the Patcher launches the
Manual Shift UI. This is the final stage of the "Man-in-the-Middle" workflow,
giving you surgical, line-by-line control over the integration.

🔍 When It Triggers

The Manual Shift UI activates automatically in two scenarios:

1.  Headless Snippets: When the logic doesn't have a clear "named" anchor (like
    a def or class).
2.  Hunk Rescue: If a complex diff patch fails to find an exact match, the
    Patcher identifies the "closest plausible" area and asks you to help it
    finish the job.

📺 The Interface

The UI transforms your terminal into a live, color-coded preview of your target
file:

  - Context (Dimmed): You see 5–7 lines of the existing code on your disk above
    and below the insertion point.
  - The Snippet (Bright): The new code from your clipboard is highlighted in the
    middle, showing exactly how it will look once welded.
  - Metadata: The header displays the current Scope (e.g., SCOPE: class
    Particle) and the Structural Similarity Score.

🎮 Tactical Controls

You control the weld using standard keyboard navigation. You don't have to touch
your mouse or type a single line number.

  - ⬆️ / ⬇️ Arrows (Line Shifting): Slide the entire snippet up or down one line
    at a time. The preview updates instantly, allowing you to visually align
    brackets or move logic above/below specific comments.
  - ⬅️ / ➡️ Arrows (Candidate Cycling): If the Patcher found multiple
    "structural fingerprints" that match your snippet, use these keys to
    teleport the preview to the next candidate location (e.g., jumping from
    Star.draw to Nebula.draw).
  - ⏎ ENTER (Commit): Once the preview looks perfect, hit Enter. The Patcher
    executes the write, creates a backup, and plays the "Success" cue.
  - ESC (Abort): If you realize the snippet is garbage, hit Escape to discard
    the patch and keep your file untouched.

💡 The "No-Regrets" Integration

The Manual Shift UI eliminates the "Phantom Logic Error." We’ve all been there:
you paste code into an IDE, it looks fine, but you accidentally left an extra
closing brace at the bottom or pasted a function inside another function.

By using the Manual Shift UI, you see the result before it hits the disk. You
are the quality control inspector at the end of the assembly line, ensuring
every weld is flush and every bracket is balanced.

The Patcher handles the carpentry; you provide the final inspection.


🕹️ Manual Shift UI: Fine-Tuning the Weld

Heuristics are incredibly powerful, but codebases are messy. Sometimes an LLM
provides a "Headless Snippet" (a chunk of logic without a function name) that
could plausibly fit in three different places, or perhaps the "Accordion" math
is off by a single line due to unique comment structures.

Instead of guessing—and potentially breaking your build—the Patcher launches the
Manual Shift UI. This is the final stage of the "Man-in-the-Middle" workflow,
giving you surgical, line-by-line control over the integration.

🔍 When It Triggers

The Manual Shift UI activates automatically in two scenarios:

1.  Headless Snippets: When the logic doesn't have a clear "named" anchor (like
    a def or class).
2.  Hunk Rescue: If a complex diff patch fails to find an exact match, the
    Patcher identifies the "closest plausible" area and asks you to help it
    finish the job.



4. Installation & Requirements

The Elastic Patcher is designed for high-performance development environments.
It follows a "Portable First" philosophy—meaning it does not use a bloated
Windows installer, doesn't mess with your global environment variables, and
leaves no footprint on your system registry.

📦 The Portable ZIP

The Patcher is distributed as a single, self-contained .zip file. This allows
you to run it from any directory, a dedicated "Tools" folder, or even a USB
drive.

To install:

1.  Download the ElasticPatcher_v2.12.zip.
2.  Extract the contents to a folder on your drive (e.g.,
    C:\Tools\ElasticPatcher).
3.  Run elastic_patcher.exe.

📂 Contents of the Package

  - elastic_patcher.exe: The heavyweight heuristic engine and UI.
  - ep_settings.ini: The configuration file where you define your project
    directories.
  - elastic_patcher.ico: The high-resolution icon (used for taskbar and alt-tab
    identification).
  - sounds.dll & assets.dll: Custom binary blobs containing the audio cues and
    visual assets.

⚙️ Requirements

  - Operating System: Windows 10 or 11 (64-bit).
  - Hardware: Minimal. If your computer can run a code editor, it can run the
    Patcher.
  - Permissions: The Patcher requires read/write access to the folders you
    choose to monitor so it can create backups and apply patches.
  - No Python Required: Because the Patcher is compiled into a standalone
    binary, you do not need Python installed on your system to use it.

🚀 Initial Setup (The 60-Second Start)

Once you have extracted the files, follow these steps to arm your workspace:

1.  Open ep_settings.ini in any text editor.
2.  Define your projects: Under the [MONITOR] section, add the absolute paths to
    the codebases you want to work on.
      - Example: C:\Users\You\Documents\Projects\NebulaEngine
3.  Launch the EXE: Run elastic_patcher.exe.
4.  ARM it: Hit F9. The Patcher is now monitoring your clipboard.
5.  Test the Weld: Copy a function from an LLM, hit F9 again, and watch the
    heuristic engine identify your file and integrate the code instantly.

💡 Pro-Tip: Startup Placement

Since the Elastic Patcher is a "Man-in-the-Middle" tool, most power users keep
it running all day. We recommend pinning elastic_patcher.exe to your Taskbar.
The Patcher is designed with Window Transparency and Always-on-Top settings
(configurable in the .ini) so it can sit quietly in a corner of your screen
while you work.









5. Hotkeys & Commands Cheat Sheet

The Elastic Patcher is designed to be operated entirely by keyboard, ensuring
you never have to break your flow state.

| Key            | Action           | Description                                                                                            |
| :------------- | :--------------- | :----------------------------------------------------------------------------------------------------- |
| **F9**         | **ARM / DISARM** | Toggle standard monitoring. Arm, copy code, and let the heuristics handle the rest.                    |
| **Shift + F9** | **TACTICAL ARM** | Activate interactive routing. Manually choose targets, strategies, and scopes.                         |
| **F8**         | **SUPERLOCK**    | Force the Patcher to *only* look at a specific file. Perfect for heavy refactoring on a single module. |
| **F11**        | **WALKBACK**     | Open the Milestone History. Visually browse and restore previous versions of any file.                 |
| **Ctrl + Z**   | **UNDO**         | Instantly roll back the last patch (survives IDE crashes).                                             |
| **Ctrl + Y**   | **REDO**         | Re-apply a rolled-back patch.                                                                          |
| **F7**         | **LLM COMPOSE**  | Open the internal prompt editor. Attach local files and patch logs to your next prompt.                |
| **F10**        | **SUMMARY**      | View a diagnostic report of the current session's patches and stability.                               |
| **F12**        | **CLEAR**        | Wipe the terminal buffer and return to the startup banner.                                             |

🎮 Manual Shift UI Controls

When the Accordion Engine requires human alignment:

  - ⬆️ / ⬇️ Arrows: Shift the snippet up or down line-by-line.
  - ⬅️ / ➡️ Arrows: Cycle through different candidate locations in the file.
  - ⏎ ENTER: Commit the weld to disk.
  - ESC: Abort the patch.

6. Safety & Backups (The ep_backups System)

The Elastic Patcher treats your source code as sacred. Every time the engine
touches a file, it creates a safety net.

📂 The ep_backups/ Directory

The Patcher automatically creates a hidden ep_backups/ folder inside your
project directory. This folder contains a granular history of every "weld"
performed by the engine.

📝 Milestone Naming Convention

Backups use a unique naming scheme to track your progress across sessions:
[filename]_[session]_[job]_[write].bak

  - Session: Increments every time you launch the tool.
  - Job: A unique letter (A, B, C) for every distinct clipboard snippet.
  - Write: Increments if you modify the same snippet and re-apply it.

🛡️ The Verticality & Horizontal Guard

Before a patch is committed, the engine performs a Sanity Scan:

  - Verticality Check: If the patch would cause the file's line count to plummet
    (e.g., Grok accidentally deleted 80% of your code), the commit is ABORTED to
    prevent structural collapse.
  - Horizontal Guard: If a line becomes abnormally long (suggesting a
    concatenation error or "minification" fumble), the engine blocks the write.

7. Licensing

We believe in empowering individual developers while ensuring that the
heavyweight engineering behind the Patcher is sustainable.

👨‍💻 Personal Use (Free Edition)

Cost: $0

  - Full access to the Heuristic Engine and Syntax Strategies.
  - Ideal for hobbyists, students, and non-commercial open-source projects.
  - Requirement: You are not being paid to write the code you are patching.

🏢 Professional Edition (Commercial Use)

Cost: $49/year per developer (or $99 for a Lifetime Seat)

  - Required for any use in a corporate, freelance, or commercial environment.
  - Supports the ongoing "Battle-Data" logic updates to keep up with evolving
    LLM quirks.
  - The Value Prop: If the Patcher saves you just one hour of debugging an AI
    fumble per year, it has already paid for itself.

8. Support & Feedback

Since the Elastic Patcher is a heuristic engine, it thrives on edge cases. If
you encounter a "Wonky Patch" or a language structure that fumbles the logic:

1.  Check the Audit Log: Look for ep_patch.log in your project folder. It
    contains a record of the AI's snippet and the Patcher's decision.
2.  Report Issues: Visit our [GitHub Issues] page.
3.  Provide Snippets: When reporting a bug, please include the snippet from your
    clipboard and the target file's structure. This "Battle Data" allows us to
    harden the 6,500-line logic engine for everyone.

"Stop letting AI fumble your code. Start welding logic with the Elastic
Patcher."
