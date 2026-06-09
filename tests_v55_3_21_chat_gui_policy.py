from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.sandbox_manager import evaluate_sandbox_command


def test_plain_followup_correction_is_chat_not_self_improvement(tmp_path, monkeypatch):
    cfg = AssistantConfig(workspace=str(tmp_path))
    core = AssistantCore(cfg)
    assert core._looks_like_plain_chat("no attacking people is wrong you should never do it that was a bad example")
    assert core._automatic_mutation_guard_message("no attacking people is wrong you should never do it that was a bad example") == ""


def test_shared_file_context_does_not_make_plain_chat_a_wla_edit(monkeypatch, tmp_path):
    cfg = AssistantConfig(workspace=str(tmp_path))
    core = AssistantCore(cfg)
    monkeypatch.setattr(core, "_with_shared_file_context", lambda text: text + "\n\nUse these user-shared files as context. Nova can pass this image to /image-analyze.")
    monkeypatch.setattr(core, "_answer_plain_chat", lambda text: "plain-chat-ok")
    assert core._chat_locked("no attacking people is wrong you should never do it") == "plain-chat-ok"


def test_live_activity_css_is_bounded_and_flex_layout():
    html = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert ".chat-wrap{display:flex;flex-direction:column" in html
    assert "#chat{flex:1 1 auto;min-height:0}" in html
    assert ".activity{border-top:1px solid var(--line);background:linear-gradient" in html
    assert "max-height:132px" in html
    assert "body.collapse-activity .activity{display:block!important;max-height:38px" in html


def test_security_tool_version_check_allowed_but_target_operation_blocked(tmp_path):
    cfg = AssistantConfig(workspace=str(tmp_path))
    version = evaluate_sandbox_command(cfg, "kali", "nikto -Version")
    assert version["allowed"] is True
    assert any("metadata/version" in w for w in version["warnings"])
    target = evaluate_sandbox_command(cfg, "kali", "nikto -h http://example.com")
    assert target["allowed"] is False
    assert any("authorised Kali lab mode" in r for r in target["reasons"])
