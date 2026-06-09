from pathlib import Path
from winlocalassistant import validate


def test_run_reports_timeout_details(tmp_path):
    script = tmp_path / "slow.py"
    script.write_text(
        "import sys, time\nprint('partial out')\nsys.stdout.flush()\nprint('partial err', file=sys.stderr)\nsys.stderr.flush()\ntime.sleep(5)\n",
        encoding="utf-8",
    )

    result = validate._run([validate.sys.executable, str(script)], tmp_path, timeout=2)

    assert result["ok"] is False
    assert result["timed_out"] is True
    assert result["timeout_sec"] == 2
    # Startup latency can mean a timeout happens before any child output.
    # The guarantee is that Nova returns a structured timeout instead of hanging.
    assert "stdout_tail" in result
    assert "stderr_tail" in result
    assert "timed out" in result["error"]


def test_run_file_backed_capture_reports_completed_output(tmp_path):
    script = tmp_path / "ok.py"
    script.write_text("import sys\nprint('done out')\nprint('done err', file=sys.stderr)\n", encoding="utf-8")

    result = validate._run([validate.sys.executable, str(script)], tmp_path, timeout=60)

    assert result["ok"] is True
    assert "done out" in result["stdout_tail"]
    assert "done err" in result["stderr_tail"]


def test_render_validation_includes_failure_context():
    payload = {
        "ok": False,
        "sections": [
            {
                "name": "full_pytest",
                "ok": False,
                "detail": {
                    "cmd": ["python", "-m", "pytest", "-q"],
                    "elapsed_sec": 120.5,
                    "timeout_sec": 120,
                    "timed_out": True,
                    "error": "Command timed out after 120 second(s)",
                },
            }
        ],
        "note": "test note",
    }

    text = validate.render_validation(payload)

    assert "full_pytest: FAIL" in text
    assert "120.5s" in text
    assert "timed out after 120s" in text
    assert "cmd=python -m pytest -q" in text


def test_validate_all_writes_progress_log(monkeypatch, tmp_path):
    (tmp_path / "winlocalassistant").mkdir()
    (tmp_path / "winlocalassistant" / "__init__.py").write_text("__version__ = '55.3.164'\n", encoding="utf-8")
    (tmp_path / "nova").mkdir()
    (tmp_path / "app.py").write_text("print('Nova 55.3.164')\n", encoding="utf-8")

    def fake_run(cmd, cwd, timeout=180):
        return {
            "cmd": cmd,
            "ok": True,
            "returncode": 0,
            "elapsed_sec": 0.01,
            "timeout_sec": timeout,
            "stdout_tail": "Nova 55.3.164",
            "stderr_tail": "",
        }

    monkeypatch.setattr(validate, "_run", fake_run)
    monkeypatch.setattr(validate, "_version_sync", lambda root: {"ok": True, "version": "55.3.164"})
    monkeypatch.setattr(validate, "_launcher_checks", lambda root: {"ok": True, "checks": {}})
    monkeypatch.setattr(validate, "_startup_obviousness", lambda root: {"ok": True, "results": {}})
    monkeypatch.setattr(validate, "_web_smoke", lambda root: {"ok": True, "required": {}})

    payload = validate.validate_all(tmp_path, full=False)
    progress = tmp_path / "logs" / "validation_progress.jsonl"
    lines = progress.read_text(encoding="utf-8").splitlines()

    assert payload["progress_log"] == "logs/validation_progress.jsonl"
    assert any('"event": "section_started"' in line and '"section": "compileall"' in line for line in lines)
    assert any('"event": "section_completed"' in line and '"section": "cli_smoke"' in line for line in lines)
    assert "Progress log: logs/validation_progress.jsonl" in validate.render_validation(payload)
