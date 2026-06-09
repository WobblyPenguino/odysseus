from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.completion_audit import build_completion_audit, render_completion_audit
from winlocalassistant.config import AssistantConfig
from winlocalassistant.system_test import TEST_GROUPS, run_massive_system_test
from winlocalassistant.tools import ToolRegistry


def test_version_117_completion_label_preserves_voice_and_nova():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 117)
    assert f"v{__version__}" in VERSION_LABEL
    assert "completion audit" in VERSION_LABEL
    assert "Hey Nova" in VERSION_LABEL or "voice activation" in VERSION_LABEL


def test_completion_audit_passes_and_mentions_previous_tasks():
    payload = build_completion_audit(Path.cwd(), profile="quick")
    assert payload["ok"], payload.get("failed")
    names = {c["name"] for c in payload["checks"]}
    assert "nova_command_routing" in names
    assert "nova_gui_button_and_palette" in names
    assert "batch_startup_and_one_button_flow" in names
    assert "massive_test_includes_latest_nova_patch" in names
    md = render_completion_audit(payload)
    assert "Previous Task Completion Audit" in md
    assert "no-regression" in md or "no regression" in md


def test_completion_audit_tool_registered_and_command_routed():
    registry = ToolRegistry(AssistantConfig(workspace="."))
    assert "completion_audit" in registry.tools
    assert "previous_task_audit" in registry.tools
    assert "task_completion_audit" in registry.tools
    core = Path("winlocalassistant/core.py").read_text(encoding="utf-8")
    assert "/completion-audit" in core
    assert "previous-task-audit" in core
    assert "completion_audit" in core


def test_gui_exposes_completion_audit_button_and_keeps_legacy_marker():
    src = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "/completion-audit" in src
    assert "Completion audit" in src
    # Older v55.3.100-v116 GUI tests use this marker, so keep it intentionally.
    assert 'data-ui-overhaul="v55.3.115"' in src


def test_massive_system_test_covers_latest_nova_and_completion_without_running_full_suite():
    flat = [name for group in TEST_GROUPS for name in group]
    assert "tests_v55_3_117_completion_hardening.py" in flat
    assert "tests_v55_3_116_nova_full_system_test.py" in flat
    src = Path("winlocalassistant/system_test.py").read_text(encoding="utf-8")
    assert "build_nova_full_system_test" in src
    assert "nova_full_system_contract" in src
    assert "previous_task_completion_audit" in src


def test_massive_system_test_render_includes_new_steps_when_deps_are_stubbed(monkeypatch):
    import winlocalassistant.system_test as system_test

    monkeypatch.setattr(system_test, "build_dependency_report", lambda: {"python_ok": True, "missing_required": []})
    monkeypatch.setattr(system_test, "run_wla_doctor", lambda root, goal: {"ok": True, "summary": "doctor ok", "markdown_path": "doctor.md"})
    monkeypatch.setattr(system_test, "build_feature_audit", lambda root: {"ok": True, "summary": "features ok", "markdown_path": "features.md"})
    monkeypatch.setattr(system_test, "build_nova_full_system_test", lambda root, profile="contract", timeout=45: {"ok": True, "summary": "nova ok", "failed": [], "categories": {}})
    monkeypatch.setattr(system_test, "build_completion_audit", lambda root, profile="quick": {"ok": True, "summary": "completion ok", "failed": [], "categories": {}})
    monkeypatch.setattr(system_test, "_run", lambda name, args, cwd, timeout=240: {"name": name, "ok": True, "summary": "stubbed", "command": args})
    monkeypatch.setattr(system_test.shutil, "which", lambda name: None)

    payload = run_massive_system_test(Path.cwd(), include_docker=False, include_playwright=False)
    step_names = [s["name"] for s in payload["steps"]]
    assert "nova_full_system_contract" in step_names
    assert "previous_task_completion_audit" in step_names
    assert payload["ok"]
