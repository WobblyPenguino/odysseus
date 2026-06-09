from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .safe_io import append_jsonl, atomic_write_text, atomic_write_json

APP_STATE = Path.home() / ".winlocalassistant"
STATE_PATH = APP_STATE / "autonomy_idle_intelligence.json"
REPETITION_PATH = APP_STATE / "autonomy_repetition_memory.json"
MISTAKE_LOG_PATH = APP_STATE / "mistake_learning_log.jsonl"
LAST_REPORT_PATH = APP_STATE / "AUTONOMOUS_LAST_DETAILED_REPORT.md"
IDLE_SETTINGS_PATH = APP_STATE / "idle_background_settings.json"

DEFAULT_BACKGROUND_SETTINGS = {
    "idle_background_only": True,
    "idle_summaries": False,
    "idle_silence": True,
    "quiet_window_seconds": 180,
    "heavy_model_calls": "avoid_unless_allowed",
}


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def _read_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default
    return default


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(path, payload)


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    append_jsonl(path, payload, ensure_ascii=False)


def _tail_jsonl(path: Path, limit: int = 80) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]:
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    rows.append(obj)
            except Exception:
                continue
    except Exception:
        return []
    return rows


def load_background_settings() -> dict[str, Any]:
    data = _read_json(IDLE_SETTINGS_PATH, {})
    if not isinstance(data, dict):
        data = {}
    merged = {**DEFAULT_BACKGROUND_SETTINGS, **data}
    _write_json(IDLE_SETTINGS_PATH, merged)
    return merged


def set_background_setting(name: str, value: Any) -> dict[str, Any]:
    data = load_background_settings()
    data[name] = value
    _write_json(IDLE_SETTINGS_PATH, data)
    return data


def _events(limit: int = 160) -> list[dict[str, Any]]:
    return _tail_jsonl(APP_STATE / "activity.jsonl", limit=limit)


def _score_from_events(events: list[dict[str, Any]], mode: str = "autonomous") -> dict[str, Any]:
    text = "\n".join((str(e.get("kind", "")) + " " + str(e.get("message", ""))).lower() for e in events)
    buckets = {
        "evidence_gathered": any(k in text for k in ["investigate", "trace", "known_issues", "activity", "review"]),
        "files_improved": any(k in text for k in ["file_write", "code_write", "patch", "promote", "repair"]),
        "tests_or_validation": any(k in text for k in ["test", "validate", "verification", "release_gate", "mega", "docker"]),
        "regression_learning": any(k in text for k in ["regression", "mistake", "known issue", "lesson"]),
        "user_facing_issue": any(k in text for k in ["gui", "voice", "planning", "browser", "support"]),
        "no_repeat_guard": not repeated_signature(events).get("repeated", False),
    }
    score = sum(14 for ok in buckets.values() if ok) + (16 if buckets["tests_or_validation"] else 0)
    score = min(100, score)
    recommendations = []
    if not buckets["files_improved"] and mode == "autonomous":
        recommendations.append("Autonomous made no file/patch progress; switch to patch queue, deterministic template, or ask for approval.")
    if not buckets["tests_or_validation"]:
        recommendations.append("Add validation evidence before claiming success.")
    if not buckets["regression_learning"]:
        recommendations.append("Record a mistake/regression lesson if a failure or repeated strategy was observed.")
    return {"mode": mode, "score": score, "buckets": buckets, "recommendations": recommendations}


def repeated_signature(events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    events = events if events is not None else _events(120)
    sigs: dict[str, int] = {}
    last = ""
    for e in events:
        msg = str(e.get("message", ""))[:160]
        kind = str(e.get("kind", ""))
        if any(k in (kind + msg).lower() for k in ["rejected", "failed", "blocked", "candidate_refine", "repair"]):
            sig = f"{kind}:{msg}"
            sigs[sig] = sigs.get(sig, 0) + 1
            last = sig
    repeated = [(k, v) for k, v in sigs.items() if v >= 2]
    payload = {
        "checked_at": _now(),
        "repeated": bool(repeated),
        "last_signature": last,
        "repeated_signatures": [{"signature": k, "count": v} for k, v in sorted(repeated, key=lambda x: -x[1])[:8]],
        "rule": "If the same failure/rejection repeats twice, switch strategy instead of retrying the same local-model prompt.",
    }
    _write_json(REPETITION_PATH, payload)
    return payload


def clear_repetition_memory() -> dict[str, Any]:
    payload = {"checked_at": _now(), "repeated": False, "repeated_signatures": [], "cleared": True}
    _write_json(REPETITION_PATH, payload)
    return payload


def build_tool_choice_trace(goal: str = "") -> dict[str, Any]:
    goal_l = (goal or "general autonomous task").lower()
    choices: list[dict[str, Any]] = []
    def add(command: str, why: str, when: str, avoid: str = ""):
        choices.append({"command": command, "why": why, "use_when": when, "avoid_when": avoid})
    if any(k in goal_l for k in ["build", "make", "create", "app", "file"]):
        add("/prompt-contract", "Build tasks need prompt-specific must-have and must-not-have checks first.", "before generating or accepting files")
        add("/candidate-tournament", "Multiple candidates reduce bad single-output local-model drift.", "when output quality matters or the model previously went off course")
        add("/browser-run-test", "Generated web apps need runtime behaviour evidence, not only syntax.", "after files are written")
    if any(k in goal_l for k in ["bug", "fix", "repair", "error", "broken"]):
        add("/trace-errors", "Bug work should start from evidence rather than guessing.", "before repair")
        add("/repair-diagnose", "Classify the failure so repair stays minimal.", "when a project/file exists")
        add("/patch-propose", "Stage changes before touching live source.", "for Nova code changes or medium-risk repairs")
    if any(k in goal_l for k in ["autonomous", "idle", "mission"]):
        add("/mission-dashboard", "Mission state prevents vague repeated cycles.", "at the start and end of autonomous work")
        add("/cycle-score", "Progress scoring shows whether the cycle actually helped.", "after each cycle")
        add("/repetition-guard-status", "Repeated no-op strategies should trigger a strategy switch.", "after failed/rejected steps")
    if not choices:
        add("/trace-status", "General tasks benefit from current evidence before action.", "when the best tool is unclear")
        add("/support-report", "A clean report helps debug or hand off the current state.", "when errors are unclear")
    return {"goal": goal or "general autonomous task", "generated_at": _now(), "choices": choices}


def build_mission_dashboard(goal: str = "") -> dict[str, Any]:
    mission = _read_json(APP_STATE / "mission_state.json", {})
    events = _events(160)
    score = _score_from_events(events, "autonomous")
    repeat = repeated_signature(events)
    tools = build_tool_choice_trace(goal or mission.get("goal", ""))
    status = mission.get("status") or "none"
    next_action = "create mission" if status in {"", "none"} else "run next mission step"
    if repeat.get("repeated"):
        next_action = "switch strategy because repetition guard detected repeated failure signatures"
    payload = {
        "generated_at": _now(),
        "mission": mission or {"status": "none", "goal": goal},
        "progress_score": score,
        "repetition_guard": repeat,
        "tool_choice_trace": tools,
        "next_best_action": next_action,
        "patch_queue_first": True,
        "background_idle_settings": load_background_settings(),
    }
    _write_json(STATE_PATH, payload)
    return payload


def log_mistake(mistake: str, cause: str = "", avoid_next_time: str = "") -> dict[str, Any]:
    payload = {
        "time": _now(),
        "mistake": mistake or "unspecified mistake",
        "cause": cause or "unknown cause",
        "avoid_next_time": avoid_next_time or "switch tool/strategy after repeated failure and add regression memory",
        "test_to_add": "create a regression seed from this lesson",
    }
    _append_jsonl(MISTAKE_LOG_PATH, payload)
    return payload


def load_mistake_log(limit: int = 30) -> dict[str, Any]:
    rows = _tail_jsonl(MISTAKE_LOG_PATH, limit=limit)
    return {"path": str(MISTAKE_LOG_PATH), "count": len(rows), "items": rows}


def mistake_to_regression() -> dict[str, Any]:
    log = load_mistake_log(1)
    item = (log.get("items") or [{}])[-1] if log.get("items") else {}
    seed = {
        "time": _now(),
        "regression": item.get("mistake", "no recent mistake"),
        "expected": item.get("avoid_next_time", "do not repeat the same failed strategy"),
        "protection_status": "seeded",
    }
    _append_jsonl(APP_STATE / "regression_memory.jsonl", seed)
    return seed


def autonomous_last_report() -> dict[str, Any]:
    events = _events(80)
    lines = ["# Autonomous Last Detailed Report", "", f"Generated: {_now()}", "", "## Recent actions"]
    for e in events[-25:]:
        lines.append(f"- `{e.get('time','')}` **{e.get('kind','')}** — {str(e.get('message',''))[:220]}")
    score = _score_from_events(events, "autonomous")
    repeat = repeated_signature(events)
    lines += ["", "## Progress score", f"- Score: **{score['score']}/100**"]
    for k, v in score["buckets"].items():
        lines.append(f"- {k}: {'yes' if v else 'no'}")
    lines += ["", "## Repetition guard", f"- Repeated signatures: {'yes' if repeat.get('repeated') else 'no'}"]
    for r in repeat.get("repeated_signatures", [])[:5]:
        lines.append(f"- {r['count']}× `{r['signature']}`")
    lines += ["", "## Next", f"- {score['recommendations'][0] if score['recommendations'] else 'Continue only if the mission has an unmet success condition.'}"]
    LAST_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(LAST_REPORT_PATH, "\n".join(lines))
    return {"path": str(LAST_REPORT_PATH), "markdown": "\n".join(lines), "score": score, "repetition": repeat}


def render_payload(payload: dict[str, Any], title: str = "Autonomous/Idle Intelligence") -> str:
    if "markdown" in payload:
        return str(payload["markdown"])
    lines = [f"# {title}", "", f"Generated: {payload.get('generated_at') or _now()}"]
    if "mission" in payload:
        mission = payload.get("mission", {})
        lines += ["", "## Mission", f"- Goal: {mission.get('goal','')}", f"- Status: **{mission.get('status','')}**"]
    if "progress_score" in payload:
        score = payload["progress_score"]
        lines += ["", "## Progress score", f"- Score: **{score.get('score')}/100**"]
        for k, v in score.get("buckets", {}).items():
            lines.append(f"- {k}: {'yes' if v else 'no'}")
        if score.get("recommendations"):
            lines += ["", "## Recommendations"] + [f"- {x}" for x in score["recommendations"]]
    if "repetition_guard" in payload:
        rep = payload["repetition_guard"]
        lines += ["", "## Repetition guard", f"- Repeated: **{bool(rep.get('repeated'))}**", f"- Rule: {rep.get('rule','')}"]
        for r in rep.get("repeated_signatures", [])[:8]:
            lines.append(f"- {r.get('count')}× `{r.get('signature')}`")
    if "tool_choice_trace" in payload:
        lines += ["", "## Tool choice trace"]
        for c in payload["tool_choice_trace"].get("choices", []):
            lines += [f"- `{c.get('command')}`", f"  - why: {c.get('why')}", f"  - when: {c.get('use_when')}"]
    if "choices" in payload:
        lines += ["", "## Tool choices"]
        for c in payload.get("choices", []):
            lines += [f"- `{c.get('command')}` — {c.get('why')}"]
    if "items" in payload:
        lines += ["", "## Items"] + [f"- {i.get('time','')}: {i.get('mistake') or i.get('regression') or i}" for i in payload.get("items", [])]
    lines += ["", "```json", json.dumps(payload, indent=2, ensure_ascii=False, default=str)[:12000], "```"]
    return "\n".join(lines)
