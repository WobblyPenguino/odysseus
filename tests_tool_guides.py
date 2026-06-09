from __future__ import annotations

import tempfile
from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.tools import ToolRegistry
from winlocalassistant.tool_guides import get_autonomous_tool_use_summary, get_local_model_tool_use_summary


def test_local_model_guide_file_contains_required_sections() -> None:
    text = Path("docs/NOVA_LOCAL_MODEL_TOOL_USE_GUIDE.md").read_text(encoding="utf-8")
    low = text.lower()
    for level in ["level 0", "level 1", "level 2", "level 3", "level 4", "level 5"]:
        assert level in low
    assert "verification ladder" in low
    assert "surgical fallback" in low
    assert "custom tool" in low


def test_autonomous_guide_file_contains_stop_and_repeated_failure_rules() -> None:
    text = Path("docs/NOVA_AUTONOMOUS_TOOL_USE_GUIDE.md").read_text(encoding="utf-8").lower()
    assert "repeated failed action" in text or "same signature fails" in text
    assert "verification ladder" in text
    assert "local-model repair" in text
    assert "stop conditions" in text


def test_tool_guide_returns_useful_text_without_writing_workspace_file() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_toolguide_") as tmp:
        registry = ToolRegistry(AssistantConfig(workspace=tmp, allow_mutating_tools=True))
        result = registry.tool_use_guide()
        assert result.ok
        assert "Nova identity" in result.data["content"]
        assert "verification" in result.data["content"].lower()
        assert result.data["mutating"] is False
        assert not (Path(tmp) / "TOOL_USE_GUIDE.md").exists()


def test_summary_helpers_contain_identity_verification_fallback_stop() -> None:
    joined = get_autonomous_tool_use_summary() + "\n" + get_local_model_tool_use_summary()
    low = joined.lower()
    assert "winlocalassistant" in low
    assert "verification" in low
    assert "fallback" in low or "repair" in low
    assert "stop conditions" in low


def run_all(verbose: bool = False) -> None:
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        fn()
        if verbose:
            print(f"PASS {name}")


if __name__ == "__main__":
    run_all(verbose=True)
