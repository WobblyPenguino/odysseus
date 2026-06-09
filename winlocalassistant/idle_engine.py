from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .safe_io import atomic_write_json, append_jsonl, read_json_file

logger = logging.getLogger(__name__)


@dataclass
class IdleEvidence:
    source: str
    summary: str
    path: str | None = None
    line: int | None = None
    severity: str = "info"


@dataclass
class IdleCandidate:
    id: str
    title: str
    category: str
    evidence: list[IdleEvidence]
    target_files: list[str]
    value_score: float = 0.0
    risk_score: float = 0.0
    confidence_score: float = 0.0
    final_score: float = 0.0
    allowed_to_auto_apply: bool = False
    blocked_reason: str | None = None
    reason_selected: str = ""


@dataclass
class IdleStrategyState:
    recent_candidate_ids: list[str] = field(default_factory=list)
    file_cooldowns: dict[str, int] = field(default_factory=dict)
    failed_categories: dict[str, int] = field(default_factory=dict)
    successful_categories: dict[str, int] = field(default_factory=dict)
    last_failure_reason: str | None = None
    last_successful_candidate: str | None = None


@dataclass
class IdleCycleReport:
    run_id: str
    timestamp: str
    selected_candidate: IdleCandidate | None
    rejected_candidates: list[IdleCandidate]
    no_safe_candidate: bool
    status: str
    verification_commands: list[str]
    markdown_report_path: str | None = None
    json_report_path: str | None = None


EVIDENCE_FILES = [
    "IDLE_LESSONS.md",
    "ERROR_INVESTIGATION.md",
    "KNOWN_ISSUES.md",
    "IMPROVEMENT_PROPOSALS.md",
    "SELF_IMPROVEMENT_QUEUE.md",
    "IDLE_ANALYSIS.md",
]

HIGH_RISK_PATH_TERMS = [
    "security.py",
    "tools.py",
    "core.py",
    "internet",
    "network",
    "install",
    "update",
    "package",
    "self_improve",
    "self-improve",
    "backup",
    "rollback",
    "permission",
    "safety",
]

LOW_RISK_PATH_TERMS = [
    "docs/",
    "tests",
    ".md",
    "report",
    "logging",
]

AUTO_APPLY_ELIGIBLE_CATEGORIES = {"tests", "logging", "report", "docs"}


def default_verification_commands() -> list[str]:
    return [
        "python -W error::SyntaxWarning -m py_compile app.py winlocalassistant/*.py tests_smoke.py",
        "python tests_smoke.py",
        "python -m pytest tests_smoke.py",
        "python -m pytest tests_cli_user_mode.py",
    ]


def make_candidate_id(title: str, target_files: list[str]) -> str:
    normalized_title = (title or "candidate").strip().lower()
    normalized_files = sorted(_normalize_path_key(path) for path in target_files)
    seed = normalized_title + "|" + "|".join(normalized_files)
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:10]
    title_part = _slug(normalized_title, limit=36)
    files_part = _slug(" ".join(normalized_files), limit=28) or "no-target"
    return f"{title_part}-{files_part}-{digest}"


def classify_path_risk(path: str) -> tuple[float, str | None]:
    normalized = _normalize_path_key(path)
    for term in HIGH_RISK_PATH_TERMS:
        if term in normalized:
            return 0.95, f"High-risk path contains '{term}'."
    for term in LOW_RISK_PATH_TERMS:
        if term in normalized:
            return 0.20, None
    return 0.50, None


def collect_idle_candidates(profile_dir: Path, repo_root: Path) -> list[IdleCandidate]:
    del repo_root  # Kept for future repo-aware target selection without side effects.
    evidence_by_category: dict[str, list[IdleEvidence]] = {
        "error-investigation": [],
        "tests": [],
        "report": [],
        "self-improve-review": [],
    }
    any_evidence_file = False

    for name in EVIDENCE_FILES:
        path = profile_dir / name
        if not path.exists() or not path.is_file():
            continue
        any_evidence_file = True
        text = _safe_read_tail(path)
        low = text.lower()
        if _contains_any(low, ["traceback", "exception", "failed", "error", "crash"]):
            evidence_by_category["error-investigation"].append(
                _evidence_for(path, text, ["traceback", "exception", "failed", "error", "crash"], "warning")
            )
        if _contains_any(low, ["test", "smoke", "pytest", "coverage", "verification"]):
            evidence_by_category["tests"].append(
                _evidence_for(path, text, ["test", "smoke", "pytest", "coverage", "verification"], "info")
            )
        if _contains_any(low, ["log", "report", "diagnostic", "jsonl", "event"]):
            evidence_by_category["report"].append(
                _evidence_for(path, text, ["log", "report", "diagnostic", "jsonl", "event"], "info")
            )
        if _contains_any(low, ["self-improve", "self_improve"]):
            evidence_by_category["self-improve-review"].append(
                _evidence_for(path, text, ["self-improve", "self_improve"], "warning")
            )

    candidates: list[IdleCandidate] = []
    specs = {
        "error-investigation": (
            "Investigate recurring idle errors",
            ["winlocalassistant/core.py", "winlocalassistant/tools.py"],
            0.90,
            0.75,
        ),
        "tests": (
            "Strengthen idle verification tests",
            ["tests_smoke.py", "tests_cli_user_mode.py"],
            0.75,
            0.85,
        ),
        "report": (
            "Improve idle report quality",
            ["docs/IDLE_REPORTS.md"],
            0.55,
            0.80,
        ),
        "self-improve-review": (
            "Review self-improvement proposals safely",
            ["winlocalassistant/core.py", "winlocalassistant/tools.py"],
            0.65,
            0.60,
        ),
    }

    for category, evidence in evidence_by_category.items():
        if not evidence:
            continue
        title, target_files, value, confidence = specs[category]
        risk_score, risk_reason = _max_path_risk(target_files)
        blocked_reason = risk_reason if risk_score >= 0.70 else None
        if category == "self-improve-review":
            risk_score = max(risk_score, 0.95)
            blocked_reason = blocked_reason or "Self-improvement review is high-risk and proposal-only."
        candidates.append(
            IdleCandidate(
                id=make_candidate_id(title, target_files),
                title=title,
                category=category,
                evidence=evidence,
                target_files=target_files,
                value_score=value,
                risk_score=risk_score,
                confidence_score=confidence,
                allowed_to_auto_apply=category in AUTO_APPLY_ELIGIBLE_CATEGORIES and risk_score <= 0.20 and blocked_reason is None,
                blocked_reason=blocked_reason,
            )
        )

    if not any_evidence_file or not candidates:
        return [_noop_candidate()]
    return candidates


def score_candidate(candidate: IdleCandidate, state: IdleStrategyState | None) -> IdleCandidate:
    state = state or IdleStrategyState()
    risk_score, risk_reason = _max_path_risk(candidate.target_files)
    risk_score = max(float(candidate.risk_score or 0.0), risk_score)
    value_score = float(candidate.value_score or 0.0)
    confidence_score = float(candidate.confidence_score or 0.0)
    final_score = (value_score * 0.50) + (confidence_score * 0.35) - (risk_score * 0.65)

    recent_count = _recent_count(state, candidate.id)
    if recent_count:
        final_score -= 0.25 * min(recent_count, 3)
    if recent_count >= 2:
        final_score -= 0.35

    cooldowns = {_normalize_path_key(k): int(v) for k, v in state.file_cooldowns.items()}
    for target_file in candidate.target_files:
        if cooldowns.get(_normalize_path_key(target_file), 0) > 0:
            final_score -= 0.15

    if int(state.failed_categories.get(candidate.category, 0)) >= 2:
        final_score -= 0.10

    blocked_reason = candidate.blocked_reason
    if risk_score >= 0.70:
        blocked_reason = blocked_reason or risk_reason or f"Risk score {risk_score:.2f} is too high for auto-apply."

    eligible_for_auto_apply = (
        risk_score <= 0.20
        and candidate.category in AUTO_APPLY_ELIGIBLE_CATEGORIES
        and blocked_reason is None
    )
    allowed_to_auto_apply = bool(eligible_for_auto_apply)
    if not eligible_for_auto_apply:
        allowed_to_auto_apply = False

    reason_selected = (
        f"value={value_score:.2f}, confidence={confidence_score:.2f}, risk={risk_score:.2f}, "
        f"repeat={recent_count}, final={final_score:.3f}"
    )
    return replace(
        candidate,
        value_score=value_score,
        risk_score=risk_score,
        confidence_score=confidence_score,
        final_score=final_score,
        allowed_to_auto_apply=allowed_to_auto_apply,
        blocked_reason=blocked_reason,
        reason_selected=reason_selected,
    )


def select_candidate(candidates: list[IdleCandidate], state: IdleStrategyState | None) -> IdleCycleReport:
    state = state or IdleStrategyState()
    scored = [score_candidate(candidate, state) for candidate in candidates]
    sorted_candidates = sorted(scored, key=lambda item: (-item.final_score, item.id))
    safe_candidates = [
        candidate
        for candidate in sorted_candidates
        if candidate.risk_score < 0.70 and candidate.category != "noop"
    ]
    fresh_candidates = [
        candidate
        for candidate in safe_candidates
        if _recent_count(state, candidate.id) < 2
    ]
    selected = fresh_candidates[0] if fresh_candidates else (safe_candidates[0] if safe_candidates else None)
    selected_id = selected.id if selected else ""
    rejected = [candidate for candidate in sorted_candidates if candidate.id != selected_id]
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return IdleCycleReport(
        run_id="idle-decision-" + timestamp.replace(":", "").replace("+", "Z"),
        timestamp=timestamp,
        selected_candidate=selected,
        rejected_candidates=rejected,
        no_safe_candidate=selected is None,
        status="proposal-only" if selected else "no-safe-candidate",
        verification_commands=default_verification_commands(),
    )


def _recent_count(state: IdleStrategyState | None, candidate_id: str) -> int:
    if not state or not candidate_id:
        return 0
    return sum(1 for recent_id in state.recent_candidate_ids if recent_id == candidate_id)


def load_strategy_state(path: Path) -> IdleStrategyState:
    try:
        if not path.exists() or not path.is_file():
            return IdleStrategyState()
        data = read_json_file(path, {}, expected_type=dict, quarantine=True)
        if not isinstance(data, dict):
            return IdleStrategyState()
        return IdleStrategyState(
            recent_candidate_ids=_string_list(data.get("recent_candidate_ids")),
            file_cooldowns=_int_dict(data.get("file_cooldowns")),
            failed_categories=_int_dict(data.get("failed_categories")),
            successful_categories=_int_dict(data.get("successful_categories")),
            last_failure_reason=_optional_string(data.get("last_failure_reason")),
            last_successful_candidate=_optional_string(data.get("last_successful_candidate")),
        )
    except Exception as exc:
        logger.warning("Failed to load idle strategy state from %s: %s", path, exc)
        return IdleStrategyState()


def save_strategy_state(path: Path, state: IdleStrategyState) -> None:
    if _looks_like_repo_source_path(path):
        raise ValueError(f"Refusing to save idle strategy state to source path: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(path, asdict(state), ensure_ascii=True)


def append_idle_event(profile_dir: Path, event: dict) -> Path:
    path = profile_dir / "idle_logs" / "idle_events.jsonl"
    safe_event = _sanitize_idle_event(event)
    if "timestamp" not in safe_event:
        safe_event["timestamp"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    append_jsonl(path, safe_event, ensure_ascii=False)
    return path


def update_strategy_state_after_report(state: IdleStrategyState, report: IdleCycleReport) -> IdleStrategyState:
    cooldowns = {
        _normalize_path_key(path): int(value) - 1
        for path, value in state.file_cooldowns.items()
        if int(value) - 1 > 0
    }
    recent_ids = list(state.recent_candidate_ids)
    failed_categories = dict(state.failed_categories)
    successful_categories = dict(state.successful_categories)
    last_failure_reason = state.last_failure_reason
    last_successful_candidate = state.last_successful_candidate
    selected = report.selected_candidate

    if selected is not None:
        recent_ids.append(selected.id)
        recent_ids = recent_ids[-10:]
        for target_file in selected.target_files:
            cooldowns[_normalize_path_key(target_file)] = 3
        status = report.status.lower()
        if "failed" in status:
            failed_categories[selected.category] = failed_categories.get(selected.category, 0) + 1
            last_failure_reason = report.status
        if "success" in status:
            successful_categories[selected.category] = successful_categories.get(selected.category, 0) + 1
            last_successful_candidate = selected.id

    return IdleStrategyState(
        recent_candidate_ids=recent_ids,
        file_cooldowns=cooldowns,
        failed_categories=failed_categories,
        successful_categories=successful_categories,
        last_failure_reason=last_failure_reason,
        last_successful_candidate=last_successful_candidate,
    )


def _noop_candidate() -> IdleCandidate:
    title = "No safe idle improvement found"
    return IdleCandidate(
        id=make_candidate_id(title, []),
        title=title,
        category="noop",
        evidence=[],
        target_files=[],
        value_score=0.0,
        risk_score=0.0,
        confidence_score=1.0,
        allowed_to_auto_apply=False,
        blocked_reason="No useful idle evidence was found.",
    )


def _max_path_risk(paths: list[str]) -> tuple[float, str | None]:
    highest = 0.0
    reason: str | None = None
    for path in paths:
        risk, path_reason = classify_path_risk(path)
        if risk > highest:
            highest = risk
            reason = path_reason
    return highest, reason


def _contains_any(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)


def _evidence_for(path: Path, text: str, terms: list[str], severity: str) -> IdleEvidence:
    line_no, line = _first_matching_line(text, terms)
    summary = line or f"{path.name} contains idle evidence."
    return IdleEvidence(
        source=path.name,
        summary=summary[:300],
        path=str(path),
        line=line_no,
        severity=severity,
    )


def _first_matching_line(text: str, terms: list[str]) -> tuple[int | None, str]:
    for idx, line in enumerate(text.splitlines(), start=1):
        low = line.lower()
        if any(term in low for term in terms):
            return idx, line.strip()
    return None, ""


def _safe_read_tail(path: Path, max_chars: int = 200_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[-max_chars:]
    except Exception:
        return ""


def _slug(text: str, limit: int) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return (slug or "candidate")[:limit].strip("-")


def _normalize_path_key(path: str) -> str:
    return str(path or "").replace("\\", "/").lower().strip()


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item is not None]


def _int_dict(value: object) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    out: dict[str, int] = {}
    for key, item in value.items():
        try:
            out[str(key)] = int(item)
        except Exception:
            continue
    return out


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _sanitize_idle_event(event: object) -> dict[str, Any]:
    if not isinstance(event, dict):
        return {"event": str(event)}
    return {str(key): _sanitize_idle_event_value(str(key), value) for key, value in event.items()}


def _sanitize_idle_event_value(key: str, value: object) -> Any:
    lowered = key.lower()
    if any(term in lowered for term in ["secret", "api_key", "apikey", "token", "password", "prompt", "diff", "source", "content"]):
        return "[redacted]"
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _sanitize_idle_event_value(str(k), v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize_idle_event_value(key, item) for item in value[:50]]
    if isinstance(value, tuple):
        return [_sanitize_idle_event_value(key, item) for item in value[:50]]
    if isinstance(value, (str, int, float, bool)) or value is None:
        if isinstance(value, str) and len(value) > 1000:
            return value[:1000] + "...[truncated]"
        return value
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def _looks_like_repo_source_path(path: Path) -> bool:
    source_names = {"app.py", "tests_smoke.py", "tests_cli_user_mode.py"}
    if path.suffix.lower() != ".py":
        return False
    try:
        resolved = path.resolve()
    except Exception:
        resolved = path
    if any(part.lower() == "winlocalassistant" for part in resolved.parts):
        return True
    return resolved.name.lower() in source_names


__all__ = [
    "IdleEvidence",
    "IdleCandidate",
    "IdleStrategyState",
    "IdleCycleReport",
    "default_verification_commands",
    "make_candidate_id",
    "classify_path_risk",
    "collect_idle_candidates",
    "score_candidate",
    "select_candidate",
    "append_idle_event",
    "load_strategy_state",
    "save_strategy_state",
    "update_strategy_state_after_report",
]
