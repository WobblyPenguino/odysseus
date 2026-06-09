from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from .project_type_registry import infer_project_type

LOGGER = logging.getLogger(__name__)


@dataclass
class StrategyDecision:
    goal: str
    status: str
    route: str
    reason: str
    next_actions: list[str]
    stop_conditions: list[str]
    validation_focus: list[str]
    repeated_failure: bool = False
    recommended_template: str = ""
    generated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["generated_at"] = data.get("generated_at") or time.strftime("%Y-%m-%d %H:%M:%S")
        return data


def _norm(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def _attempt_reasons(attempts: list[dict[str, Any]] | None) -> list[str]:
    out: list[str] = []
    for item in attempts or []:
        reason = _norm(item.get("reason") or item.get("status") or item)
        if reason:
            out.append(reason[:300])
    return out


def build_strategy_decision(
    goal: str,
    last_failure: Any = "",
    attempts: list[dict[str, Any]] | None = None,
    changed_files: list[str] | None = None,
    validation_passed: bool | None = None,
) -> dict[str, Any]:
    """Choose the next development strategy from evidence, not vibes.

    This is intentionally deterministic and small. It is used to stop the local
    model from repeating weak generation/refinement loops and to decide whether
    Nova should patch, use a recipe, fall back to a template, or stop honestly.
    """
    low_goal = _norm(goal)
    failure = _norm(last_failure)
    reasons = _attempt_reasons(attempts)
    repeated_failure = bool(reasons) and (len(reasons) != len(set(reasons)) or any(reasons.count(r) >= 2 for r in reasons))
    changed = bool(changed_files)
    recommended_template = infer_project_type(goal or "")

    validation_focus = ["record changed_files", "record validation output", "write action receipt"]
    if "game" in low_goal:
        validation_focus += ["controls", "update loop", "collision/interaction", "score or lives", "restart/game-over", "visible theme"]
    elif any(k in low_goal for k in ["tool", "custom tool", "mcp"]):
        validation_focus += ["tool file exists", "registry refresh", "tool_test", "tool_run example"]
    elif any(k in low_goal for k in ["script", "automation", "cli"]):
        validation_focus += ["entrypoint", "usage instructions", "input/output behaviour", "safe paths"]

    if validation_passed and changed:
        route = "promote_and_receipt"
        status = "ready_to_finish"
        reason = "Changed files exist and validation passed."
        actions = ["write final action receipt", "summarise changed files", "preserve rollback path"]
    elif repeated_failure or "candidate_refine_no_progress" in failure or "same validation" in failure:
        route = "template_or_recipe_fallback"
        status = "loop_risk"
        reason = "The same failure/rejection pattern is repeating, so continuing local-model refinement is low value."
        actions = ["stop asking for the same full candidate", f"use deterministic template baseline if available: {recommended_template}", "apply surgical recipe to only the failing behaviour", "run targeted validation"]
    elif any(k in failure for k in ["game_missing_collision", "missing collision", "collision"]):
        route = "surgical_recipe_first"
        status = "repair_specific_behaviour"
        reason = "A named behavioural check failed; repair that behaviour directly before regenerating."
        actions = ["patch the relevant function/file only", "add collision call inside update loop", "run node --check", "run game sanity validation"]
    elif any(k in failure for k in ["parseable json", "invalid json", "json"]):
        route = "json_repair_then_template"
        status = "model_output_failure"
        reason = "The model response format failed, so repair/extract JSON once then switch to deterministic fallback."
        actions = ["attempt JSON extraction/repair once", "if still invalid, use deterministic template", "do not loop full prompts"]
    elif not changed and any(k in low_goal for k in ["implement", "fix", "apply", "create", "make"]):
        route = "bounded_patch_attempt"
        status = "needs_real_change"
        reason = "The goal is mutating but no changed files are recorded yet."
        actions = ["choose smallest safe file change", "write file or patch", "run targeted validation", "write receipt"]
    else:
        route = "plan_then_patch"
        status = "needs_evidence"
        reason = "No decisive failure pattern yet; create a small acceptance contract then patch."
        actions = ["build acceptance contract", "inspect target files", "patch before regenerate", "validate and record evidence"]

    stop_conditions = [
        "same failure repeats twice without new changed_files",
        "validation cannot be run for the requested target",
        "goal requires permission not granted",
        "no safe patch path is available",
    ]
    return StrategyDecision(
        goal=goal or "general Nova task",
        status=status,
        route=route,
        reason=reason,
        next_actions=actions,
        stop_conditions=stop_conditions,
        validation_focus=list(dict.fromkeys(validation_focus)),
        repeated_failure=repeated_failure,
        recommended_template=recommended_template,
    ).to_dict()


def build_validation_evidence(root: Path, goal: str = "") -> dict[str, Any]:
    root = Path(root)
    files = [p for p in root.rglob("*") if p.is_file() and not any(part.startswith(".") for part in p.relative_to(root).parts)] if root.exists() else []
    text_parts: list[str] = []
    for p in files[:120]:
        if p.suffix.lower() in {".html", ".js", ".css", ".py", ".md", ".json"}:
            try:
                text_parts.append(p.read_text(encoding="utf-8", errors="replace")[:4000])
            except Exception:
                LOGGER.debug("Failed to read validation evidence file %s", p, exc_info=True)
    code = "\n".join(text_parts).lower()
    goal_l = _norm(goal)
    checks: list[dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    add("has_files", bool(files), f"{len(files)} file(s) found")
    add("has_readme_or_manifest", any(p.name.lower() in {"readme.md", "project_manifest.json", "project_manifest.json"} for p in files), "README or manifest present")
    if "game" in goal_l:
        add("game_canvas", "<canvas" in code, "visible canvas marker")
        add("game_controls", any(k in code for k in ["keydown", "keyup", "pointerdown", "mousedown", "addeventlistener"]), "keyboard/pointer/button controls")
        add("game_loop", any(k in code for k in ["requestanimationframe", "setinterval", "function update", "function draw"]), "draw/update loop")
        add("game_collision", any(k in code for k in ["collision", "rectsoverlap", "intersect", "collide"]) and any(k in code for k in ["if (", "if("]), "collision/intersection path")
        add("game_score_or_state", any(k in code for k in ["score", "lives", "gameover", "game over", "level"]), "score/lives/game state")
        add("game_restart", any(k in code for k in ["restart", "reset", "startgame", "play again"]), "restart/reset behaviour")
    if any(k in goal_l for k in ["tool", "custom tool"]):
        add("tool_testable_marker", any(k in code for k in ["def run", "input_schema", "tool_test", "enabled"]), "custom tool run/schema markers")
    failed = [c for c in checks if not c["ok"]]
    return {
        "ok": not failed,
        "root": str(root),
        "goal": goal,
        "file_count": len(files),
        "checks": checks,
        "failed": failed,
        "summary": "validation evidence passed" if not failed else f"{len(failed)} evidence check(s) need attention",
    }


def render_strategy(decision: dict[str, Any]) -> str:
    lines = ["# Iterative Development Strategy", "", f"Goal: {decision.get('goal','')}", f"Status: {decision.get('status','')}", f"Route: {decision.get('route','')}", f"Recommended template: `{decision.get('recommended_template','')}`", "", f"Reason: {decision.get('reason','')}", "", "## Next actions"]
    lines.extend(f"- {x}" for x in decision.get("next_actions", []))
    lines.append("\n## Validation focus")
    lines.extend(f"- {x}" for x in decision.get("validation_focus", []))
    lines.append("\n## Stop conditions")
    lines.extend(f"- {x}" for x in decision.get("stop_conditions", []))
    return "\n".join(lines)


def render_validation_evidence(evidence: dict[str, Any]) -> str:
    lines = ["# Validation Evidence", "", f"Root: {evidence.get('root','')}", f"Goal: {evidence.get('goal','')}", f"Summary: {evidence.get('summary','')}", "", "## Checks"]
    for c in evidence.get("checks", []):
        mark = "PASS" if c.get("ok") else "FAIL"
        lines.append(f"- {mark} {c.get('name')}: {c.get('detail')}")
    return "\n".join(lines)
