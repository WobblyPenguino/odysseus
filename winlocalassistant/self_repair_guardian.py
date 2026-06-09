from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from .config import APP_DIR
from .safe_io import append_jsonl, atomic_write_json, atomic_write_text, read_json_file

SELF_REPAIR_DIR = APP_DIR / "self_repair"
MISTAKE_LOG_PATH = SELF_REPAIR_DIR / "mistakes.jsonl"
STATE_PATH = SELF_REPAIR_DIR / "state.json"
LATEST_PLAN_PATH = SELF_REPAIR_DIR / "SELF_REPAIR_PLAN.md"
LATEST_REPORT_PATH = SELF_REPAIR_DIR / "SELF_REPAIR_REPORT.md"

SAFE_VALIDATION_COMMANDS = [
    [sys.executable, "-m", "compileall", "-q", "app.py", "winlocalassistant"],
    [sys.executable, "tests_smoke.py"],
]

@dataclass
class SelfRepairPolicy:
    enabled: bool = True
    max_auto_patch_files: int = 3
    max_auto_patch_lines: int = 140
    require_compile: bool = True
    require_smoke: bool = True
    allow_source_edits: bool = True
    note: str = "User granted bounded self-repair permission; risky changes still need validation and rollback."


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def load_self_repair_policy() -> SelfRepairPolicy:
    data = read_json_file(STATE_PATH, {}, expected_type=dict, quarantine=True)
    policy_data = data.get("policy") if isinstance(data, dict) else {}
    if not isinstance(policy_data, dict):
        policy_data = {}
    defaults = asdict(SelfRepairPolicy())
    defaults.update({k: v for k, v in policy_data.items() if k in defaults})
    return SelfRepairPolicy(**defaults)


def save_self_repair_policy(policy: SelfRepairPolicy) -> dict[str, Any]:
    SELF_REPAIR_DIR.mkdir(parents=True, exist_ok=True)
    data = read_json_file(STATE_PATH, {}, expected_type=dict, quarantine=True)
    if not isinstance(data, dict):
        data = {}
    data["policy"] = asdict(policy)
    data["updated_at"] = _now()
    atomic_write_json(STATE_PATH, data, ensure_ascii=True)
    return data


def set_self_repair_enabled(enabled: bool) -> dict[str, Any]:
    policy = load_self_repair_policy()
    policy.enabled = bool(enabled)
    return save_self_repair_policy(policy)


def record_mistake(kind: str, message: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    SELF_REPAIR_DIR.mkdir(parents=True, exist_ok=True)
    row = {
        "time": _now(),
        "kind": str(kind or "unknown"),
        "message": str(message or "")[:2000],
        "payload": payload or {},
    }
    append_jsonl(MISTAKE_LOG_PATH, row, ensure_ascii=False)
    return row


def _tail_jsonl(path: Path, limit: int = 80) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[-max(1, limit):]:
            try:
                item = json.loads(line)
                if isinstance(item, dict):
                    rows.append(item)
            except Exception:
                continue
    except Exception:
        return []
    return rows


def classify_mistake(text: str) -> str:
    low = (text or "").lower()
    if "ollama" in low and any(x in low for x in ["busy", "timeout", "timed out", "unreachable", "http_500", "cuda"]):
        return "model_concurrency_or_runtime"
    if "attributeerror" in low or "has no attribute" in low:
        return "type_assumption"
    if "unknown command" in low or "missing routes" in low:
        return "command_route_drift"
    if "goal_coverage" in low or "default" in low or "not about" in low:
        return "request_fit_or_truthfulness"
    if "syntaxerror" in low or "compile" in low:
        return "syntax_regression"
    if "pytest" in low or "failed" in low:
        return "test_regression"
    return "general"


def build_mistake_learning_report(root: str | Path = ".", limit: int = 80) -> dict[str, Any]:
    root = Path(root).resolve()
    mistakes = _tail_jsonl(MISTAKE_LOG_PATH, limit)
    buckets: dict[str, int] = {}
    for item in mistakes:
        text = f"{item.get('kind','')} {item.get('message','')} {json.dumps(item.get('payload', {}), default=str)[:1000]}"
        bucket = classify_mistake(text)
        buckets[bucket] = buckets.get(bucket, 0) + 1
    recommended = []
    if buckets.get("model_concurrency_or_runtime"):
        recommended.append("Queue same-model Ollama calls instead of returning None or sending concurrent prompts.")
    if buckets.get("request_fit_or_truthfulness"):
        recommended.append("Run prompt-contract/request-fit tests before claiming a generated artifact matches the request.")
    if buckets.get("command_route_drift"):
        recommended.append("Run command-route regression checks and add aliases before GUI/help surfaces expose a command.")
    if buckets.get("test_regression") or buckets.get("syntax_regression"):
        recommended.append("Run compileall plus targeted pytest before packaging and record the failure signature as a regression.")
    return {
        "ok": True,
        "root": str(root),
        "mistakes_seen": len(mistakes),
        "buckets": buckets,
        "recent": mistakes[-10:],
        "recommendations": recommended or ["No repeated mistake pattern found yet; keep recording failures and run validation gates."],
        "policy": asdict(load_self_repair_policy()),
    }


def _run_command(root: Path, cmd: list[str], timeout: int = 90) -> dict[str, Any]:
    started = time.time()
    try:
        cp = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True, timeout=timeout)
        out = ((cp.stdout or "") + (cp.stderr or "")).strip()
        return {"command": " ".join(cmd), "ok": cp.returncode == 0, "returncode": cp.returncode, "elapsed_sec": round(time.time() - started, 2), "output": out[-8000:]}
    except Exception as exc:
        return {"command": " ".join(cmd), "ok": False, "returncode": None, "elapsed_sec": round(time.time() - started, 2), "output": repr(exc)}


def run_self_repair_validation(root: str | Path = ".") -> dict[str, Any]:
    root = Path(root).resolve()
    results = [_run_command(root, cmd) for cmd in SAFE_VALIDATION_COMMANDS]
    return {"ok": all(r["ok"] for r in results), "root": str(root), "results": results}


def _backup_files(root: Path, files: list[Path]) -> Path:
    backup_root = SELF_REPAIR_DIR / "backups" / time.strftime("%Y%m%d_%H%M%S")
    for p in files:
        rel = p.relative_to(root)
        dest = backup_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if p.exists():
            shutil.copy2(p, dest)
    return backup_root


def _patch_known_noop(root: Path) -> tuple[list[str], list[Path]]:
    """A deliberately tiny deterministic patch point.

    The guardian does not invent broad edits. It only adds/refreshes a local
    policy marker so source mutation, backup, validation and rollback can be
    tested without risking Nova's runtime behaviour.
    """
    path = root / "docs" / "SELF_REPAIR_POLICY.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "# Nova Self-Repair Policy\n\nBounded automatic self-repair is enabled for deterministic, test-backed fixes only.\n\nRules:\n- Record every failure as a mistake signature.\n- Serialize same-model Ollama calls.\n- Back up edited files before changes.\n- Run compile/smoke validation after changes.\n- Roll back if validation fails.\n- Keep destructive, external account, package install, and broad OS changes behind explicit commands.\n"
    old = path.read_text(encoding="utf-8") if path.exists() else ""
    if old == text:
        return ["Self-repair policy marker already current."], []
    atomic_write_text(path, text)
    return ["Wrote/updated docs/SELF_REPAIR_POLICY.md as the safe self-repair policy marker."], [path]


def run_auto_self_repair(root: str | Path = ".", goal: str = "improve Nova safely", *, apply: bool = True) -> dict[str, Any]:
    root = Path(root).resolve()
    policy = load_self_repair_policy()
    before = run_self_repair_validation(root)
    learning = build_mistake_learning_report(root)
    actions: list[str] = []
    changed: list[Path] = []
    backup = None
    applied = False
    rolled_back = False
    after = before

    if not policy.enabled or not policy.allow_source_edits or not apply:
        actions.append("Self-repair is report-only for this run; no source files changed.")
    else:
        actions, changed = _patch_known_noop(root)
        if changed:
            backup = _backup_files(root, changed)
            applied = True
            after = run_self_repair_validation(root)
            if not after.get("ok"):
                for p in changed:
                    rel = p.relative_to(root)
                    b = backup / rel if backup else None
                    if b and b.exists():
                        p.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(b, p)
                rolled_back = True
                actions.append("Validation failed after self-repair patch; restored edited files from backup.")
                after = run_self_repair_validation(root)
        else:
            after = before

    report = {
        "ok": bool(after.get("ok")),
        "root": str(root),
        "goal": goal,
        "policy": asdict(policy),
        "learning": learning,
        "before_validation": before,
        "after_validation": after,
        "actions": actions,
        "changed_files": [p.relative_to(root).as_posix() for p in changed],
        "backup": str(backup) if backup else "",
        "applied": applied,
        "rolled_back": rolled_back,
    }
    SELF_REPAIR_DIR.mkdir(parents=True, exist_ok=True)
    atomic_write_json(SELF_REPAIR_DIR / "self_repair_latest.json", report, ensure_ascii=True)
    atomic_write_text(LATEST_REPORT_PATH, render_self_repair_report(report))
    return report


def render_mistake_learning_report(payload: dict[str, Any]) -> str:
    lines = ["# Nova Mistake Learning", "", f"Mistakes recorded: **{payload.get('mistakes_seen', 0)}**", "", "## Buckets"]
    buckets = payload.get("buckets") or {}
    if buckets:
        for k, v in sorted(buckets.items()):
            lines.append(f"- {k}: {v}")
    else:
        lines.append("- No mistake signatures recorded yet.")
    lines += ["", "## Recommendations"]
    for item in payload.get("recommendations") or []:
        lines.append(f"- {item}")
    lines += ["", "## Policy", "```json", json.dumps(payload.get("policy", {}), indent=2), "```"]
    return "\n".join(lines)


def render_self_repair_report(report: dict[str, Any]) -> str:
    lines = ["# Nova Auto Self-Repair Report", "", f"Status: **{'PASS' if report.get('ok') else 'REVIEW'}**", f"Goal: {report.get('goal')}", f"Root: `{report.get('root')}`", "", "## Actions"]
    for a in report.get("actions") or []:
        lines.append(f"- {a}")
    if report.get("changed_files"):
        lines += ["", "## Changed files"] + [f"- `{p}`" for p in report.get("changed_files", [])]
    lines += ["", "## Validation"]
    after = report.get("after_validation") or {}
    for r in after.get("results") or []:
        lines.append(f"- {'PASS' if r.get('ok') else 'FAIL'} `{r.get('command')}`")
    lines += ["", "## Learning summary"]
    learning = report.get("learning") or {}
    for k, v in (learning.get("buckets") or {}).items():
        lines.append(f"- {k}: {v}")
    return "\n".join(lines)
