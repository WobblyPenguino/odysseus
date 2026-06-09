from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.config import AssistantConfig
from winlocalassistant.nova_system_test import build_nova_full_system_test, render_nova_full_system_test
from winlocalassistant.tools import ToolRegistry


def test_version_116_markers():
    assert tuple(map(int, __version__.split('.'))) >= (55, 3, 116)
    assert f"v{__version__}" in VERSION_LABEL
    assert "Hey Nova" in VERSION_LABEL


def test_nova_system_test_tool_registered_and_renderable():
    registry = ToolRegistry(AssistantConfig(workspace="."))
    assert "nova_system_test" in registry.tools
    assert "nova_full_test" in registry.tools
    payload = build_nova_full_system_test(Path.cwd(), profile="contract", timeout=10)
    assert payload["steps"]
    names = {step["name"] for step in payload["steps"]}
    assert "intent_normal_chat" in names
    assert "intent_coding_build" in names
    assert "deterministic_coding_fallback" in names
    md = render_nova_full_system_test(payload)
    assert "One-by-one capability results" in md
    assert "Manual follow-up" in md


def test_gui_exposes_nova_full_system_button():
    src = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "/nova-system-test" in src
    assert "Nova full test" in src or "Nova full system test" in src
    assert 'data-ui-overhaul="v55.3.115"' in src  # preserve legacy UI regression marker
    assert f"v{__version__}" in src  # current version visible for continuity audit


def test_core_routes_nova_full_system_command():
    src = Path("winlocalassistant/core.py").read_text(encoding="utf-8")
    assert "/nova-system-test" in src
    assert "nova_system_test" in src


def test_feature_continuity_knows_nova_system_test():
    src = Path("winlocalassistant/feature_continuity.py").read_text(encoding="utf-8")
    assert "nova_full_system_test" in src
    assert "nova_system_test" in src
