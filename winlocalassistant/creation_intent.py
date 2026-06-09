from __future__ import annotations

import re
from typing import Any

from .project_acceptance import build_project_acceptance_contract, build_project_repair_plan, evaluate_project_acceptance
from .game_design import analyze_game_request


def analyze_creation_request(user_text: str) -> dict[str, Any]:
    text = (user_text or "").strip()
    low = text.lower()
    words = set(re.findall(r"[a-z][a-z0-9]*", low))
    artifact_type = "unknown"
    likely_files: list[str] = []
    verification_commands: list[str] = []
    assumptions: list[str] = []
    safety_notes: list[str] = []

    requested_theme = _detect_theme(low)
    requested_features = _detect_features(low)
    dodge_fallback_allowed = False

    one_file_requested = any(term in low for term in ["one file", "single file", "just one file", "only one file"]) or bool(re.search(r"\bone\s+[a-z0-9_ -]{0,40}\s*file\b", low))
    if re.search(r"\bnova\b", low) and any(term in low for term in ["add", "fix", "patch", "edit", "modify", "feature", "implement", "improve"]):
        artifact_type = "nova_source_edit"
        likely_files = []
        verification_commands = ["python -m compileall -q winlocalassistant app.py", "python -m pytest -q tests_smoke.py if available"]
        assumptions.append("Request targets the existing Nova codebase; edit Nova instead of creating a new unrelated project.")
    elif one_file_requested and any(term in low for term in ["powershell", ".ps1", "ps1"]):
        artifact_type = "powershell_automation_script"
        likely_files = ["script.ps1"]
        verification_commands = ['powershell -NoProfile -Command "$null = [scriptblock]::Create((Get-Content .\\script.ps1 -Raw)); \'syntax ok\'"']
        assumptions.append("User explicitly requested one file; do not create a scaffold or template.")
    elif any(term in low for term in ["powershell", ".ps1", "ps1"]):
        artifact_type = "powershell_automation_script"
        likely_files = ["script.ps1", "README.md"]
        verification_commands = ['powershell -NoProfile -Command "$null = [scriptblock]::Create((Get-Content .\\script.ps1 -Raw)); \'syntax ok\'"']
    elif one_file_requested and ("script" in words or "python" in words or "py" in words):
        artifact_type = "automation_script"
        likely_files = ["script.py"]
        verification_commands = ["python -m py_compile script.py"]
        assumptions.append("User explicitly requested one file; do not create a scaffold or template.")
    elif any(term in low for term in ["todo", "to-do", "web app", "website", "browser app", "html", "css", "javascript"]):
        artifact_type = "web_app" if "app" in words or "todo" in low else "html_css_js_page"
        likely_files = ["index.html", "style.css", "app.js", "README.md"]
        verification_commands = ["node --check app.js if Node is available", "open index.html in a browser"]
    elif "calculator" in low:
        artifact_type = "html_css_js_page"
        likely_files = ["index.html", "style.css", "app.js", "README.md"]
        verification_commands = ["node --check app.js if Node is available", "manual calculator operation check"]
    elif any(term in low for term in ["file organiser", "file organizer", "organise files", "organize files"]):
        artifact_type = "automation_script"
        likely_files = ["file_organiser.py", "README.md"]
        verification_commands = ["python -m py_compile file_organiser.py", "run against temporary fixture files only"]
        safety_notes.append("Do not touch real user files during verification; use temp fixtures.")
    elif "script" in words or "automation" in words:
        artifact_type = "automation_script"
        likely_files = ["script.py", "README.md"]
        verification_commands = ["python -m py_compile script.py"]
    elif any(term in low for term in ["snake game", "dodge game", "simple game", "game"]):
        game_intent = analyze_game_request(text)
        artifact_type = "html_css_js_page"
        requested_theme = game_intent.requested_game_type or requested_theme
        requested_features = sorted(set(requested_features + list(game_intent.mechanics) + list(game_intent.required_behaviours)))
        likely_files = ["index.html", "style.css", "app.js", "README.md"]
        verification_commands = ["node --check app.js if Node is available", "manual gameplay smoke test against controls/objective/restart"]
        dodge_fallback_allowed = game_intent.requested_game_type == "dodge"
        if game_intent.assumptions:
            assumptions.extend(game_intent.assumptions)
        if game_intent.genre == "generic_browser_game":
            safety_notes.append("Use a custom generic browser-game scaffold; do not silently substitute a fixed Dodge template.")
    elif "document" in words or "readme" in words or "guide" in words:
        artifact_type = "document"
        likely_files = ["README.md"]
        verification_commands = ["review markdown content for requested sections"]
    elif any(term in low for term in ["data", "csv", "json", "viewer", "dashboard"]):
        artifact_type = "data_tool"
        likely_files = ["index.html", "style.css", "app.js", "README.md"]
        verification_commands = ["node --check app.js if Node is available"]
    elif any(term in low for term in ["useful local utility", "useful local app", "useful app", "tiny useful app", "local utility application", "utility application"]):
        artifact_type = "web_app"
        requested_theme = requested_theme or "utility"
        likely_files = ["index.html", "style.css", "app.js", "README.md"]
        verification_commands = ["node --check app.js if Node is available", "manual notes/checklist/export workflow check"]
        assumptions.append("Broad utility request; create a small local browser utility with notes, checklist, local saving and export.")
    elif any(term in low for term in ["gui", "desktop app"]):
        artifact_type = "gui_app"
        likely_files = ["app.py", "README.md"]
        verification_commands = ["python -m py_compile app.py"]
    elif any(term in low for term in ["make", "build", "create", "write", "generate"]):
        if "script" in words or "python" in words or one_file_requested:
            artifact_type = "automation_script"
            likely_files = ["script.py"]
            verification_commands = ["python -m py_compile script.py"]
            assumptions.append("Request is small/script-like; create one focused script instead of a generic HTML project.")
        else:
            artifact_type = "unknown"
            likely_files = []
            verification_commands = []
            assumptions.append("Request is broad; ask/plan instead of silently forcing an HTML template.")

    if any(term in low for term in ["internet", "api", "network", "download live"]):
        safety_notes.append("Network use requires explicit user approval and should not be enabled silently.")
    if any(term in low for term in ["install", "package", "dependency"]):
        safety_notes.append("Package/install changes require explicit user approval.")

    return {
        "artifact_type": artifact_type,
        "requested_theme": requested_theme,
        "requested_features": requested_features,
        "game_design": analyze_game_request(text).to_dict() if "game" in low else None,
        "likely_files": likely_files,
        "verification_commands": verification_commands,
        "assumptions": assumptions,
        "safety_notes": safety_notes,
        "dodge_fallback_allowed": dodge_fallback_allowed,
    }


def validate_created_artifact_matches_request(
    user_text: str,
    created_files: list[str],
    summary: str,
) -> dict[str, Any]:
    analysis = analyze_creation_request(user_text)
    hay = " ".join(created_files + [summary or ""]).lower().replace("\\", "/")
    low = (user_text or "").lower()
    missing: list[str] = []
    unexpected: list[str] = []

    dodge_present = "dodge" in hay or "canvasdodgegame" in hay
    dodge_requested = "dodge" in low
    vague_simple_game = _is_vague_simple_game(low)
    if dodge_present and not (dodge_requested or vague_simple_game):
        unexpected.append("Dodge Game default appeared even though the user did not request a dodge game.")

    artifact_type = analysis.get("artifact_type")
    if artifact_type in {"web_app", "html_css_js_page", "data_tool"}:
        if not any(path.endswith((".html", ".js", ".css")) for path in _lower_files(created_files)):
            missing.append("Expected browser app/page files such as index.html, app.js, or style.css.")
    if artifact_type == "automation_script":
        if not any(path.endswith((".py", ".ps1")) for path in _lower_files(created_files)):
            missing.append("Expected an automation script file.")
        if any(term in hay for term in ["game", "canvas", "dodge"]):
            unexpected.append("Created output looks like a game instead of an automation script.")
    if "calculator" in low and "calculator" not in hay and "calc" not in hay:
        missing.append("Calculator requirement is not visible in created files or summary.")
    if "todo" in low and "todo" not in hay and "to-do" not in hay:
        missing.append("Todo requirement is not visible in created files or summary.")
    if "snake" in low and "snake" not in hay:
        missing.append("Snake game theme is not visible in created files or summary.")

    ok = not missing and not unexpected
    return {
        "matches_request": ok,
        "missing_requirements": missing,
        "unexpected_defaults": unexpected,
        "verification_summary": "Created output appears to match the request." if ok else "Created output does not match the original request.",
        "analysis": analysis,
    }


def _detect_theme(low: str) -> str:
    themes = [
        ("todo", "todo"),
        ("to-do", "todo"),
        ("calculator", "calculator"),
        ("file organiser", "file organiser"),
        ("file organizer", "file organiser"),
    ]
    for needle, theme in themes:
        if needle in low:
            return theme
    if "game" in low:
        return analyze_game_request(low).requested_game_type or "generic browser game"
    return ""


def _detect_features(low: str) -> list[str]:
    features = []
    checks = [
        ("search", ["search"]),
        ("filter", ["filter"]),
        ("export", ["export", "download"]),
        ("local_saving", ["local saving", "localstorage", "save"]),
        ("score", ["score"]),
        ("controls", ["controls", "keyboard", "mouse", "touch"]),
        ("verification", ["test", "verify"]),
    ]
    for label, needles in checks:
        if any(needle in low for needle in needles):
            features.append(label)
    return features


def _lower_files(files: list[str]) -> list[str]:
    return [str(path).lower().replace("\\", "/") for path in files or []]


def _is_vague_simple_game(low: str) -> bool:
    words = set(re.findall(r"[a-z][a-z0-9]*", low or ""))
    if "game" not in words and "games" not in words:
        return False
    return not analyze_game_request(low).explicit_game_type


def project_target_decision(user_text: str, current_project: dict[str, Any] | None = None) -> dict[str, Any]:
    """Decide whether a new creation request should modify current project or create a new one.

    This is intentionally conservative. If the current project clearly has a
    different theme/type from the new request and the user did not explicitly say
    to add it to the current project, Nova should pause and ask instead of
    silently mixing unrelated projects.
    """
    analysis = analyze_creation_request(user_text)
    current_project = current_project or {}
    current_goal = str(current_project.get("goal") or current_project.get("name") or current_project.get("project") or "")
    current_analysis = analyze_creation_request(current_goal) if current_goal else {}
    low = (user_text or "").lower().strip()
    explicit_current = any(term in low for term in ["current project", "this project", "existing project", "add to this", "inside this", "modify this"])
    explicit_new = any(term in low for term in ["new project", "separate project", "fresh project", "from scratch", "new app"])
    if not current_goal:
        return {"decision": "new_project", "reason": "No active project context was supplied.", "analysis": analysis}
    if explicit_current:
        return {"decision": "current_project", "reason": "User explicitly asked to use the current project.", "analysis": analysis, "current_analysis": current_analysis}
    if explicit_new:
        return {"decision": "new_project", "reason": "User explicitly asked for a new/separate project.", "analysis": analysis, "current_analysis": current_analysis}
    new_theme = str(analysis.get("requested_theme") or "")
    old_theme = str(current_analysis.get("requested_theme") or "")
    new_type = str(analysis.get("artifact_type") or "")
    old_type = str(current_analysis.get("artifact_type") or "")
    creation_words = {"make", "build", "create", "generate", "write", "add"}
    action_words = set(re.findall(r"[a-z][a-z0-9]*", low))
    if (new_theme or new_type) and (new_theme != old_theme or new_type != old_type) and action_words & creation_words:
        return {
            "decision": "clarify",
            "reason": "The request appears to create a different artifact than the active project.",
            "question": "Create a new project for this request, or modify the current project?",
            "recommended_commands": [
                "/do create a new project for " + user_text,
                "/continue modify the current project to include " + user_text,
            ],
            "analysis": analysis,
            "current_analysis": current_analysis,
        }
    return {"decision": "current_project", "reason": "Request appears compatible with the current project context.", "analysis": analysis, "current_analysis": current_analysis}


def score_created_project_quality(user_text: str, created_files: list[str], summary: str, checks: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Return a transparent 0-100 quality score for a generated artifact.

    v52.3 combines request matching, file completeness, behavioural keywords,
    verification checks and an explicit acceptance contract. This keeps Nova from
    claiming success for apps/games that merely contain plausible-looking files.
    """
    match = validate_created_artifact_matches_request(user_text, created_files, summary)
    analysis = match.get("analysis") or analyze_creation_request(user_text)
    acceptance = evaluate_project_acceptance(user_text, created_files, summary)
    contract = build_project_acceptance_contract(user_text)
    expected_files = [str(x).lower() for x in analysis.get("likely_files") or contract.expected_files or []]
    have_files = [str(path).lower().replace("\\", "/") for path in created_files or []]
    file_score = 100 if not expected_files else int(100 * sum(1 for f in expected_files if any(path.endswith(f) or f in path for path in have_files)) / max(1, len(expected_files)))
    request_score = 100 if match.get("matches_request") else max(0, 60 - 15 * len(match.get("missing_requirements") or []) - 20 * len(match.get("unexpected_defaults") or []))
    behaviour_score = _behaviour_score_for_request(str(user_text or ""), " ".join(created_files + [summary or ""]).lower().replace("\\", "/"))
    acceptance_score = float(acceptance.get("percent") or 0)
    verification_score = 70
    if checks:
        total = len(checks)
        passed = sum(1 for c in checks if isinstance(c, dict) and c.get("ok"))
        verification_score = int(100 * passed / max(1, total))
    overall = round(request_score * 0.25 + file_score * 0.15 + behaviour_score * 0.25 + acceptance_score * 0.25 + verification_score * 0.10, 1)
    missing: list[str] = []
    if request_score < 100:
        missing.extend(match.get("missing_requirements") or [])
        missing.extend(match.get("unexpected_defaults") or [])
    if behaviour_score < 70:
        missing.append("Behavioural evidence is weak for the requested artifact type.")
    missing.extend(acceptance.get("missing_behaviours") or [])
    passed_threshold = overall >= 80 and bool(match.get("matches_request")) and bool(acceptance.get("passed"))
    return {
        "overall_percent": overall,
        "passed_threshold": passed_threshold,
        "request_match_score": request_score,
        "file_completeness_score": file_score,
        "behaviour_score": behaviour_score,
        "acceptance_contract_score": acceptance_score,
        "verification_score": verification_score,
        "missing_or_weak_items": missing,
        "request_match": match,
        "acceptance_contract": acceptance,
        "repair_plan": build_project_repair_plan(user_text, acceptance),
    }

def _behaviour_score_for_request(user_text: str, hay: str) -> int:
    low = user_text.lower()
    groups: list[list[str]] = []
    if "calculator" in low or "calc" in low:
        groups = [["button", "input", "digit", "number"], ["+", "-", "*", "/", "operator"], ["clear", "backspace", "reset"], ["result", "display", "textcontent", "value"], ["addeventlistener", "onclick", "calculate"]]
    elif "todo" in low or "to-do" in low or "task" in low:
        groups = [["todo", "task"], ["add", "push", "create"], ["delete", "remove", "splice", "filter"], ["complete", "done", "checked", "toggle"], ["render", "appendchild", "createelement", "innerhtml"]]
    elif "game" in low or "snake" in low or "pong" in low:
        groups = [["keydown", "keyup", "addeventlistener", "controls"], ["score", "level", "lives", "progress"], ["collision", "collide", "food", "enemy", "obstacle", "ball"], ["requestanimationframe", "setinterval", "loop", "update", "draw"], ["restart", "reset", "game over", "gameover", "instructions"]]
    else:
        groups = [["readme", "instructions"], ["function", "class", "button", "input", "script"], ["verify", "test", "check"]]
    if not groups:
        return 70
    hits = sum(1 for group in groups if any(token in hay for token in group))
    return int(100 * hits / len(groups))
