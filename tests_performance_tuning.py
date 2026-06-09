from __future__ import annotations

import os
from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.performance_tuning import (
    PATCH_ID,
    apply_startup_performance_environment,
    benchmark_plan_payload,
    collect_performance_status,
    render_artifact_checklist,
    render_benchmark_plan,
    render_performance_status,
    render_tuning_plan,
    build_tuning_plan,
    write_benchmark_scripts,
)


def test_safe_performance_env_defaults_do_not_override(monkeypatch):
    for key in ["OLLAMA_FLASH_ATTENTION", "TOKENIZERS_PARALLELISM", "CUDA_LAUNCH_BLOCKING", "NOVA_PERF_ENV_PROFILE", "OMP_NUM_THREADS"]:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("OMP_NUM_THREADS", "13")
    payload = apply_startup_performance_environment()
    assert payload["ok"] is True
    assert os.environ["OLLAMA_FLASH_ATTENTION"] == "1"
    assert os.environ["TOKENIZERS_PARALLELISM"] == "false"
    assert os.environ["CUDA_LAUNCH_BLOCKING"] == "0"
    assert os.environ["OMP_NUM_THREADS"] == "13"
    assert payload["preserved"]["OMP_NUM_THREADS"] == "already-set"


def test_performance_status_redacts_tokens_and_renders(tmp_path, monkeypatch):
    monkeypatch.setenv("NOVA_API_TOKEN", "secret-token-value")
    monkeypatch.setenv("OLLAMA_FLASH_ATTENTION", "1")
    payload = collect_performance_status(tmp_path)
    text = render_performance_status(payload)
    assert payload["patch_id"] == PATCH_ID
    assert payload["env"]["NOVA_API_TOKEN"]["value"] == "<redacted>"
    assert "secret-token-value" not in text
    assert "Nova Local AI Performance Status" in text
    assert "Manual-only" in text


def test_benchmark_plan_and_scripts_are_safe_and_reproducible(tmp_path):
    plan = benchmark_plan_payload(tmp_path)
    rendered = render_benchmark_plan(plan)
    assert "wall_ms" in rendered
    assert "nvidia" in rendered or "gpu" in rendered.lower()
    result = write_benchmark_scripts(tmp_path)
    assert result["ok"] is True
    assert (tmp_path / "scripts" / "nova_perf_probe.py").exists()
    assert (tmp_path / "scripts" / "nova_perf_collect.ps1").exists()
    assert (tmp_path / "docs" / "NOVA_LOCAL_AI_PERFORMANCE_TUNING.md").exists()
    assert "NOVA_API_TOKEN" not in (tmp_path / "scripts" / "nova_perf_probe.py").read_text(encoding="utf-8")


def test_core_performance_commands_route(tmp_path):
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True))
    assert "Nova Local AI Performance Status" in core.handle_command("/perf-status")
    assert "Nova Local AI Performance Tuning Plan" in core.handle_command("/perf-tune-plan")
    assert "Nova Performance Benchmark Plan" in core.handle_command("/perf-benchmark")
    assert "Nova Performance Artifact Checklist" in core.handle_command("/perf-artifact-checklist")
    assert "Nova Performance Benchmark Scripts" in core.handle_command("/perf-benchmark --write-scripts")


def test_tuning_plan_renders_rollback():
    text = render_tuning_plan(build_tuning_plan())
    assert "Rollback" in text
    assert "Defender" in text
    assert "quantized" in text
