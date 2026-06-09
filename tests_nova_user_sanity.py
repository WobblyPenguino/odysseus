from __future__ import annotations

import subprocess
import sys

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore


def _require_contains(name: str, text: str, expected: list[str]) -> None:
    lower = text.lower()
    assert text.strip(), f"{name} returned empty output"
    assert any(bit.lower() in lower for bit in expected), (
        f"{name} missing expected markers {expected!r}; got: {text[:500]!r}"
    )


def test_nova_user_facing_core_commands_remain_useful_without_live_model(tmp_path, monkeypatch) -> None:
    import winlocalassistant.core as core_module
    import winlocalassistant.tools as tools_module

    monkeypatch.setattr(core_module, "model_chat", lambda *args, **kwargs: None)
    monkeypatch.setattr(tools_module, "model_chat", lambda *args, **kwargs: None)

    cfg = AssistantConfig(
        workspace=str(tmp_path),
        allow_mutating_tools=True,
        allow_internet=False,
        local_model_timeout_sec=0,
        chat_model_timeout_sec=0,
        command_timeout_sec=10,
    )
    core = AssistantCore(cfg)

    _require_contains("plain chat", core.chat("hi"), ["nova", "help", "command"])
    _require_contains("/help", core.handle_command("/help"), ["nova help", "/help-full", "/command-help"])
    _require_contains("/help-full", core.handle_command("/help-full"), ["/write", "/read", "/verify", "/code"])
    _require_contains("/command-help code", core.handle_command("/command-help code"), ["/code"])
    _require_contains("/model-health", core.handle_command("/model-health"), ["model health", "provider"])
    _require_contains("/command-timeout status", core.handle_command("/command-timeout status"), ["timeout", "seconds"])
    _require_contains("/command-verify", core.chat("/command-verify"), ["nova command verification", "passed"])

    _require_contains("/write", core.chat("/write notes.txt hello nova"), ["notes.txt", "wrote", "ok"])
    _require_contains("/read", core.chat("/read notes.txt"), ["notes.txt", "hello nova"])
    _require_contains("/verify", core.chat("/verify python --version"), ["verification", "python"])

    # With model_chat mocked to None, /code should not pretend it generated code.
    # It should return Nova's safe fallback and tell the user how to use /code.
    _require_contains("/code fallback", core.chat("/code show a tiny python print example"), ["safe fallback", "/code question", "ollama"])

    _require_contains("/do usage", core.chat("/do"), ["usage", "/do", "goal"])


def test_nova_validate_module_help_runs() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "nova.validate", "--help"],
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "usage" in result.stdout.lower() or "usage" in result.stderr.lower()
