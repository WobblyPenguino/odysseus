from __future__ import annotations

import tempfile

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.tools import ToolRegistry, ToolResult


class HealthGateTools(ToolRegistry):
    def __init__(self, config: AssistantConfig):
        super().__init__(config)
        self.calls: list[str] = []

    def call(self, tool_name: str, **kwargs):  # type: ignore[override]
        self.calls.append(tool_name)
        if tool_name == "runtime_self_check":
            return ToolResult(False, "runtime check failed", {"error": "broken"})
        return ToolResult(True, f"{tool_name} ok", {})


class StopAwareTools(ToolRegistry):
    def __init__(self, config: AssistantConfig, core: AssistantCore):
        super().__init__(config)
        self.core = core
        self.calls: list[str] = []

    def call(self, tool_name: str, **kwargs):  # type: ignore[override]
        self.calls.append(tool_name)
        if tool_name == "heartbeat":
            self.core.autonomous_state["stop_requested"] = True
        return ToolResult(True, f"{tool_name} ok", {})


def test_start_options_parse_cycle_limit_and_diagnostic_only() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_auto_opts_") as tmp:
        core = AssistantCore(AssistantConfig(workspace=tmp, allow_mutating_tools=True))
        goal, cycles, diagnostic = core._parse_autonomous_goal_options("--cycles 3 --diagnostic investigate logs")
        assert goal == "investigate logs"
        assert cycles == 3
        assert diagnostic is True


def test_dead_enabled_worker_can_be_recovered_on_start() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_auto_dead_") as tmp:
        core = AssistantCore(AssistantConfig(workspace=tmp, allow_mutating_tools=True))
        core.autonomous_state["enabled"] = True
        core._autonomous_thread = None
        core._autonomous_loop = lambda: None  # type: ignore[method-assign]
        out = core.autonomous_command("start --cycles 1 investigate logs")
        assert "Autonomous mode started" in out
        assert core.autonomous_state["max_cycles"] == 1
        core.autonomous_command("stop")


def test_autonomous_health_gate_skips_mutating_sequence_after_runtime_failure() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_auto_health_gate_") as tmp:
        cfg = AssistantConfig(workspace=tmp, allow_mutating_tools=True)
        core = AssistantCore(cfg)
        core.tools = HealthGateTools(cfg)
        out = core.autonomous_once("make a calculator app")
        calls = core.tools.calls  # type: ignore[attr-defined]
        assert "runtime_self_check" in calls
        assert "ai_create_project" not in calls
        assert "Autonomous health gate" in out


def test_diagnostic_only_skips_mutating_sequence() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_auto_diag_") as tmp:
        cfg = AssistantConfig(workspace=tmp, allow_mutating_tools=True)
        core = AssistantCore(cfg)
        core.tools = HealthGateTools(cfg)
        out = core.autonomous_once("--diagnostic make a calculator app")
        calls = core.tools.calls  # type: ignore[attr-defined]
        assert "ai_create_project" not in calls
        assert "Diagnostic-only mode" in out


def test_stop_requested_skips_final_health_checks() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_auto_stop_") as tmp:
        cfg = AssistantConfig(workspace=tmp, allow_mutating_tools=True)
        core = AssistantCore(cfg)
        core.tools = StopAwareTools(cfg, core)
        out = core.autonomous_once("investigate logs")
        calls = core.tools.calls  # type: ignore[attr-defined]
        assert calls.count("heartbeat") == 1
        assert "Stop requested; skipped final health check" in out
