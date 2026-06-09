from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .config import APP_DIR
from .safe_io import append_jsonl

WATCHER_LOG_PATH = APP_DIR / "ACTION_WATCHER_LOG.jsonl"


@dataclass
class WatcherDecision:
    allowed: bool
    risk: str
    requires_approval: bool
    status: str
    reasons: list[str] = field(default_factory=list)
    recommended_next_action: str = "proceed"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


LOW_RISK_ACTIONS = {"status", "read", "inspect", "report", "quality_dashboard", "idle_once", "idle_propose"}
MUTATING_WORDS = {"write", "edit", "replace", "delete", "remove", "apply", "self-improve", "self_improve", "install", "network", "shell", "powershell", "cmd"}
PROTECTED_PATH_TERMS = {"winlocalassistant/core.py", "winlocalassistant/tools.py", "security.py", "self_improve", "self-improve", ".env", ".key", ".pem"}


def evaluate_action_risk(action: dict[str, Any] | str, failure_memory: Any | None = None) -> WatcherDecision:
    """Evaluate a proposed Nova action before execution.

    This watcher is intentionally conservative and dependency-free. It is not a
    sandbox; it is a policy gate that can be reused by autonomous planning, GUI
    buttons and future skill execution paths.
    """
    if isinstance(action, str):
        action = {"name": action, "command": action}
    name = str(action.get("name") or action.get("tool") or "action").lower()
    command = str(action.get("command") or action.get("goal") or "").lower()
    target = str(action.get("target") or action.get("path") or "").replace("\\", "/").lower()
    category = str(action.get("category") or "").lower()
    text = "\n".join([name, command, target, category])
    reasons: list[str] = []
    risk = "low"

    if any(term in text for term in PROTECTED_PATH_TERMS):
        risk = "high"
        reasons.append("touches protected Nova/safety path")
    if "/self-improve" in text or "self_improve" in text:
        risk = "high"
        reasons.append("self-improvement requires explicit guarded workflow")
    if any(term in text for term in ["delete", "remove", "rmdir", "del ", "rm "]):
        risk = "high"
        reasons.append("delete/remove action needs explicit review")
    if any(term in text for term in ["pip install", "npm install", "winget", "curl", "invoke-webrequest", "internet", "network"]):
        risk = "medium" if risk == "low" else risk
        reasons.append("package/network action needs approval")
    if any(term in text for term in MUTATING_WORDS) and risk == "low":
        risk = "medium"
        reasons.append("mutating or shell-like action")
    if category in LOW_RISK_ACTIONS and not reasons:
        risk = "low"
        reasons.append("read-only/report/status action")

    signature = str(action.get("signature") or action.get("failure_signature") or "")
    if signature and failure_memory is not None:
        cooldowns = getattr(failure_memory, "cooldowns", {}) if not isinstance(failure_memory, dict) else failure_memory.get("cooldowns", {})
        if cooldowns.get(signature, 0):
            risk = "high"
            reasons.append("same action is on recent-failure cooldown")

    requires = risk in {"medium", "high"}
    allowed = risk != "high"
    status = "allow" if allowed and not requires else "review-required" if allowed else "blocked"
    recommended = "ask_user_approval" if requires and allowed else "stop_or_propose" if not allowed else "proceed"
    return WatcherDecision(allowed, risk, requires, status, reasons or ["no risk signals"], recommended)


def requires_user_approval(action: dict[str, Any] | str) -> bool:
    return evaluate_action_risk(action).requires_approval


def should_block_repeated_action(action: dict[str, Any] | str, failure_memory: Any) -> bool:
    if isinstance(action, str):
        action = {"signature": action}
    return evaluate_action_risk(action, failure_memory).status == "blocked"


def record_action_outcome(action: dict[str, Any] | str, result: dict[str, Any] | str, path: Path = WATCHER_LOG_PATH) -> Path:
    if isinstance(action, str):
        action = {"name": action}
    if isinstance(result, str):
        result = {"summary": result}
    row = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "action": _safe(action),
        "result": _safe(result),
        "decision": evaluate_action_risk(action).to_dict(),
    }
    append_jsonl(path, row, ensure_ascii=False)
    return path


SENSITIVE_KEYS = {"api_key", "apikey", "token", "password", "secret", "authorization", "bearer"}


def _safe(value: Any) -> Any:
    """Return JSON-safe action/result data with likely secrets redacted.

    The watcher log is useful for debugging, but it must not leak API keys or
    auth tokens. Redaction is recursive and handles both sensitive keys and
    obvious token-bearing strings.
    """
    try:
        data = json.loads(json.dumps(value, default=str))
    except Exception:
        data = str(value)
    return _redact(data)


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            key_text = str(key)
            if any(secret in key_text.lower() for secret in SENSITIVE_KEYS):
                out[key_text] = "[redacted]"
            else:
                out[key_text] = _redact(item)
        return out
    if isinstance(value, list):
        return [_redact(item) for item in value]
    if isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in ["bearer ", "api_key=", "token=", "password=", "secret="]):
            return "[redacted]"
        return value
    return value
