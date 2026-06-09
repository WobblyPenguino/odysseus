from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from .safe_io import atomic_write_text, atomic_write_json


@dataclass
class MissionContract:
    goal: str
    target_type: str
    success_conditions: list[str]
    forbidden_success_conditions: list[str]
    max_attempts: int
    fallback_strategy: str
    requires_user_permission: bool = False
    generated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["generated_at"] = data.get("generated_at") or time.strftime("%Y-%m-%d %H:%M:%S")
        return data


def _goal_low(goal: str) -> str:
    return re.sub(r"\s+", " ", (goal or "").strip().lower())


def infer_target_type(goal: str) -> str:
    low = _goal_low(goal)
    if any(k in low for k in ["wla", "codebase", "assistant source", "winlocalassistant", "self improve", "autonomous", "idle"]):
        return "wla_source"
    if any(k in low for k in ["tool", "custom tool", "mcp"]):
        return "tool"
    if any(k in low for k in ["project", "app", "game", "script", "website", "dashboard"]):
        return "project"
    return "general"


def build_mission_contract(goal: str, target_type: str | None = None, max_attempts: int = 3) -> dict[str, Any]:
    low = _goal_low(goal)
    target = target_type or infer_target_type(goal)
    success: list[str] = [
        "goal-specific files or outputs exist",
        "changed files are listed in an action receipt when mutation is requested",
        "verification commands run and their result is recorded",
        "final report states passed, failed, or blocked honestly",
    ]
    forbidden = [
        "heartbeat only",
        "runtime self-check only",
        "proposal only when the user asked to implement",
        "success with no changed files for a mutating goal",
        "success based only on keyword presence without behavioural evidence",
    ]
    fallback = "patch_dont_regenerate_then_surgical_recipe_then_deterministic_template"
    if "game" in low:
        success.extend([
            "project files exist with an entry point",
            "game has controls",
            "game has a loop/update path",
            "game has collision or interaction logic",
            "game has score/progress and restart/game-over behaviour",
            "visible UI theme matches the requested subject",
        ])
    if "tool" in low:
        success.extend([
            "new custom tool file exists",
            "registry refresh lists the tool",
            "tool_test passes",
            "tool_run succeeds with example input",
        ])
    if any(k in low for k in ["fix", "implement", "apply", "improve"]):
        success.extend([
            "at least one concrete improvement is implemented or a clear blocked/no-op receipt is written",
            "regression/continuity checks are run after the change",
        ])
    return MissionContract(
        goal=goal or "general Nova task",
        target_type=target,
        success_conditions=list(dict.fromkeys(success)),
        forbidden_success_conditions=forbidden,
        max_attempts=max(1, int(max_attempts or 3)),
        fallback_strategy=fallback,
        requires_user_permission=any(k in low for k in ["delete", "remove", "install", "system", "self apply"]),
    ).to_dict()


def score_progress(events: list[dict[str, Any]], contract: dict[str, Any] | None = None) -> dict[str, Any]:
    score = 0
    positives: list[str] = []
    negatives: list[str] = []
    kinds = [str(e.get("kind") or "") for e in events]
    messages = "\n".join(str(e.get("message") or "") + " " + json.dumps(e.get("data") or {}, default=str)[:500] for e in events)
    if any(k in kinds for k in ["file_write", "code_edit_write", "known_error_recovery_write"]):
        score += 3; positives.append("files changed")
    if any(k in kinds for k in ["command_done", "docker_validate", "auto_verify", "verification_passed"]):
        score += 2; positives.append("verification ran")
    if any(k in kinds for k in ["regression_add", "mistake_to_regression"]):
        score += 2; positives.append("regression protection added")
    if "candidate_refine_no_progress" in kinds:
        score -= 4; negatives.append("candidate refinement made no progress")
    if len([k for k in kinds if k == "candidate_refine_prompt"]) >= 2:
        score -= 3; negatives.append("repeated candidate-refinement prompts")
    if "cycle_done" in kinds and not any(k in kinds for k in ["file_write", "command_done", "docker_validate", "tool_create"]):
        score -= 5; negatives.append("cycle completed with no measurable action")
    if "heartbeat" in kinds and "runtime_self_check" in messages and not positives:
        score -= 3; negatives.append("heartbeat/runtime check without goal-specific progress")
    status = "progress" if score > 0 else "no_progress" if score == 0 else "regression_or_loop_risk"
    return {"score": score, "status": status, "positives": positives, "negatives": negatives, "event_count": len(events), "contract_goal": (contract or {}).get("goal", "")}


def should_switch_strategy(progress: dict[str, Any], repeated_reason: str = "") -> bool:
    reason = (repeated_reason or "").lower()
    return progress.get("score", 0) <= 0 or "no progress" in reason or "same" in reason or "repeated" in reason


def render_mission_contract(payload: dict[str, Any]) -> str:
    lines = ["# Autonomous Mission Contract", "", f"Goal: {payload.get('goal','')}", f"Target: {payload.get('target_type','')}", f"Max attempts: {payload.get('max_attempts',3)}", f"Fallback: {payload.get('fallback_strategy','')}", "", "## Success conditions"]
    lines.extend(f"- {x}" for x in payload.get("success_conditions", []))
    lines.append("\n## Forbidden success conditions")
    lines.extend(f"- {x}" for x in payload.get("forbidden_success_conditions", []))
    return "\n".join(lines)


def write_contract_report(root: Path, payload: dict[str, Any]) -> Path:
    out = Path(root) / "docs" / "NOVA_MISSION_CONTRACT_LATEST.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(out, payload)
    md = out.with_suffix(".md")
    atomic_write_text(md, render_mission_contract(payload))
    return md
