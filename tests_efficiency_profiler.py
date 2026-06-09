from __future__ import annotations

import json
from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.efficiency_profiler import EFFICIENCY_LOG_PATH, read_efficiency_samples, append_efficiency_sample, set_runtime_profiler_enabled
from winlocalassistant.tools import ToolRegistry, ToolResult


def _config(tmp_path: Path) -> AssistantConfig:
    set_runtime_profiler_enabled(True)
    cfg = AssistantConfig(workspace=str(tmp_path))
    cfg.efficiency_profiler_enabled = True
    cfg.efficiency_cpu_watts = 40.0
    cfg.efficiency_gpu_watts = 0.0
    cfg.efficiency_model_extra_watts = 10.0
    return cfg


def test_tool_registry_records_efficiency_sample(tmp_path):
    cfg = _config(tmp_path)
    if EFFICIENCY_LOG_PATH.exists():
        EFFICIENCY_LOG_PATH.unlink()
    reg = ToolRegistry(cfg)
    reg.register("dummy_efficiency_tool", lambda: ToolResult(True, "dummy ok", {"value": 1}))

    result = reg.call("dummy_efficiency_tool")

    assert result.ok
    assert "efficiency" in result.data
    samples = read_efficiency_samples(limit=20)
    assert any(s.get("kind") == "tool" and s.get("name") == "dummy_efficiency_tool" for s in samples)
    assert all(float(s.get("wall_ms") or 0) >= 0 for s in samples)


def test_efficiency_command_times_read_only_command(tmp_path):
    cfg = _config(tmp_path)
    core = AssistantCore(cfg)

    out = core.efficiency_command("time 2 /status")

    assert "Timed efficiency run completed" in out
    assert "Average wall time" in out
    samples = read_efficiency_samples(limit=50)
    assert any(s.get("kind") == "timed_run" and s.get("name") == "/status" for s in samples)


def test_efficiency_report_and_clear(tmp_path):
    cfg = _config(tmp_path)
    core = AssistantCore(cfg)
    core.efficiency_command("time 1 /avatar")

    report = core.efficiency_command("report")
    assert "Nova Efficiency Report" in report
    assert "Estimated energy" in report

    cleared = core.efficiency_command("clear")
    assert "cleared" in cleared.lower()


def test_efficiency_off_disables_automatic_chat_samples(tmp_path):
    cfg = _config(tmp_path)
    core = AssistantCore(cfg)
    core.efficiency_command("clear")
    off = core.efficiency_command("off")
    assert "disabled" in off.lower()
    # Clear the sample written while toggling off; future automatic chat/tool samples
    # must remain suppressed while the profiler is disabled.
    core.efficiency_command("clear")

    core.chat("/status")

    samples = read_efficiency_samples(limit=20)
    assert samples == []

    stale_cfg = _config(tmp_path)
    stale_cfg.efficiency_profiler_enabled = True
    set_runtime_profiler_enabled(False)
    append_efficiency_sample(stale_cfg, kind="tool", name="stale_core", ok=True, wall_s=0.001, process_cpu_s=0.0)
    assert read_efficiency_samples(limit=20) == []


def test_efficiency_time_blocks_mutating_or_recursive_commands(tmp_path):
    cfg = _config(tmp_path)
    core = AssistantCore(cfg)

    blocked = core.efficiency_command("time 2 /do build a test app")
    assert "blocked" in blocked.lower()
    assert "/do" in blocked

    nested = core.efficiency_command("time 2 /efficiency time 2 /status")
    assert "blocked" in nested.lower()
    assert "nested" in nested.lower()


def test_efficiency_time_normal_prompt_does_not_use_mutating_build_path(tmp_path, monkeypatch):
    cfg = _config(tmp_path)
    cfg.allow_mutating_tools = True
    core = AssistantCore(cfg)
    monkeypatch.setattr("winlocalassistant.core.model_chat", lambda *a, **k: "mocked plain reply")
    core.efficiency_command("clear")

    out = core.efficiency_command("time 1 build a tiny app")

    assert "Timed efficiency run completed" in out
    # It should be benchmarked as normal chat, not treated as an auto build/edit task.
    assert not (tmp_path / ".nova_project.json").exists()
