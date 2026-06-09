from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

from .game_design import analyze_game_request


@dataclass
class AcceptanceCheck:
    name: str
    ok: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProjectAcceptanceContract:
    artifact_type: str
    required_behaviours: list[str]
    expected_files: list[str]
    verification_focus: list[str]
    repair_hints: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_project_acceptance_contract(user_text: str) -> ProjectAcceptanceContract:
    low = (user_text or "").lower()
    if any(term in low for term in ["typescript", "ts-node", "tsx", "ts cli", "typescript cli"]):
        return ProjectAcceptanceContract(
            artifact_type="typescript_cli_tool",
            expected_files=["package.json", "tsconfig.json", "src/index.ts", "README.md"],
            required_behaviours=["TypeScript source file", "typed command/input handling", "accurate build/typecheck/start scripts"],
            verification_focus=["tsconfig", "src/index.ts", "package.json scripts", "typecheck"],
            repair_hints=["Do not convert TypeScript requests into browser-only JavaScript; create src/index.ts plus package metadata."],
        )
    if any(term in low for term in ["fastapi", "rest api", "api server", "backend", "endpoint", "uvicorn"]):
        return ProjectAcceptanceContract(
            artifact_type="python_fastapi_service",
            expected_files=["main.py", "requirements.txt", "README.md"],
            required_behaviours=["FastAPI app object", "at least one route", "health/sample response", "clear localhost run instructions"],
            verification_focus=["FastAPI", "route", "py_compile", "uvicorn", "README"],
            repair_hints=["Create a real FastAPI app in main.py and keep install/run steps accurate."],
        )
    if any(term in low for term in ["java", "javac", "swing"]):
        return ProjectAcceptanceContract(
            artifact_type="java_cli_or_desktop_app",
            expected_files=["Main.java", "README.md"],
            required_behaviours=["public class matching filename", "runnable main method or Swing entrypoint", "clear javac/java run instructions"],
            verification_focus=["class Main", "public static void main", "javac", "README"],
            repair_hints=["Do not convert Java requests into browser code; create compileable Java source."],
        )
    if any(term in low for term in ["powershell", "ps1"]):
        return ProjectAcceptanceContract(
            artifact_type="powershell_automation_script",
            expected_files=["script.ps1", "README.md"],
            required_behaviours=["runnable PowerShell script", "safe example command", "dry-run or WhatIf for risky operations"],
            verification_focus=["scriptblock syntax", "param", "WhatIf", "README"],
            repair_hints=["Use PowerShell syntax and include safe dry-run behaviour for file-changing tasks."],
        )
    if any(term in low for term in ["batch file", "windows batch", ".bat", "cmd script", "batch script"]):
        return ProjectAcceptanceContract(
            artifact_type="batch_script",
            expected_files=["script.bat", "README.md"],
            required_behaviours=["runnable batch file", "setlocal/environment handling", "safe usage/help output", "quoted paths"],
            verification_focus=["@echo off", "setlocal", "cmd", "README"],
            repair_hints=["Use Windows batch syntax and avoid destructive actions unless dry-run or explicit confirmation exists."],
        )
    if any(term in low for term in ["node", "npm", "javascript cli", "js cli", "command line tool"]):
        return ProjectAcceptanceContract(
            artifact_type="node_cli_tool",
            expected_files=["index.js", "package.json", "README.md"],
            required_behaviours=["Node entrypoint", "argument or stdin handling", "accurate npm/node run command"],
            verification_focus=["node --check", "process.argv", "package.json", "README"],
            repair_hints=["Use Node CLI files rather than browser DOM code when the prompt asks for a command-line tool."],
        )
    if any(term in low for term in ["python", "script", "automation", "csv", "parse", "convert files"]):
        return ProjectAcceptanceContract(
            artifact_type="python_cli_script",
            expected_files=["main.py", "README.md"],
            required_behaviours=["runnable Python entrypoint", "clear input/output handling", "error handling", "py_compile verification"],
            verification_focus=["if __name__", "argparse or main", "py_compile", "README"],
            repair_hints=["Use a Python source file for script/data/automation tasks instead of static HTML."],
        )
    if any(term in low for term in ["markdown", "readme", "documentation", "docs"]) and not any(term in low for term in ["website", "browser", "html", "web app", "server", "script", "cli"]):
        return ProjectAcceptanceContract(
            artifact_type="markdown_document",
            expected_files=["README.md"],
            required_behaviours=["Markdown headings", "requested content covered", "examples or steps where useful", "no false claim of runnable code"],
            verification_focus=["README.md", "headings", "requested sections", "accuracy"],
            repair_hints=["Produce a complete Markdown document rather than inventing code files for documentation-only requests."],
        )
    if any(term in low for term in ["json config", "json schema", "config file", "configuration file", "settings file", "settings json"]) or ("json" in low and not any(term in low for term in ["parse", "parser", "python", "script", "api", "browser", "website", "game"])):
        return ProjectAcceptanceContract(
            artifact_type="json_config",
            expected_files=["config.json", "README.md"],
            required_behaviours=["valid JSON", "clear setting names", "safe placeholder values for secrets", "README explains settings"],
            verification_focus=["json parse", "config.json", "README", "no real secrets"],
            repair_hints=["Keep JSON strict and put explanatory comments in README.md, not inside the JSON file."],
        )
    if "calculator" in low or "calc" in low:
        return ProjectAcceptanceContract(
            artifact_type="calculator",
            expected_files=["index.html", "app.js"],
            required_behaviours=[
                "visible numeric input/buttons",
                "multiple arithmetic operations",
                "equals/calculate action",
                "clear/reset and backspace/delete",
                "visible result/display update",
                "click or keyboard event wiring",
            ],
            verification_focus=["digits", "operators", "event handlers", "result updates", "reset controls"],
            repair_hints=["Implement real calculator state and event handlers, not a static mock-up."],
        )
    if "todo" in low or "to-do" in low or "task" in low:
        return ProjectAcceptanceContract(
            artifact_type="todo_app",
            expected_files=["index.html", "app.js"],
            required_behaviours=[
                "add task",
                "delete/remove task",
                "complete/toggle task",
                "render list updates",
                "state storage or in-memory task array",
            ],
            verification_focus=["add", "delete", "complete", "render", "state"],
            repair_hints=["Use a tasks array and re-render after every add/delete/toggle action."],
        )
    if "snake" in low:
        return ProjectAcceptanceContract(
            artifact_type="snake_game",
            expected_files=["index.html", "app.js"],
            required_behaviours=[
                "snake movement",
                "keyboard controls",
                "food spawning",
                "score and growth",
                "collision/end state",
                "restart/reset",
                "instructions",
            ],
            verification_focus=["snake", "food", "score", "collision", "restart", "controls"],
            repair_hints=["Use grid movement with food, growth, collision, score and restart."],
        )
    if "game" in low or "pong" in low:
        game = analyze_game_request(user_text)
        required = [
            "player controls",
            "game loop/update loop",
            "objective matching requested game type",
            "score/progress",
            "collision or gameplay interaction",
            "restart/end state",
            "instructions",
        ]
        for behaviour in game.required_behaviours:
            if behaviour not in required:
                required.append(behaviour)
        focus = ["controls", "loop", "score", "interaction", "restart", "instructions"] + list(game.core_objects[:4]) + list(game.mechanics[:4])
        return ProjectAcceptanceContract(
            artifact_type="browser_game",
            expected_files=["index.html", "app.js"],
            required_behaviours=required,
            verification_focus=focus,
            repair_hints=[
                "Create a custom game matching the requested theme and mechanics, not a fixed Dodge template.",
                "Include real controls, game state, objective, scoring/progress, interaction/collision, restart and visible instructions.",
            ],
        )
    if "file organiser" in low or "file organizer" in low or "organise files" in low or "organize files" in low:
        return ProjectAcceptanceContract(
            artifact_type="automation_script",
            expected_files=["file_organiser.py", "README.md"],
            required_behaviours=["safe dry-run mode", "temporary fixture verification", "clear file movement rules"],
            verification_focus=["dry run", "temp fixtures", "path safety"],
            repair_hints=["Never test on real user files; use temp fixture files and dry-run first."],
        )
    return ProjectAcceptanceContract(
        artifact_type="generic_project",
        expected_files=["README.md"],
        required_behaviours=["matches the user request", "has clear run/open instructions", "has verification notes"],
        verification_focus=["request match", "instructions", "verification"],
        repair_hints=["Add the smallest project-specific behaviour needed to satisfy the request."],
    )


def evaluate_project_acceptance(user_text: str, created_files: list[str], summary: str) -> dict[str, Any]:
    contract = build_project_acceptance_contract(user_text)
    hay = " ".join([summary or ""] + [str(f) for f in created_files or []]).lower().replace("\\", "/")
    checks: list[AcceptanceCheck] = []

    def has_any(*tokens: str) -> bool:
        return any(t.lower() in hay for t in tokens)

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(AcceptanceCheck(name, bool(ok), detail))

    for expected in contract.expected_files:
        if expected == "README.md":
            # README is desirable but not always mandatory for one-file browser artifacts.
            add("file:" + expected, has_any(expected.lower(), "readme", "instructions", "how to"), "README or visible instructions evidence")
        else:
            add("file:" + expected, any(str(f).lower().replace("\\", "/").endswith(expected.lower()) for f in created_files or []) or expected.lower() in hay, "Expected project file")

    if contract.artifact_type == "calculator":
        add("calculator_input", has_any("0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "digit", "number"), "Numeric input/buttons")
        add("calculator_operations", sum(1 for t in ["+", "-", "*", "/", "operator", "calculate"] if t in hay) >= 2, "Multiple arithmetic operations")
        add("calculator_reset", has_any("clear", "backspace", "delete", "reset"), "Clear/backspace/reset")
        add("calculator_result", has_any("result", "display", "screen", "textcontent", "value"), "Visible result update")
        add("calculator_events", has_any("addeventlistener", "onclick", "keydown", "input"), "Event wiring")
    elif contract.artifact_type == "todo_app":
        add("todo_state", has_any("tasks", "todo", "todos", "tasklist"), "Task state")
        add("todo_add", has_any("add", "push", "create"), "Add task")
        add("todo_delete", has_any("delete", "remove", "splice", "filter"), "Delete/remove task")
        add("todo_complete", has_any("complete", "done", "checked", "toggle"), "Complete/toggle task")
        add("todo_render", has_any("render", "appendchild", "createelement", "innerhtml", "map"), "Render updates")
    elif contract.artifact_type in {"browser_game", "snake_game"}:
        add("game_controls", has_any("keydown", "keyup", "touchstart", "pointer", "controls"), "Controls")
        add("game_loop", has_any("requestanimationframe", "setinterval", "update", "draw", "loop"), "Game loop")
        add("game_score", has_any("score", "level", "lives", "progress"), "Score/progress")
        add("game_interaction", has_any("collision", "collide", "food", "enemy", "obstacle", "ball", "hit"), "Collision/interaction")
        add("game_restart", has_any("restart", "reset", "gameover", "game over", "startgame"), "Restart/end state")
        add("game_instructions", has_any("instructions", "how to", "use arrow", "press", "controls"), "Visible instructions")
        game = analyze_game_request(user_text)
        if game.explicit_game_type and contract.artifact_type != "snake_game":
            theme_tokens = [t for t in re.findall(r"[a-z0-9]+", game.requested_game_type.lower()) if t != "game"]
            add("game_requested_theme", any(has_any(t) for t in theme_tokens) if theme_tokens else True, "Requested game theme is visible in implementation")
        if game.genre == "platformer":
            add("platformer_gravity_logic", has_any("gravity") and has_any("vy", "velocity"), "Platformer gravity and vertical velocity")
            add("platformer_jump_logic", has_any("jump") and has_any("onground", "grounded"), "Grounded jump mechanic")
            add("platformer_collision_logic", has_any("platforms", "platform") and has_any("collision", "rectshit", "overlap", "landing", "landon"), "Platform collision/landing")
            add("platformer_goal_logic", has_any("goal") and has_any("win", "reached"), "Reachable goal/win condition")
        alias_groups = {
            "obstacles": ["obstacle", "obstacles", "block", "blocks", "hazard", "hazards", "enemy", "enemies"],
            "dodging": ["dodge", "dodging", "avoid", "avoiding", "evade", "hazard", "obstacle", "block"],
            "collecting": ["collect", "collecting", "target", "coin", "food", "pickup"],
        }
        for obj in game.core_objects[:3]:
            if obj not in {"player", "targets", "hazards"}:
                aliases = alias_groups.get(obj, [obj])
                add("game_object:" + obj, has_any(*aliases), "Requested game object/mechanic: " + obj)
        for mech in game.mechanics[:3]:
            tokens = alias_groups.get(mech, [t for t in re.findall(r"[a-z0-9]+", mech.lower()) if len(t) > 3])
            add("game_mechanic:" + mech, any(has_any(t) for t in tokens) if tokens else True, "Requested game mechanic: " + mech)
        if contract.artifact_type == "snake_game":
            add("snake_theme", has_any("snake", "food", "growth", "direction"), "Snake-specific theme")
    elif contract.artifact_type == "python_fastapi_service":
        add("fastapi_app", has_any("fastapi", "app =", "app=", "FastAPI"), "FastAPI app object")
        add("fastapi_route", has_any("@app.get", "@app.post", "route"), "At least one API route")
        add("python_entry", has_any("main.py", "py_compile", "uvicorn"), "Python/FastAPI run or verify command")
    elif contract.artifact_type == "java_cli_or_desktop_app":
        add("java_file", has_any("main.java", "class main", "public class"), "Java source/class evidence")
        add("java_entrypoint", has_any("public static void main", "swingutilities", "jframe"), "Java main or Swing entrypoint")
        add("java_run", has_any("javac", "java main"), "javac/java run instructions")
    elif contract.artifact_type == "node_cli_tool":
        add("node_entry", has_any("index.js", "node index.js", "process.argv", "readline"), "Node CLI entrypoint")
        add("node_package", has_any("package.json", "npm", "scripts"), "package.json or Node run script")
        add("node_verify", has_any("node --check", "syntax"), "Node syntax verification")
    elif contract.artifact_type == "typescript_cli_tool":
        add("typescript_source", has_any("src/index.ts", ".ts", "typescript", "interface", "type "), "TypeScript source evidence")
        add("typescript_config", has_any("tsconfig.json", "compileroptions"), "TypeScript compiler config")
        add("typescript_package", has_any("package.json", "typecheck", "npm run build", "scripts"), "package scripts for build/typecheck")
        add("typescript_cli_io", has_any("process.argv", "readline", "stdin", "args"), "CLI input/output handling")
    elif contract.artifact_type == "powershell_automation_script":
        add("powershell_file", has_any("script.ps1", "powershell"), "PowerShell script file")
        add("powershell_safety", has_any("whatif", "dry-run", "dry run", "-whatif"), "Safe dry-run/WhatIf behaviour")
        add("powershell_verify", has_any("scriptblock", "syntax", "executionpolicy"), "PowerShell syntax/run instructions")
    elif contract.artifact_type == "batch_script":
        add("batch_file", has_any("script.bat", "@echo off", "cmd /c"), "Batch script file")
        add("batch_environment", has_any("setlocal", "enabledelayedexpansion"), "Batch environment handling")
        add("batch_safety", has_any("dry-run", "dry run", "confirm", "usage", "--help"), "Safe usage/help output")
    elif contract.artifact_type == "markdown_document":
        add("markdown_file", has_any("readme.md", "markdown", "# "), "Markdown document file")
        add("markdown_structure", has_any("#", "##", "steps", "examples", "summary"), "Document structure")
        add("markdown_accuracy", not has_any("todo only", "placeholder", "lorem ipsum"), "No obvious placeholder-only document")
    elif contract.artifact_type == "json_config":
        add("json_file", has_any("config.json", ".json"), "JSON config file")
        add("json_settings", has_any("settings", "config", "option", "schema", "default"), "Config/settings content")
        add("json_secret_safety", has_any("placeholder", "example", "changeme", "do not commit", "secret"), "Secret placeholders or safety notes")
    elif contract.artifact_type == "python_cli_script":
        add("python_file", has_any("main.py", "if __name__", "argparse", "def main"), "Python entrypoint")
        add("python_io", has_any("argparse", "input(", "sys.argv", "pathlib", "csv", "json"), "Input/output handling")
        add("python_verify", has_any("py_compile", "pytest", "python -m"), "Python verification command")

    passed = sum(1 for c in checks if c.ok)
    total = len(checks) or 1
    percent = round(100 * passed / total, 1)
    missing = [c.detail for c in checks if not c.ok]
    return {
        "contract": contract.to_dict(),
        "checks": [c.to_dict() for c in checks],
        "passed": percent >= 80 and not missing[:2],
        "percent": percent,
        "missing_behaviours": missing,
        "repair_hints": contract.repair_hints,
        "summary": f"{passed}/{total} acceptance checks passed ({percent}%).",
    }


def build_project_repair_plan(user_text: str, acceptance: dict[str, Any]) -> dict[str, Any]:
    missing = acceptance.get("missing_behaviours") or []
    contract = acceptance.get("contract") or {}
    artifact = contract.get("artifact_type", "project")
    actions = []
    for item in missing[:8]:
        actions.append(f"Add or repair: {item}")
    if not actions:
        actions.append("No repair action required by the static acceptance contract.")
    return {
        "artifact_type": artifact,
        "recommended_scope": "project-local files only",
        "actions": actions,
        "verification": ["rerun project quality verification", "recheck request match", "open/run generated main file manually if browser checks are unavailable"],
        "auto_apply_allowed": False,
    }
