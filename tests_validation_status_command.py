import json
from pathlib import Path

from winlocalassistant import validate
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore


def test_validation_status_reads_latest_report_and_progress(tmp_path: Path):
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "validation_latest.json").write_text(
        json.dumps({
            "ok": False,
            "sections": [
                {"name": "compileall", "ok": True, "detail": {"elapsed_sec": 0.1}},
                {"name": "full_pytest", "ok": False, "detail": {"elapsed_sec": 12.5}},
            ],
        }),
        encoding="utf-8",
    )
    (logs / "validation_progress.jsonl").write_text(
        "\n".join([
            json.dumps({"ts": 1, "event": "section_started", "section": "compileall"}),
            json.dumps({"ts": 2, "event": "section_completed", "section": "compileall", "ok": True, "detail": {"elapsed_sec": 0.1}}),
            json.dumps({"ts": 3, "event": "section_started", "section": "full_pytest", "cmd": ["python", "-m", "pytest", "-q"]}),
            "not json",
        ]),
        encoding="utf-8",
    )

    status = validate.load_validation_status(tmp_path)
    rendered = validate.render_validation_status(status)

    assert status["state"] == "review"
    assert status["running_section"] == "full_pytest"
    assert status["failed_sections"] == ["full_pytest"]
    assert any("malformed" in warning for warning in status["warnings"])
    assert "Current/last-started stage: `full_pytest`" in rendered
    assert "Failed sections:" in rendered


def test_validation_status_command_is_routed_without_running_validation(tmp_path: Path, monkeypatch):
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "validation_latest.json").write_text(json.dumps({"ok": True, "sections": []}), encoding="utf-8")
    (logs / "validation_progress.jsonl").write_text(
        json.dumps({"ts": 1, "event": "section_completed", "section": "cli_smoke", "ok": True, "detail": {"elapsed_sec": 0.2}}) + "\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    out = AssistantCore(AssistantConfig(workspace=str(tmp_path))).handle_command("/validation-status")

    assert "Nova Validation Status" in out
    assert "State: **pass**" in out
    assert "Last completed stage: `cli_smoke`" in out


def test_validation_status_command_uses_configured_workspace_not_cwd(tmp_path: Path, monkeypatch):
    workspace = tmp_path / "workspace"
    other = tmp_path / "other"
    (workspace / "logs").mkdir(parents=True)
    (other / "logs").mkdir(parents=True)
    (workspace / "logs" / "validation_latest.json").write_text(json.dumps({"ok": True, "sections": []}), encoding="utf-8")
    (workspace / "logs" / "validation_progress.jsonl").write_text(
        json.dumps({"ts": 1, "event": "section_completed", "section": "workspace_stage", "ok": True}) + "\n",
        encoding="utf-8",
    )
    (other / "logs" / "validation_latest.json").write_text(json.dumps({"ok": False, "sections": []}), encoding="utf-8")
    (other / "logs" / "validation_progress.jsonl").write_text(
        json.dumps({"ts": 1, "event": "section_completed", "section": "wrong_cwd_stage", "ok": False}) + "\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(other)

    out = AssistantCore(AssistantConfig(workspace=str(workspace))).handle_command("/validation-status")

    assert "State: **pass**" in out
    assert "workspace_stage" in out
    assert "wrong_cwd_stage" not in out


def test_validation_status_warns_when_progress_log_is_interrupted_after_pass_report(tmp_path: Path):
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "validation_latest.json").write_text(json.dumps({"ok": True, "sections": []}), encoding="utf-8")
    (logs / "validation_progress.jsonl").write_text(
        "\n".join([
            json.dumps({"ts": 1, "event": "section_completed", "section": "cli_smoke", "ok": True}),
            json.dumps({"ts": 2, "event": "section_started", "section": "unit_tests_chunk_003"}),
        ]),
        encoding="utf-8",
    )

    status = validate.load_validation_status(tmp_path)
    rendered = validate.render_validation_status(status)

    assert status["state"] == "pass_report_with_interrupted_progress"
    assert status["progress_incomplete"] is True
    assert "unit_tests_chunk_003" in rendered
    assert "interrupted" in rendered or "still running" in rendered
