from __future__ import annotations

from pathlib import Path

from winlocalassistant.model_calibration import build_model_calibration, benchmark_deterministic_chat, render_model_calibration_markdown


def test_model_calibration_writes_host_probe_report(tmp_path: Path):
    payload = build_model_calibration(tmp_path, run_benchmarks=False)
    assert payload["ok"] is True
    assert "ollama_list" in payload["probes"]
    assert "nvidia_smi" in payload["probes"]
    assert (tmp_path / "docs" / "NOVA_MODEL_CALIBRATION_LATEST.json").exists()
    rendered = render_model_calibration_markdown(payload)
    assert "Nova Model Calibration" in rendered
    assert "ollama list" in rendered


def test_deterministic_chat_benchmark_has_useful_rows(tmp_path: Path):
    rows = benchmark_deterministic_chat(tmp_path, prompts=["hi", "help", "run a command safely"])
    assert len(rows) == 3
    assert all(row["ok"] for row in rows)
    assert any("/verify" in row["reply_preview"] for row in rows)
