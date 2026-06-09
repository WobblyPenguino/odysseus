from __future__ import annotations

import json
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Literal


class NovaState(str, Enum):
    SLEEPING = "sleeping"
    LISTENING = "listening"
    CONFIRMING = "confirming"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    WAITING_FOR_USER = "waiting_for_user"
    IDLE = "idle"
    BLOCKED = "blocked"
    ERROR = "error"


_ALLOWED_TRANSITIONS: dict[NovaState, set[NovaState]] = {
    NovaState.SLEEPING: {NovaState.LISTENING, NovaState.IDLE, NovaState.ERROR},
    NovaState.LISTENING: {NovaState.CONFIRMING, NovaState.PROCESSING, NovaState.IDLE, NovaState.SLEEPING, NovaState.ERROR},
    NovaState.CONFIRMING: {NovaState.PROCESSING, NovaState.WAITING_FOR_USER, NovaState.LISTENING, NovaState.IDLE, NovaState.ERROR},
    NovaState.PROCESSING: {NovaState.SPEAKING, NovaState.WAITING_FOR_USER, NovaState.IDLE, NovaState.BLOCKED, NovaState.ERROR},
    NovaState.SPEAKING: {NovaState.IDLE, NovaState.LISTENING, NovaState.SLEEPING, NovaState.ERROR},
    NovaState.WAITING_FOR_USER: {NovaState.PROCESSING, NovaState.LISTENING, NovaState.IDLE, NovaState.SLEEPING, NovaState.ERROR},
    NovaState.IDLE: {NovaState.LISTENING, NovaState.PROCESSING, NovaState.SLEEPING, NovaState.ERROR},
    NovaState.BLOCKED: {NovaState.WAITING_FOR_USER, NovaState.IDLE, NovaState.ERROR},
    NovaState.ERROR: {NovaState.IDLE, NovaState.SLEEPING, NovaState.PROCESSING},
}

_MICROPHONE_OWNERS = {NovaState.LISTENING, NovaState.CONFIRMING}
_BUSY_STATES = {NovaState.PROCESSING, NovaState.SPEAKING}


@dataclass(slots=True)
class StateTransition:
    ok: bool
    old_state: str
    new_state: str
    reason: str
    illegal_because: str = ""


def normalise_state(value: str | NovaState) -> NovaState:
    if isinstance(value, NovaState):
        return value
    return NovaState(str(value).strip().lower().replace("-", "_"))


def validate_transition(old_state: str | NovaState, new_state: str | NovaState, *, interrupt_enabled: bool = False) -> StateTransition:
    old = normalise_state(old_state)
    new = normalise_state(new_state)
    if old == new:
        return StateTransition(True, old.value, new.value, "state unchanged")
    if old in _BUSY_STATES and new in _MICROPHONE_OWNERS and not interrupt_enabled:
        return StateTransition(
            False,
            old.value,
            new.value,
            "blocked",
            "Nova cannot return to microphone ownership while processing/speaking unless interrupt mode is explicit.",
        )
    allowed = new in _ALLOWED_TRANSITIONS.get(old, set())
    return StateTransition(
        allowed,
        old.value,
        new.value,
        "allowed" if allowed else "blocked",
        "transition is not in Nova's approved state machine" if not allowed else "",
    )


@dataclass(slots=True)
class NovaStateMachine:
    state: NovaState = NovaState.IDLE
    interrupt_enabled: bool = False
    history: list[dict[str, Any]] = field(default_factory=list)

    def transition(self, new_state: str | NovaState, reason: str = "") -> StateTransition:
        result = validate_transition(self.state, new_state, interrupt_enabled=self.interrupt_enabled)
        self.history.append({
            "time": time.time(),
            "old_state": result.old_state,
            "new_state": result.new_state,
            "ok": result.ok,
            "reason": reason or result.reason,
            "illegal_because": result.illegal_because,
        })
        if result.ok:
            self.state = normalise_state(new_state)
        return result


JobStatus = Literal["queued", "running", "blocked", "succeeded", "failed", "cancelled"]


@dataclass(slots=True)
class JobRecord:
    job_id: str
    kind: str
    goal: str
    status: JobStatus = "queued"
    priority: int = 100
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    lease_until: float = 0.0
    attempts: int = 0
    max_attempts: int = 3
    payload_json: str = "{}"
    result_json: str = "{}"

    @property
    def payload(self) -> dict[str, Any]:
        try:
            data = json.loads(self.payload_json or "{}")
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    @property
    def result(self) -> dict[str, Any]:
        try:
            data = json.loads(self.result_json or "{}")
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}


class JobQueue:
    """Small durable SQLite queue for Nova worker orchestration.

    It deliberately stores simple JSON payloads and never executes commands by
    itself. Workers must lease a job, run their own policy checks, and mark the
    result. This prevents duplicate jobs and gives Nova resumability after restarts.
    """

    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    goal TEXT NOT NULL,
                    status TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    lease_until REAL NOT NULL DEFAULT 0,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    max_attempts INTEGER NOT NULL DEFAULT 3,
                    payload_json TEXT NOT NULL DEFAULT '{}',
                    result_json TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status_priority ON jobs(status, priority, created_at)")

    def enqueue(self, kind: str, goal: str, payload: dict[str, Any] | None = None, *, priority: int = 100, job_id: str | None = None, dedupe_key: str | None = None) -> JobRecord:
        if not kind.strip() or not goal.strip():
            raise ValueError("kind and goal are required")
        payload = dict(payload or {})
        if dedupe_key:
            payload.setdefault("dedupe_key", dedupe_key)
            existing = self.find_by_dedupe_key(dedupe_key)
            if existing and existing.status in {"queued", "running", "blocked"}:
                return existing
        now = time.time()
        rec = JobRecord(
            job_id=job_id or str(uuid.uuid4()),
            kind=kind.strip(),
            goal=goal.strip(),
            status="queued",
            priority=int(priority),
            created_at=now,
            updated_at=now,
            payload_json=json.dumps(payload, ensure_ascii=True, sort_keys=True),
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO jobs(job_id, kind, goal, status, priority, created_at, updated_at, lease_until, attempts, max_attempts, payload_json, result_json)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (rec.job_id, rec.kind, rec.goal, rec.status, rec.priority, rec.created_at, rec.updated_at, rec.lease_until, rec.attempts, rec.max_attempts, rec.payload_json, rec.result_json),
            )
        return rec

    def _row_to_record(self, row: sqlite3.Row | None) -> JobRecord | None:
        if row is None:
            return None
        return JobRecord(**{key: row[key] for key in row.keys()})

    def get(self, job_id: str) -> JobRecord | None:
        with self._connect() as conn:
            return self._row_to_record(conn.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone())

    def find_by_dedupe_key(self, dedupe_key: str) -> JobRecord | None:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
        for row in rows:
            rec = self._row_to_record(row)
            if rec and rec.payload.get("dedupe_key") == dedupe_key:
                return rec
        return None

    def list_jobs(self, status: str | None = None, limit: int = 50) -> list[JobRecord]:
        query = "SELECT * FROM jobs"
        params: list[Any] = []
        if status:
            query += " WHERE status=?"
            params.append(status)
        query += " ORDER BY priority ASC, created_at ASC LIMIT ?"
        params.append(max(1, min(int(limit), 500)))
        with self._connect() as conn:
            return [self._row_to_record(row) for row in conn.execute(query, params).fetchall() if row]

    def lease_next(self, worker_id: str, lease_seconds: int = 300) -> JobRecord | None:
        now = time.time()
        lease_until = now + max(1, int(lease_seconds))
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM jobs WHERE status='queued' ORDER BY priority ASC, created_at ASC LIMIT 1"
            ).fetchone()
            if not row:
                return None
            rec = self._row_to_record(row)
            payload = rec.payload if rec else {}
            payload["worker_id"] = worker_id
            conn.execute(
                "UPDATE jobs SET status='running', updated_at=?, lease_until=?, attempts=attempts+1, payload_json=? WHERE job_id=? AND status='queued'",
                (now, lease_until, json.dumps(payload, ensure_ascii=True, sort_keys=True), rec.job_id),
            )
        return self.get(rec.job_id) if rec else None

    def mark(self, job_id: str, status: JobStatus, result: dict[str, Any] | None = None) -> JobRecord | None:
        if status not in {"queued", "running", "blocked", "succeeded", "failed", "cancelled"}:
            raise ValueError(f"unknown job status: {status}")
        with self._connect() as conn:
            conn.execute(
                "UPDATE jobs SET status=?, updated_at=?, result_json=? WHERE job_id=?",
                (status, time.time(), json.dumps(result or {}, ensure_ascii=True, sort_keys=True), job_id),
            )
        return self.get(job_id)

    def cancel(self, job_id: str, reason: str = "cancelled by user") -> JobRecord | None:
        return self.mark(job_id, "cancelled", {"reason": reason})

    def detect_zombies(self, now: float | None = None) -> list[JobRecord]:
        now = time.time() if now is None else float(now)
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM jobs WHERE status='running' AND lease_until > 0 AND lease_until < ?", (now,)).fetchall()
        return [rec for row in rows if (rec := self._row_to_record(row))]

    def summary(self) -> dict[str, Any]:
        with self._connect() as conn:
            counts = {row["status"]: row["count"] for row in conn.execute("SELECT status, COUNT(*) as count FROM jobs GROUP BY status").fetchall()}
        return {"db_path": str(self.db_path), "counts": counts, "zombie_count": len(self.detect_zombies())}


RiskLevel = Literal["read_only", "low", "medium", "high"]
WorkingDirPolicy = Literal["project_only", "sandbox_only", "system"]


@dataclass(slots=True)
class ToolContract:
    name: str
    description: str
    risk_level: RiskLevel = "read_only"
    requires_approval: bool = False
    timeout_seconds: int = 60
    working_dir_policy: WorkingDirPolicy = "project_only"
    validation_command: str | None = None
    dry_run_supported: bool = True

    def validate(self) -> list[str]:
        problems: list[str] = []
        if not self.name or not self.name.replace("_", "").replace("-", "").isalnum():
            problems.append("tool name must be non-empty and command-safe")
        if self.risk_level in {"medium", "high"} and not self.requires_approval:
            problems.append("medium/high risk tools must require approval")
        if self.timeout_seconds <= 0:
            problems.append("timeout_seconds must be positive")
        if self.working_dir_policy == "system" and self.risk_level == "read_only":
            problems.append("system-scope tools should not be labelled read_only")
        return problems


def default_tool_contracts() -> list[ToolContract]:
    return [
        ToolContract("run_project_tests", "Run pytest/compile checks in the current project", risk_level="low", timeout_seconds=600, validation_command="python -m pytest -q"),
        ToolContract("video_plan", "Create a manifest-first video plan without rendering", risk_level="read_only", timeout_seconds=30),
        ToolContract("browser_research", "Read-only browser research with screenshots", risk_level="medium", requires_approval=True, timeout_seconds=180),
        ToolContract("windows_install_profile", "Preview and run safe winget/uv installs", risk_level="high", requires_approval=True, timeout_seconds=900, working_dir_policy="system"),
    ]


def build_integration_foundation_report(runtime_dir: Path | str) -> dict[str, Any]:
    runtime_dir = Path(runtime_dir)
    queue = JobQueue(runtime_dir / "nova_jobs.sqlite3")
    contracts = default_tool_contracts()
    contract_results = [{"contract": asdict(contract), "problems": contract.validate()} for contract in contracts]
    illegal = validate_transition("processing", "listening")
    legal = validate_transition("speaking", "idle")
    summary = queue.summary()
    ok = not any(item["problems"] for item in contract_results) and not illegal.ok and legal.ok
    return {
        "ok": ok,
        "summary": "Nova integration foundation ready" if ok else "Nova integration foundation needs attention",
        "state_machine": {
            "states": [state.value for state in NovaState],
            "illegal_processing_to_listening_without_interrupt": asdict(illegal),
            "legal_speaking_to_idle": asdict(legal),
        },
        "job_queue": summary,
        "tool_contracts": contract_results,
        "next_actions": [
            "Wire GUI state badge to NovaStateMachine.state",
            "Route long-running coding/browser/video tasks through JobQueue leases",
            "Require ToolContract approval for medium/high-risk workers",
        ],
    }


def render_integration_foundation_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Nova Integration Foundation",
        "",
        f"Status: {'PASS' if payload.get('ok') else 'REVIEW'}",
        str(payload.get("summary", "")),
        "",
        "## State machine",
        "- States: " + ", ".join(payload.get("state_machine", {}).get("states", [])),
        "- Processing -> listening without interrupt: " + ("blocked" if not payload.get("state_machine", {}).get("illegal_processing_to_listening_without_interrupt", {}).get("ok") else "allowed"),
        "",
        "## Durable job queue",
        f"- DB: `{payload.get('job_queue', {}).get('db_path', '')}`",
        f"- Counts: `{payload.get('job_queue', {}).get('counts', {})}`",
        f"- Zombies: `{payload.get('job_queue', {}).get('zombie_count', 0)}`",
        "",
        "## Tool contracts",
    ]
    for item in payload.get("tool_contracts", []):
        contract = item.get("contract", {})
        problems = item.get("problems", [])
        lines.append(f"- {'✅' if not problems else '⚠️'} `{contract.get('name')}` risk={contract.get('risk_level')} approval={contract.get('requires_approval')} timeout={contract.get('timeout_seconds')}s")
        if problems:
            lines.append("  - problems: " + "; ".join(problems))
    lines += ["", "## Next actions"]
    lines += [f"- {action}" for action in payload.get("next_actions", [])]
    return "\n".join(lines)
