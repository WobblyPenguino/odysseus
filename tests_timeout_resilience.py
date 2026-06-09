from __future__ import annotations

import subprocess
import tempfile

from winlocalassistant.config import AssistantConfig
from winlocalassistant.tools import ToolRegistry
import winlocalassistant.tools as tools_module
from winlocalassistant.autonomous_failure import classify_autonomous_failure


def test_run_shell_timeout_returns_structured_failure() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_timeout_") as tmp:
        registry = ToolRegistry(AssistantConfig(workspace=tmp, allow_mutating_tools=True, command_timeout_sec=1))
        old_which = tools_module.shutil.which
        old_run = tools_module.subprocess.run
        try:
            tools_module.shutil.which = lambda name: "powershell" if name in {"powershell", "pwsh"} else None

            def fake_run(*args, **kwargs):
                raise subprocess.TimeoutExpired(cmd="fake", timeout=1, output="partial stdout", stderr="partial stderr")

            tools_module.subprocess.run = fake_run
            result = registry.run_shell("Start-Sleep -Seconds 99", timeout=1)
        finally:
            tools_module.shutil.which = old_which
            tools_module.subprocess.run = old_run

        assert result.ok is False
        assert "timed out" in result.summary.lower()
        assert result.data["timed_out"] is True
        assert result.data["timeout_sec"] == 1
        assert "partial stdout" in result.data["output"]
        assert "partial stderr" in result.data["output"]
        assert "do not retry" in result.data["advice"].lower()


def test_timeout_result_classifies_as_autonomous_timeout() -> None:
    category = classify_autonomous_failure(
        result_text="Command timed out after 1 seconds",
        error_text='{"timed_out": true, "advice": "do not retry blindly"}',
        timed_out=True,
    )
    assert category == "timeout"


def run_all() -> None:
    test_run_shell_timeout_returns_structured_failure()
    test_timeout_result_classifies_as_autonomous_timeout()
