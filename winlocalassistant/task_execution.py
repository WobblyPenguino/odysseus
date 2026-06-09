from __future__ import annotations

"""Small task-contract, evidence and repeated-failure helpers for Nova.

This module is intentionally lightweight: it does not introduce a new agent
framework.  It gives existing /do, /write, /run, /verify and autonomous release
checks a shared way to describe intent, record evidence and stop blind retries.
"""

import hashlib
import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .project_request_contract import build_request_contract
from .safe_io import atomic_write_json, atomic_write_text

SCHEMA_VERSION = 1
EVIDENCE_DIR = Path("logs") / "task_evidence"
FAILURE_LOG = "repeated_failures.json"


@dataclass
class TaskContract:
    original_request: str
    inferred_intent: str
    target_files_or_folders: list[str] = field(default_factory=list)
    allowed_actions: list[str] = field(default_factory=list)
    forbidden_actions: list[str] = field(default_factory=list)
    expected_outputs: list[str] = field(default_factory=list)
    verification_commands: list[str] = field(default_factory=list)
    risk_level: str = "low"
    package_permission: bool = False
    rollback_notes: str = "No rollback required for read-only task. For edits, keep a backup/diff before replacing files."
    task_plan: list[str] = field(default_factory=list)
    user_review_needed: bool = False
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": SCHEMA_VERSION, **asdict(self)}


@dataclass
class FailureDecision:
    ok_to_run: bool
    repeated: bool
    count: int
    signature: str
    reason: str
    suggested_next_step: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _root(root: str | Path) -> Path:
    return Path(root).expanduser().resolve()


def _low(text: str) -> str:
    return (text or "").strip().lower()


def _has_any(low: str, *words: str) -> bool:
    return any(word in low for word in words)


def infer_task_intent(request: str) -> str:
    low = _low(request)
    if not low:
        return "empty"
    if low.startswith("/verify") or low.startswith("verify ") or "test" in low or "compile" in low:
        return "verify"
    if low.startswith("/write") or _has_any(low, "write a file", "create a file", "one file", "single file") or bool(re.search(r"\bone\s+[a-z0-9_ -]{0,40}\s*file\b", low)):
        return "file_write"
    if low.startswith("/run") or low.startswith("/shell") or _has_any(low, "run this", "run command", "execute"):
        return "command_run"
    if "nova" in low and _has_any(low, "fix", "improve", "patch", "edit", "add a feature", "continue"):
        return "nova_source_edit"
    if _has_any(low, "browser game", "make a game", "build an app", "create a project"):
        return "new_project"
    if is_broad_prompt(request):
        return "broad_maintenance"
    return "general_task"


def is_broad_prompt(request: str) -> bool:
    low = _low(request)
    broad_markers = [
        "fix bugs",
        "improve nova",
        "improve this",
        "make this work",
        "continue where",
        "continue improving",
        "add this feature",
        "finish this",
        "do what's next",
        "do whats next",
    ]
    return any(marker in low for marker in broad_markers)


def decompose_task(request: str) -> list[str]:
    if is_broad_prompt(request):
        return [
            "inspect current files, command routes, recent evidence and failing tests",
            "identify the smallest concrete defect or missing contract",
            "patch only the targeted files needed for that defect",
            "run focused tests/compile checks for the touched area",
            "verify release-readiness or a lighter gate when full validation is not requested",
            "summarize files changed, evidence, failures and review items",
        ]
    intent = infer_task_intent(request)
    if intent == "file_write":
        return ["confirm requested file path/content", "write only the requested file", "read back or syntax-check when possible", "record evidence"]
    if intent == "command_run":
        return ["classify command risk", "run once with timeout", "summarize stdout/stderr", "do not repeat if the same error recurs"]
    if intent == "verify":
        return ["run syntax/targeted verification", "scan output for error markers", "record PASS/REVIEW/FAIL evidence"]
    if intent == "nova_source_edit":
        return ["inspect Nova source area", "patch narrowly", "run targeted tests", "run release-readiness before packaging"]
    return ["inspect request", "choose safe action", "execute minimal step", "verify result", "summarize evidence"]


def build_task_contract(request: str, *, root: str | Path = ".") -> TaskContract:
    text = (request or "").strip()
    low = _low(text)
    intent = infer_task_intent(text)
    generation = build_request_contract(text) if text else {"expected_output_files": [], "target": "none", "verification_command": ""}
    expected = list(generation.get("expected_output_files") or [])
    target_files: list[str] = []
    if generation.get("target") == "nova_source_edit" or intent == "nova_source_edit":
        target_files = ["winlocalassistant/", "app.py", "tests_*.py", "docs/"]
    elif expected:
        target_files = expected
    elif intent == "verify":
        target_files = ["current workspace"]
    verification: list[str] = []
    if generation.get("verification_command"):
        verification.append(str(generation["verification_command"]))
    if intent == "nova_source_edit":
        verification = [
            "python -m compileall -q winlocalassistant app.py scripts",
            "python -m pytest -q <targeted tests>",
            "python -m winlocalassistant.release_readiness --root . --full",
        ]
    elif intent == "broad_maintenance":
        verification = [
            "python -m compileall -q winlocalassistant app.py scripts",
            "python -m pytest -q <focused tests>",
            "python -m winlocalassistant.release_readiness --root . --full if packaging is requested",
        ]
    elif intent == "verify" and text:
        verification = [re.sub(r"^/?verify\s+", "", text, flags=re.I).strip() or "python -m compileall -q winlocalassistant app.py"]
    if not verification:
        verification = ["manual review or targeted syntax/test command required"]

    risk = "low"
    if intent in {"command_run", "nova_source_edit", "broad_maintenance"}:
        risk = "medium"
    if _has_any(low, "delete", "remove files", "format", "install", "network", "token", "secret", "system32", "registry"):
        risk = "high"

    allowed = ["inspect", "plan", "summarize"]
    if intent in {"file_write", "new_project", "nova_source_edit", "broad_maintenance"}:
        allowed.append("edit_files")
    if intent in {"command_run", "verify", "nova_source_edit", "broad_maintenance"}:
        allowed.append("run_safe_commands")
    if "package" in low or "zip" in low or "release" in low:
        allowed.append("package_after_passed_gate")

    forbidden = [
        "delete files without explicit permission",
        "install packages or use network without explicit permission",
        "retry the same failing command blindly",
        "package if release-readiness is FAIL or repeated-failure guard is tripped",
    ]
    if intent in {"broad_maintenance", "nova_source_edit"} or is_broad_prompt(text):
        forbidden.append("create a random new project instead of inspecting the current one")
    if generation.get("must_not_create_scaffold"):
        forbidden.append("create a scaffold when the request asks for one file or a Nova edit")

    return TaskContract(
        original_request=text,
        inferred_intent=intent,
        target_files_or_folders=target_files or ["current workspace"],
        allowed_actions=allowed,
        forbidden_actions=forbidden,
        expected_outputs=expected or (["patched Nova source plus validation evidence"] if intent in {"nova_source_edit", "broad_maintenance"} else ["plain-language result"]),
        verification_commands=verification,
        risk_level=risk,
        package_permission=("package_after_passed_gate" in allowed),
        rollback_notes="Back up touched files or keep a diff before promotion; package only after release-readiness PASS." if intent in {"nova_source_edit", "broad_maintenance", "new_project"} else "No rollback required unless files are edited.",
        task_plan=decompose_task(text),
        user_review_needed=risk != "low" or "manual review" in " ".join(verification).lower(),
        notes=["Broad request decomposed into inspect/identify/patch/test/verify/summarize." if is_broad_prompt(text) else "Task contract generated from request wording."],
    )


def render_task_contract(contract: TaskContract | dict[str, Any]) -> str:
    data = contract.to_dict() if isinstance(contract, TaskContract) else dict(contract)
    lines = [
        "# Nova Task Contract",
        "",
        f"Intent: **{data.get('inferred_intent')}**",
        f"Risk: **{data.get('risk_level')}**",
        f"Package permission: `{data.get('package_permission')}`",
        f"User review needed: `{data.get('user_review_needed')}`",
        "",
        "## Target",
    ]
    for item in data.get("target_files_or_folders") or []:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Allowed actions"])
    lines.extend(f"- {item}" for item in data.get("allowed_actions") or [])
    lines.extend(["", "## Forbidden actions"])
    lines.extend(f"- {item}" for item in data.get("forbidden_actions") or [])
    lines.extend(["", "## Expected outputs"])
    lines.extend(f"- {item}" for item in data.get("expected_outputs") or [])
    lines.extend(["", "## Verification commands"])
    lines.extend(f"- `{item}`" for item in data.get("verification_commands") or [])
    lines.extend(["", "## Task plan"])
    for index, step in enumerate(data.get("task_plan") or [], start=1):
        lines.append(f"{index}. {step}")
    lines.extend(["", "## Rollback notes", str(data.get("rollback_notes") or "")])
    return "\n".join(lines).strip() + "\n"


def evidence_root(root: str | Path) -> Path:
    path = _root(root) / EVIDENCE_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def _short_hash(text: str, n: int = 12) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:n]


def _summarize_output(text: str, limit: int = 1200) -> str:
    clean = (text or "").replace("\x00", "")
    if len(clean) <= limit:
        return clean
    return clean[: limit // 2] + "\n...<snip>...\n" + clean[-limit // 2 :]


def error_signature(command: str, output: str = "", returncode: Any = None) -> str:
    compact = re.sub(r"\s+", " ", (output or "").strip().lower())[-1000:]
    first = compact[:240]
    base = json.dumps({"command": (command or "").strip().lower(), "returncode": returncode, "error": first}, sort_keys=True)
    return _short_hash(base, 16)


def _load_failure_log(root: str | Path) -> dict[str, Any]:
    path = evidence_root(root) / FAILURE_LOG
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {"schema_version": SCHEMA_VERSION, "failures": {}}


def _save_failure_log(root: str | Path, data: dict[str, Any]) -> Path:
    path = evidence_root(root) / FAILURE_LOG
    atomic_write_json(path, data, ensure_ascii=True)
    return path


def repeated_failure_block(root: str | Path, action: str, command: str) -> FailureDecision:
    data = _load_failure_log(root)
    action_key = _short_hash(f"{action}:{(command or '').strip().lower()}", 16)
    entry = (data.get("failures") or {}).get(action_key) or {}
    count = int(entry.get("count") or 0)
    if count >= 2:
        return FailureDecision(
            ok_to_run=False,
            repeated=True,
            count=count,
            signature=action_key,
            reason="The same action has already failed twice with a matching command/error family.",
            suggested_next_step="Stop retrying automatically. Inspect the saved evidence, change the command or fix the first concrete error before running again.",
        )
    return FailureDecision(True, False, count, action_key, "No repeated-failure block is active.", "Run once, then verify the result.")


def record_failure_result(root: str | Path, action: str, command: str, *, ok: bool, output: str = "", returncode: Any = None) -> FailureDecision:
    data = _load_failure_log(root)
    failures = data.setdefault("failures", {})
    action_key = _short_hash(f"{action}:{(command or '').strip().lower()}", 16)
    if ok:
        failures.pop(action_key, None)
        _save_failure_log(root, data)
        return FailureDecision(True, False, 0, action_key, "Successful run cleared matching failure history.", "Continue normally.")
    sig = error_signature(command, output, returncode)
    entry = failures.get(action_key) or {"count": 0}
    last_error = entry.get("error_signature")
    count = int(entry.get("count") or 0)
    count = count + 1 if last_error in {None, sig} else 1
    entry.update({
        "action": action,
        "command": command,
        "count": count,
        "error_signature": sig,
        "output_tail": _summarize_output(output, 800),
        "returncode": returncode,
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "blocked" if count >= 2 else "observed",
    })
    failures[action_key] = entry
    _save_failure_log(root, data)
    if count >= 2:
        return FailureDecision(
            ok_to_run=False,
            repeated=True,
            count=count,
            signature=action_key,
            reason="Repeated failure guard tripped after the same action/error failed twice.",
            suggested_next_step="Do not package. Diagnose the first error, change the command, or apply a targeted fix before retrying.",
        )
    return FailureDecision(True, False, count, action_key, "Failure recorded; one more identical failure will block automatic retry.", "Inspect the output before retrying.")


def record_task_evidence(
    root: str | Path,
    *,
    action: str,
    command: str = "",
    files_changed: list[str] | None = None,
    tests_run: list[str] | None = None,
    result: str = "PASS",
    stdout: str = "",
    stderr: str = "",
    verification_passed: bool | None = None,
    user_review_needed: bool = False,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    folder = evidence_root(root)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    suffix = _short_hash(f"{action}:{command}:{time.time()}", 8)
    stem = f"{stamp}_{re.sub(r'[^a-zA-Z0-9_-]+', '_', action).strip('_') or 'task'}_{suffix}"
    json_path = folder / f"{stem}.json"
    md_path = folder / f"{stem}.md"
    payload = {
        "schema_version": SCHEMA_VERSION,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "command": command,
        "files_changed": files_changed or [],
        # v55.3.168: backwards-compatible aliases/fields so project-state can
        # summarize recent work without knowing every historical evidence shape.
        "changed_files": files_changed or [],
        "tests_run": tests_run or [],
        "verification_commands": tests_run or ([command] if command else []),
        "result": result,
        "status": result,
        "review_status": "REVIEW" if user_review_needed else result,
        "stdout_summary": _summarize_output(stdout),
        "stderr_summary": _summarize_output(stderr),
        "verification_passed": verification_passed,
        "user_review_needed": bool(user_review_needed),
        "repeated_failure_status": (extra or {}).get("repeated_failure_guard") or {},
        "extra": extra or {},
        "json_path": str(json_path),
        "markdown_path": str(md_path),
    }
    atomic_write_json(json_path, payload, ensure_ascii=True)
    lines = [
        "# Nova Task Evidence",
        "",
        f"Action: `{action}`",
        f"Result: **{result}**",
        f"Verification passed: `{verification_passed}`",
        f"User review needed: `{user_review_needed}`",
        f"Command: `{command}`" if command else "Command: `(none)`",
        "",
        "## Files changed",
    ]
    lines.extend(f"- `{item}`" for item in (files_changed or ["none recorded"]))
    lines.extend(["", "## Tests run"])
    lines.extend(f"- `{item}`" for item in (tests_run or ["none recorded"]))
    if stdout:
        lines.extend(["", "## stdout summary", "```text", _summarize_output(stdout), "```"])
    if stderr:
        lines.extend(["", "## stderr summary", "```text", _summarize_output(stderr), "```"])
    atomic_write_text(md_path, "\n".join(lines).strip() + "\n")
    return payload


def latest_task_evidence(root: str | Path, limit: int = 10) -> list[dict[str, Any]]:
    folder = evidence_root(root)
    rows: list[dict[str, Any]] = []
    for path in sorted(folder.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        if path.name == FAILURE_LOG:
            continue
        try:
            rows.append(json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            rows.append({"path": str(path), "ok": False, "error": "could not parse evidence"})
        if len(rows) >= limit:
            break
    return rows


def build_task_execution_status(root: str | Path = ".") -> dict[str, Any]:
    root_path = _root(root)
    folder = evidence_root(root_path)
    failures = _load_failure_log(root_path)
    active_failures = [v for v in (failures.get("failures") or {}).values() if int(v.get("count") or 0) >= 2]
    evidence = latest_task_evidence(root_path, limit=5)
    sample_contract = build_task_contract("improve Nova safely", root=root_path)
    ok = bool(evidence) and not active_failures
    return {
        "schema_version": SCHEMA_VERSION,
        "ok": ok,
        "status": "PASS" if ok else ("FAIL" if active_failures else "REVIEW"),
        "root": str(root_path),
        "evidence_dir": str(folder),
        "evidence_count": len([p for p in folder.glob("*.json") if p.name != FAILURE_LOG]),
        "latest_evidence": evidence,
        "active_repeated_failures": active_failures,
        "sample_contract": sample_contract.to_dict(),
        "summary": "Task execution evidence exists and repeated-failure guard is clear." if ok else "Task execution evidence needs review or repeated-failure guard is tripped.",
    }


def render_task_execution_status(payload: dict[str, Any]) -> str:
    lines = [
        "# Nova Task Execution Status",
        "",
        f"Status: **{payload.get('status')}**",
        f"Summary: {payload.get('summary')}",
        f"Evidence dir: `{payload.get('evidence_dir')}`",
        f"Evidence count: `{payload.get('evidence_count')}`",
        "",
        "## Repeated-failure guard",
    ]
    active = payload.get("active_repeated_failures") or []
    if not active:
        lines.append("- PASS — no active repeated-failure blocks.")
    else:
        for item in active:
            lines.append(f"- FAIL — `{item.get('command')}` failed {item.get('count')} time(s): {item.get('output_tail','')[:180]}")
    lines.extend(["", "## Latest evidence"])
    for ev in payload.get("latest_evidence") or []:
        lines.append(f"- **{ev.get('result')}** `{ev.get('action')}` command=`{ev.get('command')}` review=`{ev.get('user_review_needed')}`")
    return "\n".join(lines).strip() + "\n"


def build_verify_summary(root: str | Path, *, full: bool = False, command: str = "") -> dict[str, Any]:
    status = build_task_execution_status(root)
    return {
        "schema_version": SCHEMA_VERSION,
        "ok": status.get("status") != "FAIL",
        "status": status.get("status"),
        "syntax_compile_status": "not run by summary" if not full else "run through release-readiness when requested",
        "targeted_test_status": "not run by summary" if not command else "see command evidence",
        "release_readiness_status": "not requested" if not full else "run `/release-readiness --full` for authoritative result",
        "changed_files": [],
        "missing_evidence": [] if status.get("evidence_count", 0) else ["No task evidence files found yet."],
        "final_result": status.get("status"),
        "task_execution_status": status,
    }


def render_verify_summary(payload: dict[str, Any]) -> str:
    lines = [
        "# Nova Verify Summary",
        "",
        f"Final result: **{payload.get('final_result')}**",
        f"Syntax/compile status: {payload.get('syntax_compile_status')}",
        f"Targeted test status: {payload.get('targeted_test_status')}",
        f"Release-readiness status: {payload.get('release_readiness_status')}",
        "",
        "## Missing evidence",
    ]
    missing = payload.get("missing_evidence") or []
    lines.extend(f"- {item}" for item in (missing or ["none"] ))
    lines.extend(["", render_task_execution_status(payload.get("task_execution_status") or {})])
    return "\n".join(lines).strip() + "\n"


def autonomous_safety_snapshot(state: dict[str, Any] | None = None, *, allowed_to_edit: bool = False, allowed_to_run: bool = False, allowed_to_package: bool = False, stop_reason: str = "") -> dict[str, Any]:
    state = state or {}
    current_task = state.get("current_task") or state.get("current_action") or "none"
    current_step = state.get("current_step") or state.get("phase") or "idle"
    return {
        "ok": True,
        "current_task": current_task,
        "current_step": current_step,
        "last_successful_step": state.get("last_successful_step") or state.get("last_success") or "none recorded",
        "last_failed_step": state.get("last_failed_step") or state.get("last_failure") or "none recorded",
        "stop_reason": stop_reason or state.get("stop_reason") or "none",
        "allowed_to_edit_files": bool(allowed_to_edit),
        "allowed_to_run_commands": bool(allowed_to_run),
        "allowed_to_package": bool(allowed_to_package),
        "must_stop_conditions": [
            "release-readiness fails",
            "same command/action fails twice with the same error",
            "high-risk edit lacks explicit permission",
            "code change has no verification command",
        ],
    }


def check_task_execution_contract(root: str | Path = ".") -> str:
    root_path = _root(root)
    contract = build_task_contract("continue where it left off and improve Nova", root=root_path)
    assert contract.inferred_intent in {"broad_maintenance", "nova_source_edit"}, contract
    assert "inspect current files, command routes, recent evidence and failing tests" in contract.task_plan, contract.task_plan
    assert any("random new project" in item for item in contract.forbidden_actions), contract.forbidden_actions
    before = repeated_failure_block(root_path, "release-contract-smoke", "python definitely_missing_file.py")
    assert before.ok_to_run is True, before
    record_task_evidence(root_path, action="release_contract_smoke", command="task contract smoke", result="PASS", verification_passed=True)
    status = build_task_execution_status(root_path)
    assert status["evidence_count"] >= 1, status
    snap = autonomous_safety_snapshot({"current_action": "release contract smoke", "phase": "verify"}, allowed_to_edit=True, allowed_to_run=True)
    assert snap["allowed_to_package"] is False, snap
    return "Task contract, decomposition, evidence logging, repeated-failure guard and autonomous safety snapshot contracts passed."
