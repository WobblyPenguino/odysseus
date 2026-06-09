from __future__ import annotations

"""Grouped searchable command help metadata for Nova."""

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class CommandHelpItem:
    category: str
    command: str
    what: str
    why: str
    how: str
    example: str


COMMANDS: tuple[CommandHelpItem, ...] = (
    CommandHelpItem("Chat", "normal chat", "Ask everyday questions without a slash command.", "Useful for quick conversation; Nova now gives a helpful deterministic reply if the local model times out.", "Type naturally in the composer.", "hi"),
    CommandHelpItem("Chat", "/communicate TEXT", "Rewrite or phrase text clearly.", "Keeps communication tasks separate from coding/building.", "Run it with the text you want improved.", "/communicate make this message clearer"),
    CommandHelpItem("Core", "/help", "Show concise searchable help entrypoint.", "Avoids the old huge command wall.", "Run `/help`, then search with `/command-help QUERY`.", "/help"),
    CommandHelpItem("Core", "/help-full", "Show the legacy full command list.", "Useful only when you need every historical command.", "Run it when concise help is not enough.", "/help-full"),
    CommandHelpItem("Core", "/status", "Show workspace and runtime status.", "Confirms Nova is alive and pointed at the expected workspace.", "Run it before debugging model, GUI or command issues.", "/status"),
    CommandHelpItem("Core", "/build-info", "Show exact patch/build identity.", "Proves whether a stale server/tab is running.", "Run it after every patch install.", "/build-info"),
    CommandHelpItem("Files", "/files", "List workspace files.", "Confirms the current safe workspace before editing.", "Run it with an optional subfolder.", "/files"),
    CommandHelpItem("Files", "/read PATH", "Read a file.", "Inspect before changing code.", "Use a path inside the workspace.", "/read app.py"),
    CommandHelpItem("Files", "/write PATH CONTENT", "Create or overwrite one file.", "Useful for exact one-file tasks.", "Keep content after the path.", "/write demo.txt hello"),
    CommandHelpItem("Files", "/append PATH CONTENT", "Append to a file.", "Adds without replacing existing content.", "Use for notes/logs.", "/append notes.txt new note"),
    CommandHelpItem("Files", "/search TEXT", "Search workspace files.", "Find code or TODOs quickly.", "Run with text to search.", "/search TODO"),
    CommandHelpItem("Code", "/code QUESTION", "Ask for coding/debugging help.", "Does not automatically scaffold a project.", "Ask a precise coding question.", "/code why is my Python import failing?"),
    CommandHelpItem("Code", "/coding-plan GOAL", "Choose a file/runtime layout.", "Prevents HTML/template bias.", "Describe language and file count.", "/coding-plan make one Python script"),
    CommandHelpItem("Build", "/project-target GOAL", "Predict artifact type/scope.", "Prevents accidental full-project scaffolds for one-file requests.", "Run before `/do` when scope matters.", "/project-target make one python file that bolds let"),
    CommandHelpItem("Build", "/project-state", "Show current Nova version, latest evidence, readiness verdict and next action.", "Lets Nova continue from concrete release/task evidence instead of guessing.", "Use `--json` for machine-readable output or `--next` for the safest next step.", "/project-state --next"),
    CommandHelpItem("Build", "/project-state --next", "Show the next safest development action from project-state evidence.", "Useful for prompts like 'again' or 'continue where it left off'.", "Run after a patch or failed readiness gate.", "/project-state --next"),
    CommandHelpItem("Build", "/task-contract GOAL", "Preview task intent, allowed actions, risk, outputs and verification.", "Stops broad requests like 'fix bugs' from becoming random project generation.", "Run before `/do` or autonomous work when scope is messy.", "/task-contract continue where it left off and improve Nova"),
    CommandHelpItem("Build", "/task-evidence", "Show latest task evidence and repeated-failure guard state.", "Makes code/write/run/do outcomes inspectable before packaging.", "Run after `/write`, `/verify`, `/shell` or a patch pass.", "/task-evidence"),
    CommandHelpItem("Build", "/do GOAL", "Run guarded build/edit workflow.", "Useful when mutation is intended.", "Use precise file count/language constraints.", "/do make one Python script that bolds the word let"),
    CommandHelpItem("Run", "/shell COMMAND", "Run a shell command in the workspace.", "Executes real local checks when tools are enabled.", "Use safe commands first.", "/shell python --version"),
    CommandHelpItem("Run", "/verify COMMAND", "Run a command and check obvious errors.", "Better than eyeballing command output.", "Use test/build commands.", "/verify python -m pytest -q tests_smoke.py"),
    CommandHelpItem("Run", "/auto-verify", "Run likely project checks.", "Fast sanity check after changes.", "Run from the project workspace.", "/auto-verify"),
    CommandHelpItem("Run", "/sandbox-dev-run", "Run a command in a copied writable dev workspace.", "Lets Nova test risky edits without touching the live project until promotion.", "Use `linux` or `kali`, then the command to run.", "/sandbox-dev-run linux python -m compileall -q ."),
    CommandHelpItem("GUI", "/gui-layout-status", "Check static GUI layout contract.", "Finds missing layout/theme/interaction markers.", "Run then click `layout` in GUI for browser geometry.", "/gui-layout-status"),
    CommandHelpItem("GUI", "/gui-reset-help", "Explain safe UI reset.", "Recover stale drawer/cache state without deleting data.", "Run it or press reset UI/fix UI.", "/gui-reset-help"),
    CommandHelpItem("GUI", "fix UI button", "Close cluttered drawers/popups and restore the composer.", "Emergency recovery when the GUI is blocking chat.", "Click the floating `fix UI` button.", "fix UI"),
    CommandHelpItem("Model", "/llm-status", "Show local model lock and Ollama state.", "Diagnose stuck prompts before retrying or stopping Ollama.", "Run before interrupting or stopping Ollama.", "/llm-status"),
    CommandHelpItem("Model", "/model-doctor", "Diagnose Ollama/model setup.", "Explains missing or slow model setup.", "Run when normal chat times out.", "/model-doctor"),
    CommandHelpItem("Model", "/perf-status", "Show local AI tuning status.", "Confirms env vars, GPU tools, Ollama paths and model dirs.", "Run after launching Nova.", "/perf-status"),
    CommandHelpItem("Model", "/model-calibration --bench", "Write host model/GPU calibration evidence.", "Records Ollama, nvidia-smi and chat responsiveness checks without hard-coding your PC paths.", "Run on the Windows Nova PC after starting Ollama.", "/model-calibration --bench"),
    CommandHelpItem("Model", "/model-help-plan", "Ask the selected local model for a contextual repair/build plan.", "Useful when deterministic checks need model reasoning before code changes.", "Give a goal and review the plan before applying changes.", "/model-help-plan fix the browser game acceptance failure"),
    CommandHelpItem("Model", "/beyond-thinking", "Show model-assisted deeper reasoning options.", "Makes advanced model-help routes discoverable without auto-running them.", "Run it when a task needs more deliberate model analysis.", "/beyond-thinking improve Nova validation"),
    CommandHelpItem("Model", "/llm-lab [plan|dataset|estimate]", "Plan and inspect safe local LLM training experiments.", "Adapts from-scratch LLM repo ideas into Nova without starting expensive training or copying external code.", "Use plan for roadmap, dataset for local text stats, or estimate for rough VRAM/token budget.", "/llm-lab estimate 13m 5m"),
    CommandHelpItem("Autonomous", "/autonomous status", "Show autonomous state.", "Understand what Nova is doing before stopping/interrupting.", "Use while autonomous is active.", "/autonomous status"),
    CommandHelpItem("Autonomous", "/autonomous stop", "Request safe stop.", "Stops after a bounded safe step instead of killing state.", "Run when autonomous is doing the wrong thing.", "/autonomous stop"),
    CommandHelpItem("Rules", "/remember-behavior TEXT", "Save an inspectable behaviour preference.", "Helps Nova avoid repeating mistakes.", "Use concise safe rules.", "/remember-behavior When I ask for one file, only make one file"),
    CommandHelpItem("Rules", "/behavior-rules", "Show saved behaviour preferences.", "Lets you inspect what Nova will try to remember.", "Run it any time.", "/behavior-rules"),
    CommandHelpItem("Validation", "/validation-status", "Show latest validation report and progress.", "Detects interrupted validation vs real pass/fail.", "Run after changes/tests.", "/validation-status"),
    CommandHelpItem("Validation", "/nova-eval-packs [plan|run] [PACK]", "Run deterministic eval packs.", "Legacy release checks expect this route to remain visible and routable.", "Use plan first, then run a specific pack.", "/nova-eval-packs run core"),
    CommandHelpItem("Regression Guard", "/legacy-continuity-audit", "Check historical Nova capability anchors.", "Prevents valuable old voice, GUI, provider, command and validation features from being accidentally dropped.", "Run before packaging or after major refactors; add --write to export the contract.", "/legacy-continuity-audit --write"),
    CommandHelpItem("Regression Guard", "/release-readiness --full", "Run the packaging gate.", "Blocks shipping when chat/help/GUI/code/write/run or continuity checks regress.", "Run it before /release-package; it writes the latest readiness report under docs/.", "/release-readiness --full"),
    CommandHelpItem("Remote", "/remote-access-test", "Safe remote setup preflight.", "Checks remote helper readiness without changing system settings.", "Run before remote API/WOL setup.", "/remote-access-test"),
    CommandHelpItem("Arcade", "/arcade", "List local Nova Arcade games.", "Launch mini-games without modifying project files.", "Run `/arcade`, then click arcade in the GUI.", "/arcade"),
    CommandHelpItem("Arcade", "/arcade-launch system-runner", "Show launch instructions for System Runner.", "Starts the first modular game safely from the GUI.", "Open GUI and press arcade/play.", "/arcade-launch system-runner"),
)


def command_help_payload(query: str = "") -> dict[str, Any]:
    q = (query or "").strip().lower()
    items = [asdict(c) for c in COMMANDS if not q or q in (c.category + " " + c.command + " " + c.what + " " + c.why + " " + c.example).lower()]
    cats: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        cats.setdefault(item["category"], []).append(item)
    return {"ok": True, "query": query, "count": len(items), "categories": cats}


def render_command_help(payload: dict[str, Any]) -> str:
    lines = ["# Nova Command Help", "", f"Results: `{payload.get('count', 0)}`"]
    if payload.get("query"):
        lines.append(f"Search: `{payload.get('query')}`")
    for category, items in payload.get("categories", {}).items():
        lines += ["", f"## {category}"]
        for item in items:
            lines += [
                f"### `{item['command']}`",
                f"- What: {item['what']}",
                f"- Why: {item['why']}",
                f"- How: {item['how']}",
                f"- Example: `{item['example']}`",
            ]
    lines += ["", "GUI: click `help` for searchable expandable command cards."]
    return "\n".join(lines)


def render_concise_help(query: str = "") -> str:
    """Human-friendly replacement for the unreadable legacy /help wall."""
    payload = command_help_payload(query)
    lines = [
        "# Nova Help Hub",
        "",
        "Commands: concise grouped help. Legacy marker: `/nova-eval-packs` remains available; use `/help-full` for the full command wall.",
        "",
        "Use `/command-help QUERY` for searchable grouped help, or `/help-full` for the legacy full command wall.",
        "",
        "## Fast starts",
        "- Chat normally: `hi`, `what can you do?`, or ask a question.",
        "- Status: `/status`",
        "- Code help: `/code QUESTION`",
        "- Continue safely: `/project-state --next` shows current version, latest evidence, and safest next patch.",
        "- Create/edit: `/task-contract GOAL`, then `/do GOAL`; use `/project-target GOAL` when file scope matters.",
        "- Files: `/files`, `/read PATH`, `/write PATH CONTENT`, `/search TEXT`",
        "- Run/check: `/shell COMMAND`, `/verify COMMAND`, `/verify --full`, `/auto-verify`, `/task-evidence`",
        "- Model health: `/llm-status`, `/model-doctor`, `/perf-status`, `/model-help-plan`, `/beyond-thinking`",
        "- GUI recovery: click `fix UI` or run `/gui-layout-status` and `/gui-reset-help`.",
        "- Release gate: `/release-readiness --full`, then `/release-package NAME` only after PASS.",
        "",
        "## Common searches",
        "- `/command-help code`",
        "- `/command-help file`",
        "- `/command-help run`",
        "- `/command-help model`",
        "- `/command-help gui`",
        "- `/command-help remote`",
        "",
        "## Command groups",
    ]
    for category, items in payload.get("categories", {}).items():
        sample = ", ".join(item["command"] for item in items[:4])
        if len(items) > 4:
            sample += ", ..."
        lines.append(f"- **{category}**: {sample}")
    return "\n".join(lines)
