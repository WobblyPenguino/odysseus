from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent


def test_legacy_continuity_audit_passes_current_tree():
    from winlocalassistant.legacy_continuity import build_legacy_continuity_audit
    payload = build_legacy_continuity_audit(ROOT)
    assert payload["ok"] is True
    assert payload["anchor_count"] >= 8
    ids = {a["id"] for a in payload["anchors"]}
    for required in {
        "odysseus_voyage_deck",
        "voice_wake_reliability",
        "pipeline_observability",
        "provider_runtime",
        "remote_scheduler_validation",
        "emergency_chat_help_layout",
    }:
        assert required in ids


def test_legacy_continuity_markdown_mentions_regression_lock():
    from winlocalassistant.legacy_continuity import build_legacy_continuity_audit, render_legacy_continuity_audit
    md = render_legacy_continuity_audit(build_legacy_continuity_audit(ROOT))
    assert "Nova Legacy Continuity Audit" in md
    assert "Regression lock instructions" in md
    assert "Pipeline routing" in md
    assert "Hey Nova" in md


def test_legacy_continuity_command_routes_through_core(tmp_path, monkeypatch):
    from winlocalassistant.core import AssistantCore
    from winlocalassistant.config import AssistantConfig
    cfg = AssistantConfig.load()
    cfg.workspace = str(ROOT)
    core = AssistantCore(cfg)
    out = core.handle_command("/legacy-continuity-audit")
    assert "Nova Legacy Continuity Audit" in out
    assert "Status: **PASS**" in out


def test_write_legacy_contract(tmp_path):
    from winlocalassistant.legacy_continuity import write_legacy_contract
    out = write_legacy_contract(ROOT)
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert "anchor_count" in text


def test_build_identity_tracks_legacy_patch():
    from winlocalassistant.build_info import PATCH_ID, SERVICE_WORKER_CACHE, LAYOUT_STORAGE_VERSION, build_patch_identity
    payload = build_patch_identity(ROOT)
    assert PATCH_ID == "project-state-continuity-memory-v1"
    assert SERVICE_WORKER_CACHE == "nova-orbit-shell-v55-3-168-project-state-v1"
    assert LAYOUT_STORAGE_VERSION == "v55.3.168-project-state-v1"
    assert payload["patch_id"] == PATCH_ID
