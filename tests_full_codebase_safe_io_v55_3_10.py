from __future__ import annotations

import json
from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.config import AssistantConfig
from winlocalassistant.safe_io import atomic_write_json, atomic_write_text, unique_path
import winlocalassistant.efficiency_profiler as profiler
from winlocalassistant.efficiency_profiler import render_efficiency_markdown
from winlocalassistant.code_quality_gate import write_code_quality_gate_report
from winlocalassistant.code_review_audit import write_code_review_report
from winlocalassistant.code_repair_audit import write_code_repair_audit_report
from winlocalassistant.codebase_integrity_audit import write_codebase_integrity_report
from winlocalassistant.architecture_audit import write_architecture_audit_report


def test_safe_io_atomic_write_text_and_json(tmp_path: Path):
    text_path = tmp_path / "nested" / "state.txt"
    json_path = tmp_path / "nested" / "state.json"
    atomic_write_text(text_path, "hello")
    atomic_write_json(json_path, {"ok": True, "items": [1, 2]})
    assert text_path.read_text(encoding="utf-8") == "hello"
    assert json.loads(json_path.read_text(encoding="utf-8"))["ok"] is True
    assert not list(tmp_path.rglob("*.tmp"))


def test_unique_path_does_not_collide_under_fast_repeated_calls(tmp_path: Path):
    paths = [unique_path(tmp_path, "report", ".md") for _ in range(25)]
    assert len({p.name for p in paths}) == len(paths)
    assert all(p.parent == tmp_path for p in paths)


def test_efficiency_report_survives_malformed_numeric_samples(tmp_path: Path, monkeypatch):
    log = tmp_path / "efficiency_metrics.jsonl"
    reports = tmp_path / "reports"
    monkeypatch.setattr(profiler, "EFFICIENCY_LOG_PATH", log)
    monkeypatch.setattr(profiler, "EFFICIENCY_REPORT_DIR", reports)
    log.write_text(
        json.dumps({"kind":"tool","name":"bad","ok":True,"wall_ms":"not-a-number","process_cpu_ms":"also-bad","estimated_joules":"bad"}) + "\n"
        + "not json\n"
        + json.dumps({"kind":"tool","name":"good","ok":True,"wall_ms":10,"process_cpu_ms":2,"estimated_joules":0.5}) + "\n",
        encoding="utf-8",
    )
    text, md, js, payload = render_efficiency_markdown(AssistantConfig(workspace=str(tmp_path)))
    assert "Nova Efficiency Report" in text
    assert md.exists() and js.exists()
    assert payload["sample_count"] == 2
    assert payload["total_wall_ms"] == 10.0


def test_key_audit_report_writers_use_unique_atomic_outputs(tmp_path: Path):
    writers = [
        write_code_quality_gate_report,
        write_code_review_report,
        write_code_repair_audit_report,
        write_codebase_integrity_report,
    ]
    for writer in writers:
        first = writer(tmp_path)
        second = writer(tmp_path)
        assert first[0] != second[0]
        assert first[1] != second[1]
        assert first[0].exists() and first[1].exists()
        assert second[0].exists() and second[1].exists()

    a1 = write_architecture_audit_report(tmp_path, tmp_path)
    a2 = write_architecture_audit_report(tmp_path, tmp_path)
    assert a1[0] != a2[0]
    assert a1[1] != a2[1]


def test_version_label_updated_for_v55_3_10():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 123)
    assert f"v{__version__}" in VERSION_LABEL


def test_integrity_and_architecture_audits_do_not_flag_self_created_pycache(tmp_path: Path):
    # Importing audit modules may create __pycache__; that should not make the audit
    # look dirty every time a user runs it. Persistent caches such as .pytest_cache
    # can still be handled by release cleanup.
    pkg = tmp_path / "winlocalassistant"
    cache = pkg / "__pycache__"
    cache.mkdir(parents=True)
    (cache / "sample.pyc").write_bytes(b"cache")
    from winlocalassistant.codebase_integrity_audit import run_codebase_integrity_audit
    from winlocalassistant.architecture_audit import run_architecture_audit

    integrity = run_codebase_integrity_audit(tmp_path)
    assert not [i for i in integrity.issues if i.title == "Runtime/cache artifacts present"]
    architecture = run_architecture_audit(tmp_path)
    runtime_check = [c for c in architecture.checks if c.get("name") == "runtime_artifacts"][0]
    assert runtime_check["count"] == 0


def test_quality_gate_does_not_flag_import_created_pycache(tmp_path: Path):
    pkg = tmp_path / "winlocalassistant"
    cache = pkg / "__pycache__"
    cache.mkdir(parents=True)
    (cache / "sample.pyc").write_bytes(b"cache")
    (pkg / "sample.py").write_text("def ok():\n    return 1\n", encoding="utf-8")
    from winlocalassistant.code_quality_gate import run_code_quality_gate

    report = run_code_quality_gate(tmp_path)
    assert not [c for c in report.comments if c.title == "Runtime/cache artifact present"]
