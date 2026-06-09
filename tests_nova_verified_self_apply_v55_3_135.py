from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.nova_verified_changes import (
    build_verified_change_plan,
    preview_verified_change,
    apply_verified_change,
)


def _core(tmp_path: Path) -> AssistantCore:
    cfg = AssistantConfig(workspace=str(tmp_path))
    return AssistantCore(cfg)


def test_verified_change_plan_lists_odysseus_changeset(tmp_path: Path):
    plan = build_verified_change_plan(tmp_path)
    assert plan["ok"] is True
    ids = {item["id"] for item in plan["available_changesets"]}
    assert "odysseus-adaptation-report" in ids
    assert "verified-self-change-flow" in ids


def test_verified_change_preview_is_read_only_and_safe(tmp_path: Path):
    payload = preview_verified_change(tmp_path, "odysseus-adaptation-report")
    assert payload["ok"] is True
    assert payload["mode"] == "preview"
    assert not (tmp_path / "docs" / "NOVA_ODYSSEUS_ADAPTATION_PLAN.md").exists()
    assert "diff" in payload["diffs"][0]


def test_verified_change_requires_confirmation(tmp_path: Path):
    payload = apply_verified_change(tmp_path, "verified-self-change-flow", confirm=False)
    assert payload["ok"] is False
    assert payload["status"] == "confirmation_required"
    assert not (tmp_path / "docs" / "NOVA_VERIFIED_SELF_CHANGE_FLOW.md").exists()


def test_command_routes_verified_self_apply_plan(tmp_path: Path):
    core = _core(tmp_path)
    text = core.handle_command("/nova-self-apply plan")
    assert "Nova Verified Self-Apply" in text
    assert "odysseus-adaptation-report" in text


def test_command_routes_verified_self_apply_preview(tmp_path: Path):
    core = _core(tmp_path)
    text = core.handle_command("/nova-self-apply preview odysseus-adaptation-report")
    assert "Mode: **preview**" in text
    assert "NOVA_ODYSSEUS_ADAPTATION_PLAN.md" in text
    assert "Safety: PASS" in text
