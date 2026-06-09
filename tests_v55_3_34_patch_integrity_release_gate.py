import json
from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.docker_manager import docker_promote_validated_patch
from winlocalassistant.wla_doctor import run_wla_doctor, run_wla_release_gate


def test_patch_validation_reports_include_sha256_guardrail(tmp_path, monkeypatch):
    import winlocalassistant.docker_manager as dm
    run_dir = tmp_path / "docker_runs" / "run123"
    run_dir.mkdir(parents=True)
    patch = run_dir / "input.patch"
    patch.write_text("original patch text\n", encoding="utf-8")
    report = {
        "ok": True,
        "type": "patch_validation",
        "run_id": "run123",
        "patch_path": str(patch),
        "patch_sha256": "definitely-not-the-current-hash",
        "source_path": str(tmp_path),
        "summary": "Docker patch validation passed",
    }
    (run_dir / "validation_report.json").write_text(json.dumps(report), encoding="utf-8")
    monkeypatch.setattr(dm, "DOCKER_RUNS_DIR", tmp_path / "docker_runs")
    payload = docker_promote_validated_patch(AssistantConfig(workspace=str(tmp_path)), run_id="run123", path=str(tmp_path))
    assert payload["ok"] is False
    assert "hash" in payload["summary"].lower()
    assert payload["expected_patch_sha256"] != payload["actual_patch_sha256"]


def test_wla_doctor_checks_patch_hash_locking():
    payload = run_wla_doctor(Path("."), "verify patch promotion safety")
    names = {check["name"]: check for check in payload["checks"]}
    assert "patch_hash_locking" in names
    assert names["patch_hash_locking"]["ok"] is True


def test_release_gate_command_can_be_run_with_tiny_custom_check():
    payload = run_wla_release_gate(Path("."), "quick release gate smoke", test_command="python -c 'print(123)' ")
    assert "doctor" in payload
    assert any(cmd["name"] == "compileall" for cmd in payload["commands"])
    assert any(cmd["name"] == "custom_tests" for cmd in payload["commands"])
