from pathlib import Path

from winlocalassistant import validate


def _minimal_repo(root: Path) -> None:
    (root / "winlocalassistant").mkdir()
    (root / "winlocalassistant" / "__init__.py").write_text("__version__ = '55.3.164'\n", encoding="utf-8")
    (root / "nova").mkdir()
    (root / "app.py").write_text("print('Nova 55.3.164')\n", encoding="utf-8")
    for rel in [
        "orchestration_foundation.py",
        "repo_intelligence.py",
        "browser_worker.py",
        "document_ingestion.py",
        "nova_video.py",
        "model_registry.py",
        "integration_review.py",
    ]:
        (root / "winlocalassistant" / rel).write_text("# fixture\n", encoding="utf-8")
    (root / "RELEASE_MANIFEST.json").write_text("{}\n", encoding="utf-8")
    for idx in range(5):
        (root / f"tests_chunk_{idx}.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")


def test_chunked_full_pytest_records_bounded_chunks(monkeypatch, tmp_path):
    _minimal_repo(tmp_path)
    calls = []

    def fake_run(cmd, cwd, timeout=180):
        calls.append(list(cmd))
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

    payload = validate.validate_all(tmp_path, full=True, chunk_size=2)
    full = next(section for section in payload["sections"] if section["name"] == "full_pytest")

    assert payload["ok"] is True
    assert full["detail"]["mode"] == "chunked"
    assert full["detail"]["total_files"] == 5
    assert full["detail"]["total_chunks"] == 3
    assert full["detail"]["completed_chunks"] == 3
    assert all(len(chunk["files"]) <= 2 for chunk in full["detail"]["chunks"])
    assert any(cmd[:3] == [validate.sys.executable, "-m", "pytest"] and "tests_chunk_0.py" in cmd for cmd in calls)

    progress = (tmp_path / "logs" / "validation_progress.jsonl").read_text(encoding="utf-8")
    assert "full_pytest_chunk_001" in progress
    assert "full_pytest_chunk_003" in progress
    assert "chunked 3/3 chunks" in validate.render_validation(payload)


def test_chunked_full_pytest_stops_on_first_failed_chunk(monkeypatch, tmp_path):
    _minimal_repo(tmp_path)
    runs = {"count": 0}

    def fake_run(cmd, cwd, timeout=180):
        is_chunk = len(cmd) >= 4 and cmd[1:4] == ["-m", "pytest", "-q"]
        if is_chunk:
            runs["count"] += 1
            ok = runs["count"] != 2
        else:
            ok = True
        return {
            "cmd": cmd,
            "ok": ok,
            "returncode": 0 if ok else 1,
            "elapsed_sec": 0.02,
            "timeout_sec": timeout,
            "stdout_tail": "Nova 55.3.164" if not is_chunk else ("passed" if ok else "failed assertion"),
            "stderr_tail": "",
        }

    monkeypatch.setattr(validate, "_run", fake_run)
    monkeypatch.setattr(validate, "_version_sync", lambda root: {"ok": True, "version": "55.3.164"})
    monkeypatch.setattr(validate, "_launcher_checks", lambda root: {"ok": True, "checks": {}})
    monkeypatch.setattr(validate, "_startup_obviousness", lambda root: {"ok": True, "results": {}})
    monkeypatch.setattr(validate, "_web_smoke", lambda root: {"ok": True, "required": {}})

    payload = validate.validate_all(tmp_path, full=True, chunk_size=2)
    full = next(section for section in payload["sections"] if section["name"] == "full_pytest")

    assert payload["ok"] is False
    assert full["ok"] is False
    assert full["detail"]["completed_chunks"] == 2
    assert full["detail"]["failed_chunks"] == ["full_pytest_chunk_002"]
    rendered = validate.render_validation(payload)
    assert "full_pytest: FAIL" in rendered
    assert "failed=full_pytest_chunk_002" in rendered


def test_targeted_pytest_chunks_can_report_unit_test_groups(monkeypatch, tmp_path):
    calls = []

    def fake_run(cmd, cwd, timeout=180):
        calls.append(list(cmd))
        return {
            "cmd": cmd,
            "ok": True,
            "returncode": 0,
            "elapsed_sec": 0.03,
            "timeout_sec": timeout,
            "stdout_tail": "passed",
            "stderr_tail": "",
        }

    monkeypatch.setattr(validate, "_run", fake_run)
    result = validate._run_pytest_chunks(
        tmp_path,
        chunk_size=2,
        timeout_per_chunk=10,
        test_files=["tests_a.py", "tests_b.py", "tests_c.py"],
        section_prefix="unit_tests",
    )

    assert result["ok"] is True
    assert result["total_chunks"] == 2
    assert result["chunks"][0]["name"] == "unit_tests_chunk_001"
    assert result["chunks"][1]["files"] == ["tests_c.py"]
    assert calls[0][:3] == [validate.sys.executable, "-m", "pytest"]
    progress = (tmp_path / "logs" / "validation_progress.jsonl").read_text(encoding="utf-8")
    assert "unit_tests_chunk_001" in progress
