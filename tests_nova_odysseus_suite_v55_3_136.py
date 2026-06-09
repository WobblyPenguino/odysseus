from __future__ import annotations

from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.nova_odysseus_suite import (
    build_suite_status,
    classify_action,
    detect_hardware,
    recommend_models,
)


def test_odysseus_suite_reports_full_feature_coverage(tmp_path: Path) -> None:
    payload = build_suite_status(tmp_path)
    assert payload["ok"] is True
    assert payload["coverage"]["covered"] == payload["coverage"]["total"]
    commands = payload["primary_commands"]
    assert "/nova-cookbook" in commands
    assert "/nova-tool-permissions" in commands
    assert "/nova-odysseus-runtime" in commands
    assert any(f["id"] == "compare" and f["status"] == "implemented" for f in payload["features"])


def test_tool_permission_classifier_admin_gates_risky_actions(tmp_path: Path) -> None:
    payload = classify_action(tmp_path, "write a file and send email")
    assert payload["decision"] == "admin"
    assert payload["requires_confirmation"] is True
    tools = {item["tool"] for item in payload["matched_surfaces"]}
    assert "write_file" in tools
    assert "email" in tools


def test_cookbook_whatif_ranks_coding_model_for_16gb_vram() -> None:
    hardware = detect_hardware("ram=32 vram=16 gpu=RTX 5070 Ti")
    payload = recommend_models(hardware, "coding")
    names = [m["name"] for m in payload["models"]]
    assert any("coder" in name for name in names[:3])
    assert payload["hardware"]["vram_gb"] == 16.0


def test_core_routes_odysseus_suite_commands(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "winlocalassistant").mkdir()
    (tmp_path / "docs").mkdir()
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path)))

    suite = core.handle_command("/nova-odysseus-suite")
    assert "Nova Odysseus Feature Suite" in suite
    assert "Coverage: **16/16**" in suite

    runtime = core.handle_command("/nova-odysseus-runtime")
    assert "Nova Odysseus Runtime" in runtime
    assert "State:" in runtime

    policy = core.handle_command("/nova-tool-permissions check write file")
    assert "Decision: **admin**" in policy

    cookbook = core.handle_command("/nova-cookbook whatif ram=32 vram=16 => coding")
    assert "Nova Model Cookbook" in cookbook
    assert "coder" in cookbook.lower()

    compare = core.handle_command("/nova-compare plan Improve Nova => qwen2.5-coder:7b, qwen2.5:14b")
    assert "Nova Blind Model Compare" in compare
    assert "Comparison ID" in compare

    doc = core.handle_command("/nova-docs new Test => # Test")
    assert "Nova Documents" in doc
    assert "test" in doc.lower()

    notes = core.handle_command("/nova-notes add remember this")
    assert "Nova Notes" in notes
    assert "Saved" in notes

    task = core.handle_command("/nova-tasks add verify Nova")
    assert "Nova Tasks" in task
    assert "Saved" in task

    skill = core.handle_command("/nova-skills add debugger => Always run tests")
    assert "Nova Skills" in skill
    assert "Saved" in skill

    preset = core.handle_command("/nova-presets add careful => Be precise")
    assert "Nova Presets" in preset
    assert "Saved" in preset

    vault = core.handle_command("/nova-memory-vault audit")
    assert "Nova Memory Vault" in vault

    gates = core.handle_command("/nova-integration-gates")
    assert "Nova Integration Gates" in gates

    scaffold = core.handle_command("/nova-email-plan")
    assert "Nova Odysseus Integration Scaffold" in scaffold
