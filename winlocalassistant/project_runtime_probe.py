from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .game_design import analyze_game_request


@dataclass
class RuntimeProbeCheck:
    name: str
    ok: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RuntimeProbeResult:
    artifact_type: str
    passed: bool
    percent: float
    checks: list[RuntimeProbeCheck] = field(default_factory=list)
    manual_test_steps: list[str] = field(default_factory=list)
    repair_suggestions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["checks"] = [check.to_dict() for check in self.checks]
        return data


def run_project_runtime_probe(user_text: str, root: Path | None = None, sources: dict[str, str] | None = None) -> dict[str, Any]:
    """Dependency-free interaction probe for generated projects.

    This is not a browser emulator. It checks whether a project has enough actual
    event/state/update evidence to be worth presenting as functional, and returns
    manual test steps the user can run in the browser.
    """
    source_map = dict(sources or {})
    if root is not None:
        source_map.update(_read_project_sources(Path(root)))
    hay = "\n".join(f"\n--- {name} ---\n{text}" for name, text in sorted(source_map.items())).lower()
    code_hay = "\n".join(
        text for name, text in sorted(source_map.items())
        if str(name).lower().endswith((".js", ".html", ".css", ".py", ".java", ".ps1", ".bat"))
    ).lower()
    js_hay = "\n".join(
        text for name, text in sorted(source_map.items())
        if str(name).lower().endswith(".js")
    ).lower()
    user = (user_text or "").lower()
    artifact = _artifact_type(user)
    checks: list[RuntimeProbeCheck] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(RuntimeProbeCheck(name, bool(ok), detail))

    if artifact == "calculator":
        add("number_input_events", _has(hay, "addeventlistener", "onclick", "keydown") and _count_digits(hay) >= 4, "Numbers must be wired to user input.")
        add("operator_state", _has(hay, "operator", "operation", "+", "-", "*", "/") and _has(hay, "current", "previous", "operand", "expression"), "Operators should update calculation state.")
        add("equals_updates_display", _has(hay, "equals", "calculate", "eval", "compute") and _has(hay, "textcontent", "innertext", "value", "display"), "Equals/calculate should update a visible display.")
        add("clear_or_backspace", _has(hay, "clear", "backspace", "delete", "reset"), "Clear/backspace/reset control is required.")
        steps = ["Open index.html.", "Click 7, +, 5, = and confirm 12 appears.", "Use Clear and Backspace/Delete and confirm the display changes."]
    elif artifact == "todo_app":
        add("task_input", _has(hay, "input", "textarea") and _has(hay, "task", "todo"), "Todo app needs a task input.")
        add("add_updates_list", _has(hay, "addeventlistener", "onclick", "submit") and _has(hay, "appendchild", "createelement", "render", "innerhtml"), "Add action should update the visible task list.")
        add("delete_task", _has(hay, "delete", "remove", "splice", "filter"), "Todo items should be removable.")
        add("complete_task", _has(hay, "complete", "done", "checked", "toggle", "classlist"), "Todo items should be completable.")
        steps = ["Open index.html.", "Add a task and confirm it appears.", "Mark it complete, then delete it."]
    elif artifact in {"game", "snake_game"}:
        game = analyze_game_request(user_text)
        add("controls", _has(hay, "keydown", "keyup", "pointer", "touchstart", "controls"), "Game needs player controls.")
        add("loop", _has(hay, "requestanimationframe", "setinterval", "gameloop", "update", "draw"), "Game needs an update/draw loop.")
        add("objective_or_theme", _theme_present(hay, user_text), "Implementation should visibly match the requested game theme/objective.")
        add("score_or_progress", _has(hay, "score", "level", "lives", "progress", "timer"), "Game needs visible score/progress.")
        add("interaction", _has(hay, "collision", "collide", "hit", "food", "enemy", "obstacle", "collect", "target"), "Game needs interaction/collision/collection.")
        add("restart", _has(hay, "restart", "reset", "startgame", "gameover", "game over"), "Game needs restart/end-state handling.")
        if game.genre == "platformer":
            add("platformer_gravity", _has(js_hay, "gravity") and _has(js_hay, "vy", "velocity"), "Platformer needs gravity and vertical velocity in game logic.")
            add("platformer_jump", _has(js_hay, "jump") and _has(js_hay, "onground", "grounded"), "Platformer needs a grounded jump mechanic.")
            add("platformer_platforms", _has(js_hay, "platforms", "platform") and _has(js_hay, "landon", "collision", "rectshit", "overlap"), "Platformer needs actual platforms and landing/collision logic.")
            add("platformer_goal_or_level", _has(code_hay, "goal", "level") and _has(js_hay, "win", "goal"), "Platformer needs a reachable goal or level completion.")
        if game.explicit_game_type:
            for obj in list(game.core_objects[:3]) + list(game.mechanics[:3]):
                token = _main_token(obj)
                if token and token not in {"player", "game", "score"}:
                    add("requested:" + token, token in hay, f"Requested game concept should appear: {token}.")
        steps = ["Open index.html.", "Use the listed controls and confirm the player moves.", "Confirm score/progress changes after interaction.", "Trigger end/restart and confirm it resets."]
    else:
        add("has_entrypoint", any(name.endswith(("index.html", ".py", ".js", ".java", ".ps1", ".bat")) for name in source_map), "Project should have an obvious runnable/openable entrypoint.")
        add("has_instructions", _has(hay, "how to", "run", "open", "instructions", "usage"), "Project should explain how to run or open it.")
        add("has_verification", _has(hay, "verify", "test", "check", "passed"), "Project should include verification notes.")
        steps = ["Open or run the main file listed in the manifest/README.", "Follow the documented usage steps.", "Confirm the output matches the original request."]

    passed_count = sum(1 for check in checks if check.ok)
    total = max(1, len(checks))
    percent = round(100 * passed_count / total, 1)
    # Games are more complex; require a high but not perfect static signal.
    required_percent = 78 if artifact in {"game", "snake_game"} else 80
    result = RuntimeProbeResult(
        artifact_type=artifact,
        passed=percent >= required_percent,
        percent=percent,
        checks=checks,
        manual_test_steps=steps,
        repair_suggestions=[check.detail for check in checks if not check.ok],
    )
    return result.to_dict()


def _read_project_sources(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".html", ".js", ".css", ".py", ".md", ".txt", ".json", ".java", ".ps1", ".bat", ".yaml", ".yml"}:
            continue
        if any(part in {".git", "__pycache__", "node_modules"} for part in path.parts):
            continue
        try:
            rel = path.relative_to(root).as_posix()
            result[rel] = path.read_text(encoding="utf-8", errors="replace")[:12000]
        except Exception:
            continue
    return result


def _artifact_type(text: str) -> str:
    if "calculator" in text or "calc" in text:
        return "calculator"
    if "todo" in text or "to-do" in text or "task" in text:
        return "todo_app"
    if "snake" in text:
        return "snake_game"
    if "game" in text or any(term in text for term in ["pong", "maze", "fishing", "platformer", "racing", "shooter"]):
        return "game"
    return "generic_project"


def _has(text: str, *needles: str) -> bool:
    return any(needle.lower() in text for needle in needles)


def _count_digits(text: str) -> int:
    return len(set(re.findall(r"\b[0-9]\b", text)))


def _main_token(text: str) -> str:
    tokens = [t for t in re.findall(r"[a-z0-9]+", (text or "").lower()) if len(t) > 3]
    return tokens[0] if tokens else ""


def _theme_present(hay: str, user_text: str) -> bool:
    game = analyze_game_request(user_text)
    if not game.explicit_game_type:
        return True
    tokens = [t for t in re.findall(r"[a-z0-9]+", game.requested_game_type.lower()) if len(t) > 3 and t != "game"]
    if not tokens:
        return True
    return any(token in hay for token in tokens)
