from __future__ import annotations

import tempfile
from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant import config as config_mod
from winlocalassistant.core import AssistantCore
from winlocalassistant.command_verifier import default_command_contracts
from winlocalassistant.model_health import assess_model_dependency, render_model_health_markdown


def test_model_health_reports_ollama_unavailable() -> None:
    cfg = AssistantConfig(workspace=".", model="qwen2.5-coder:7b")
    report = assess_model_dependency(cfg, ollama_ps={"available": False, "error": "missing"}, busy_state={})
    assert not report.ok
    assert report.status == "degraded"
    assert any("Ollama" in issue for issue in report.issues)
    text = render_model_health_markdown(report)
    assert "# Model Health" in text
    assert "ollama serve" in text


def test_model_health_reports_openrouter_without_internet() -> None:
    cfg = AssistantConfig(workspace=".", model_provider="openrouter", allow_internet=False)
    report = assess_model_dependency(cfg, ollama_ps=None, busy_state={})
    assert not report.ok
    assert any("internet access is disabled" in issue.lower() for issue in report.issues)


def test_model_health_reports_prompt_active() -> None:
    cfg = AssistantConfig(workspace=".")
    report = assess_model_dependency(cfg, ollama_ps={"available": True, "active_models": []}, busy_state={"prompt_active": True})
    assert not report.ok
    assert report.prompt_active is True
    assert any("prompt is currently active" in issue for issue in report.issues)


def test_command_timeout_command_status_and_set() -> None:
    old_config = config_mod.CONFIG_PATH.read_text(encoding="utf-8") if config_mod.CONFIG_PATH.exists() else None
    with tempfile.TemporaryDirectory(prefix="wla_cmd_timeout_") as tmp:
        try:
            core = AssistantCore(AssistantConfig(workspace=tmp, command_timeout_sec=120))
            assert "120" in core.chat("/command-timeout status")
            out = core.chat("/command-timeout 7")
            assert "7 seconds" in out
            assert core.config.command_timeout_sec == 7
            assert "Usage" in core.chat("/command-timeout banana")
        finally:
            if old_config is None:
                config_mod.CONFIG_PATH.unlink(missing_ok=True)
            else:
                config_mod.CONFIG_PATH.write_text(old_config, encoding="utf-8")


def test_model_health_command_returns_markdown() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_model_health_") as tmp:
        core = AssistantCore(AssistantConfig(workspace=tmp))
        out = core.chat("/model-health")
        assert "# Model Health" in out
        assert "Provider" in out
        assert "Recommendations" in out


def test_command_contracts_include_model_health_and_command_timeout() -> None:
    commands = {contract.command for contract in default_command_contracts()}
    assert "/model-health" in commands
    assert "/command-timeout status" in commands


def test_ollama_preflight_stops_only_stopping_selected_model() -> None:
    import winlocalassistant.ollama as om

    calls: list[list[str]] = []
    old_which = om.shutil.which
    old_run = om.subprocess.run

    class Proc:
        def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    def fake_which(name: str) -> str:
        return "ollama.exe" if name == "ollama" else ""

    def fake_run(args, **kwargs):
        calls.append(list(args))
        if args == ["ollama.exe", "ps"]:
            return Proc(stdout="qwen2.5-coder:7b abc 5 GB CPU 4096 Stopping...\n")
        if args == ["ollama.exe", "stop", "qwen2.5-coder:7b"]:
            return Proc(stdout="stopped")
        raise AssertionError(args)

    try:
        om.shutil.which = fake_which
        om.subprocess.run = fake_run
        om._try_stop_stopping_model("qwen2.5-coder:7b")
    finally:
        om.shutil.which = old_which
        om.subprocess.run = old_run

    assert ["ollama.exe", "ps"] in calls
    assert ["ollama.exe", "stop", "qwen2.5-coder:7b"] in calls


def run_all(verbose: bool = False) -> None:
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        fn()
        if verbose:
            print(f"PASS {name}")


if __name__ == "__main__":
    run_all(verbose=True)
