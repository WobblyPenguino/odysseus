"""
Task Scheduling System
Enables cron-like scheduling of commands and tools with local model support.
"""

import json
import logging
import threading
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Callable, Any
import re

from .config import APP_DIR
from .safe_io import read_json_file, atomic_write_json, append_jsonl, timestamp_id


SCHEDULER_DIR = Path(APP_DIR) / "scheduler"
SCHEDULER_DIR.mkdir(exist_ok=True, parents=True)

SCHEDULES_FILE = SCHEDULER_DIR / "schedules.json"
EXECUTION_LOG = SCHEDULER_DIR / "execution_log.jsonl"

_LOGGER = logging.getLogger(__name__)


class CronExpression:
    """Simple cron expression parser (minute hour day month day_of_week).

    This intentionally keeps Nova's existing Monday=0..Sunday=6 weekday mapping
    because earlier scheduler tests and saved tasks were built around
    ``datetime.weekday()``. The parser now validates numeric bounds at creation
    time so malformed expressions fail loudly instead of being saved as tasks
    that can never run.
    """

    def __init__(self, expression: str):
        parts = str(expression or "").strip().split()
        if len(parts) != 5:
            raise ValueError("Cron expression must have 5 parts: minute hour day month day_of_week")

        fields = (
            ("minute", parts[0], 0, 59),
            ("hour", parts[1], 0, 23),
            ("day", parts[2], 1, 31),
            ("month", parts[3], 1, 12),
            ("day_of_week", parts[4], 0, 6),
        )
        for name, pattern, min_val, max_val in fields:
            self._validate_field(name, pattern, min_val, max_val)

        self.minute = parts[0]
        self.hour = parts[1]
        self.day = parts[2]
        self.month = parts[3]
        self.day_of_week = parts[4]

    @classmethod
    def _validate_field(cls, name: str, pattern: str, min_val: int, max_val: int) -> None:
        def fail() -> None:
            raise ValueError(f"Cron {name} field {pattern!r} is outside {min_val}-{max_val} or is malformed")

        pattern = str(pattern or "")
        if pattern == "*":
            return
        if "," in pattern:
            parts = [part.strip() for part in pattern.split(",")]
            if not parts or any(not part for part in parts):
                fail()
            for part in parts:
                cls._validate_field(name, part, min_val, max_val)
            return
        if "/" in pattern:
            base, step_text = pattern.split("/", 1)
            try:
                step = int(step_text)
            except ValueError:
                fail()
            if step <= 0:
                fail()
            if base == "*":
                return
            cls._validate_field(name, base, min_val, max_val)
            return
        if "-" in pattern:
            start_text, end_text = pattern.split("-", 1)
            try:
                start, end = int(start_text), int(end_text)
            except ValueError:
                fail()
            if start > end or start < min_val or end > max_val:
                fail()
            return
        try:
            value = int(pattern)
        except ValueError:
            fail()
        if value < min_val or value > max_val:
            fail()

    def matches(self, dt: datetime) -> bool:
        """Check if datetime matches cron expression"""
        if not self._matches_field(self.minute, dt.minute, 0, 59):
            return False
        if not self._matches_field(self.hour, dt.hour, 0, 23):
            return False
        if not self._matches_field(self.day, dt.day, 1, 31):
            return False
        if not self._matches_field(self.month, dt.month, 1, 12):
            return False
        if not self._matches_field(self.day_of_week, dt.weekday(), 0, 6):
            return False
        return True

    @staticmethod
    def _matches_field(pattern: str, value: int, min_val: int, max_val: int) -> bool:
        """Check if value matches cron field pattern.

        Keep validation and matching semantics aligned. Step expressions must be
        evaluated before bare ranges/lists because patterns such as ``10-40/5``
        contain both ``-`` and ``/``.
        """
        pattern = str(pattern or "")
        if pattern == "*":
            return True

        # Handle lists like 0,1,2 and mixed validated items such as 0,15-45/15.
        if "," in pattern:
            return any(CronExpression._matches_field(part.strip(), value, min_val, max_val) for part in pattern.split(",") if part.strip())

        # Handle step values like */5, 10/5, or 10-40/5.
        if "/" in pattern:
            parts = pattern.split("/", 1)
            if len(parts) == 2:
                try:
                    base, step_text = parts
                    step = int(step_text)
                    if step <= 0:
                        return False
                    if base == "*":
                        start, end = min_val, max_val
                    elif "-" in base:
                        start_text, end_text = base.split("-", 1)
                        start, end = int(start_text), int(end_text)
                    else:
                        start, end = int(base), max_val
                    return start <= value <= end and (value - start) % step == 0
                except (ValueError, IndexError):
                    return False

        # Handle ranges like 0-5.
        if "-" in pattern:
            parts = pattern.split("-", 1)
            if len(parts) == 2:
                try:
                    start, end = int(parts[0]), int(parts[1])
                    return start <= value <= end
                except ValueError:
                    return False

        # Direct value.
        try:
            return value == int(pattern)
        except ValueError:
            return False


@dataclass
class ScheduledTask:
    id: str
    name: str
    schedule: str  # Cron expression
    command: str  # Command to execute
    params: dict[str, Any] = None
    active: bool = True
    created_at: str = None
    last_run: Optional[str] = None
    last_result: Optional[str] = None
    run_count: int = 0
    error_count: int = 0
    timeout_seconds: int = 300

    def __post_init__(self):
        if self.params is None:
            self.params = {}
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    def should_run(self, dt: datetime = None) -> bool:
        """Check if task should run at given datetime"""
        if not self.active:
            return False
        
        if dt is None:
            dt = datetime.now()
        
        try:
            cron = CronExpression(self.schedule)
            return cron.matches(dt)
        except Exception:
            return False


@dataclass
class ExecutionRecord:
    task_id: str
    timestamp: str
    duration_ms: float
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


class TaskScheduler:
    """Manages scheduled task execution"""

    def __init__(self):
        self.tasks: dict[str, ScheduledTask] = self._load_tasks()
        self.callbacks: dict[str, Callable] = {}  # Command name -> handler function
        self._scheduler_thread: Optional[threading.Thread] = None
        self._should_stop = False
        self.last_check: datetime = datetime.now()

    def _load_tasks(self) -> dict[str, ScheduledTask]:
        """Load scheduled tasks from config"""
        tasks = {}
        try:
            if SCHEDULES_FILE.exists():
                data = read_json_file(SCHEDULES_FILE, {"tasks": []}, expected_type=dict, quarantine=True)
                for task_data in data.get("tasks", []):
                    if not isinstance(task_data, dict):
                        _LOGGER.warning("Skipping malformed scheduled task row: %r", task_data)
                        continue
                    try:
                        task = ScheduledTask(**task_data)
                        # Validate schedule while loading so corrupt/stale rows do not
                        # repeatedly fail at runtime with no useful clue.
                        CronExpression(task.schedule)
                        tasks[task.id] = task
                    except Exception as exc:
                        _LOGGER.warning("Skipping invalid scheduled task row: %r", exc)
        except Exception as exc:
            _LOGGER.warning("Failed to load scheduled tasks from %s: %r", SCHEDULES_FILE, exc)
        return tasks

    def _save_tasks(self) -> None:
        """Save tasks to config"""
        try:
            data = {
                "tasks": [task.to_dict() for task in self.tasks.values()],
                "saved_at": datetime.now().isoformat(),
            }
            atomic_write_json(SCHEDULES_FILE, data)
        except Exception as exc:
            _LOGGER.warning("Failed to save scheduled tasks to %s: %r", SCHEDULES_FILE, exc)

    def register_command_handler(self, command: str, handler: Callable) -> None:
        """Register a handler for a command"""
        self.callbacks[command] = handler

    def add_task(
        self,
        name: str,
        schedule: str,
        command: str,
        params: Optional[dict[str, Any]] = None,
        timeout_seconds: int = 300,
    ) -> ScheduledTask:
        """Add a new scheduled task."""
        # Validate early so a malformed schedule is rejected instead of silently
        # creating a task that will never run.
        CronExpression(schedule)
        task_id = f"task_{timestamp_id()}"
        
        task = ScheduledTask(
            id=task_id,
            name=name,
            schedule=schedule,
            command=command,
            params=params or {},
            timeout_seconds=timeout_seconds,
        )

        self.tasks[task_id] = task
        self._save_tasks()
        return task

    def remove_task(self, task_id: str) -> bool:
        """Remove a scheduled task"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self._save_tasks()
            return True
        return False

    def enable_task(self, task_id: str) -> bool:
        """Enable a task"""
        if task_id in self.tasks:
            self.tasks[task_id].active = True
            self._save_tasks()
            return True
        return False

    def disable_task(self, task_id: str) -> bool:
        """Disable a task"""
        if task_id in self.tasks:
            self.tasks[task_id].active = False
            self._save_tasks()
            return True
        return False

    def execute_task(self, task_id: str) -> bool:
        """Execute a task immediately"""
        task = self.tasks.get(task_id)
        if not task:
            return False

        handler = self.callbacks.get(task.command)
        if not handler:
            return False

        try:
            start = time.time()
            result = handler(task.params)
            duration_ms = (time.time() - start) * 1000

            record = ExecutionRecord(
                task_id=task_id,
                timestamp=datetime.now().isoformat(),
                duration_ms=duration_ms,
                success=True,
                output=str(result),
            )

            task.last_run = datetime.now().isoformat()
            task.run_count += 1
            task.last_result = str(result)

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            record = ExecutionRecord(
                task_id=task_id,
                timestamp=datetime.now().isoformat(),
                duration_ms=duration_ms,
                success=False,
                error=str(e),
            )
            task.error_count += 1

        try:
            append_jsonl(EXECUTION_LOG, record.to_dict())
        except Exception as exc:
            _LOGGER.warning("Failed to append scheduler execution record for %s: %r", task_id, exc)

        self._save_tasks()
        return record.success

    def start(self) -> None:
        """Start the scheduler"""
        if self._scheduler_thread is None or not self._scheduler_thread.is_alive():
            self._should_stop = False
            self._scheduler_thread = threading.Thread(
                target=self._schedule_loop,
                daemon=True,
            )
            self._scheduler_thread.start()

    def _schedule_loop(self) -> None:
        """Main scheduler loop (runs in background thread)"""
        while not self._should_stop:
            try:
                now = datetime.now()
                
                # Check every minute
                if (now - self.last_check).total_seconds() >= 60:
                    self.last_check = now
                    
                    for task_id, task in list(self.tasks.items()):
                        if task.should_run(now):
                            self.execute_task(task_id)

            except Exception as exc:
                _LOGGER.warning("Scheduler loop failed during task scan: %r", exc)

            time.sleep(10)  # Check every 10 seconds

    def stop(self) -> None:
        """Stop the scheduler"""
        self._should_stop = True
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)

    def get_execution_stats(self, task_id: str, hours: int = 24) -> dict[str, Any]:
        """Get execution statistics for a task"""
        cutoff = datetime.now() - timedelta(hours=hours)
        stats = {
            "total": 0,
            "successful": 0,
            "failed": 0,
            "avg_duration_ms": 0,
        }

        try:
            if EXECUTION_LOG.exists():
                durations = []
                for line in EXECUTION_LOG.read_text().strip().split("\n"):
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        if data["task_id"] != task_id:
                            continue
                        if datetime.fromisoformat(data["timestamp"]) < cutoff:
                            continue

                        stats["total"] += 1
                        if data["success"]:
                            stats["successful"] += 1
                        else:
                            stats["failed"] += 1
                        durations.append(data["duration_ms"])

                    except Exception as exc:
                        _LOGGER.debug("Skipping malformed scheduler execution log row: %r", exc)
                        continue

                if durations:
                    stats["avg_duration_ms"] = sum(durations) / len(durations)

        except Exception as exc:
            _LOGGER.warning("Failed to read scheduler execution stats for %s: %r", task_id, exc)

        return stats


def render_scheduler_status() -> str:
    """Render scheduler status in markdown"""
    scheduler = TaskScheduler()
    
    md = "# Task Scheduler Status\n\n"
    md += f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"

    active = [t for t in scheduler.tasks.values() if t.active]
    md += f"## Active Tasks ({len(active)})\n\n"

    for task in active:
        stats = scheduler.get_execution_stats(task.id, hours=24)
        md += f"### {task.name}\n"
        md += f"- **Schedule**: {task.schedule}\n"
        md += f"- **Command**: {task.command}\n"
        md += f"- **Runs (24h)**: {stats['total']} ({stats['successful']} ✅, {stats['failed']} ❌)\n"
        if task.last_run:
            md += f"- **Last Run**: {task.last_run}\n"
        md += "\n"

    return md


# Global scheduler
_task_scheduler: Optional[TaskScheduler] = None


def get_task_scheduler() -> TaskScheduler:
    """Get or create the global task scheduler"""
    global _task_scheduler
    if _task_scheduler is None:
        _task_scheduler = TaskScheduler()
    return _task_scheduler
