from __future__ import annotations

from datetime import datetime

from winlocalassistant.core import AssistantCore
from winlocalassistant.task_scheduler import CronExpression, get_task_scheduler


def test_new_improvement_commands_load_and_return_useful_text() -> None:
    core = AssistantCore.load()
    checks = {
        "analytics": "Analytics Dashboard",
        "performance_report": "Performance Analysis Report",
        "webhook_status": "Webhook Status",
        "list_tasks": "Task Scheduler Status",
        "proposal_ledger_view": "Proposal Ledger",
        "completed_improvements": "Completed Improvements",
    }
    for command, marker in checks.items():
        result = core.tools.call(command)
        assert result.ok, f"{command} failed: {result.summary}"
        message = str((result.data or {}).get("message", ""))
        assert marker in message, f"{command} did not return expected marker {marker!r}"


def test_scheduler_cron_step_expression_matches_expected_minutes() -> None:
    cron = CronExpression("*/5 * * * *")
    assert cron.matches(datetime(2026, 6, 1, 10, 10)) is True
    assert cron.matches(datetime(2026, 6, 1, 10, 11)) is False


def test_scheduler_rejects_malformed_cron_through_tool() -> None:
    core = AssistantCore.load()
    result = core.tools.call("schedule_task", action="add", name="bad", schedule="not valid", command="analytics")
    assert result.ok is False
    assert "Cron expression" in result.summary or "Scheduler error" in result.summary


def test_scheduler_can_run_safe_registered_tool() -> None:
    core = AssistantCore.load()
    add = core.tools.call("schedule_task", action="add", name="analytics smoke", schedule="* * * * *", command="analytics")
    assert add.ok, add.summary
    task_id = add.data["task"]["id"]
    try:
        run = core.tools.call("task_scheduler", action="run", task_id=task_id)
        assert run.ok, run.summary
    finally:
        scheduler = get_task_scheduler()
        scheduler.remove_task(task_id)
        scheduler.stop()


def run_all(verbose: bool = False) -> None:
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            if verbose:
                print(f"PASS {name}")


if __name__ == "__main__":
    run_all(True)
