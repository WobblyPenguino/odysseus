from __future__ import annotations

from pathlib import Path
import os

import pytest

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.command_help import command_help_payload, render_concise_help
from winlocalassistant.creation_intent import analyze_creation_request
from winlocalassistant.nova_coding_capabilities import plan_coding_execution
from winlocalassistant.project_request_contract import build_request_contract
from winlocalassistant.release_packager import build_release_package
from winlocalassistant.release_readiness import build_release_readiness, latest_release_readiness_ok
from winlocalassistant.tools import ToolResult


def make_core(tmp_path: Path) -> AssistantCore:
    return AssistantCore(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True, local_model_timeout_sec=0, chat_model_timeout_sec=0))


def test_normal_chat_has_deterministic_fast_fallback(tmp_path: Path):
    core = make_core(tmp_path)
    assert "nova" in core.chat("hi").lower()
    capabilities = core.chat("what can you do?").lower()
    assert "/command-help" in capabilities
    typo_capabilities = core.chat("whzat can you do?").lower()
    assert "/command-help" in typo_capabilities
    fallback = core.local_fallback("explain what you can do")
    assert "model" in fallback.lower() or "nova" in fallback.lower()


def test_timeout_fallback_automatically_reports_model_recovery_status(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    core = make_core(tmp_path)

    def fake_call(name: str, **kwargs):
        assert name == "llm_status"
        return ToolResult(True, "Ollama/local LLM status", {
            "ollama_ps": {"available": True},
            "winlocalassistant_model_lock": {
                "prompt_active": False,
                "cooldown_active": False,
                "last_prompt": {"result": "timeout_or_error"},
            },
            "model_health": {"status": "ready"},
            "stale_ollama_cleanup": {"attempted": False},
        })

    monkeypatch.setattr(core.tools, "call", fake_call)
    fallback = core.local_fallback("sd")

    assert "Automatic model status check" in fallback
    assert "Ollama reachable: True" in fallback
    assert "Nova prompt active: False" in fallback
    assert "/ollama-stop --confirm" in fallback
    assert "without confirmation" in fallback


def test_help_is_concise_full_preserved_and_searchable(tmp_path: Path):
    core = make_core(tmp_path)
    concise = core.handle_command("/help")
    assert "Nova Help Hub" in concise
    assert "/help-full" in concise
    assert len(concise) < 7000
    full = core.handle_command("/help-full")
    assert "/model-doctor" in full
    assert "/nova-eval-packs" in full
    code_help = core.handle_command("/command-help code")
    assert "/code QUESTION" in code_help
    assert "Results:" in code_help
    payload = command_help_payload("release")
    assert any("/release-readiness" in item["command"] for items in payload["categories"].values() for item in items)
    assert "/release-readiness" in render_concise_help()


def test_request_contracts_prevent_wrong_scaffolds():
    py_contract = build_request_contract("make one python file that bolds let")
    assert py_contract["user_asked_for_one_file"] is True
    assert py_contract["language"] == "Python"
    assert py_contract["must_not_create_scaffold"] is True
    assert py_contract["expected_output_files"] == ["script.py"]
    assert plan_coding_execution("make one python file that bolds let")["expected_files"] == ["script.py"]

    game_contract = build_request_contract("make a browser game")
    assert game_contract["language"] == "HTML/CSS/JavaScript"
    assert {"index.html", "style.css", "app.js"}.issubset(set(game_contract["expected_output_files"]))

    ps_contract = build_request_contract("make a PowerShell script")
    assert ps_contract["language"] == "PowerShell"
    assert "script.ps1" in ps_contract["expected_output_files"]
    assert analyze_creation_request("make a PowerShell script")["artifact_type"] == "powershell_automation_script"

    nova_contract = build_request_contract("add a feature to Nova")
    assert nova_contract["target"] == "nova_source_edit"
    assert nova_contract["project_or_script"] == "nova_edit"
    assert nova_contract["must_not_create_scaffold"] is True


@pytest.mark.skipif(os.environ.get("NOVA_RELEASE_READINESS_NESTED") == "1", reason="avoid recursive readiness gate inside readiness gate")
def test_release_readiness_quick_writes_gate_report(tmp_path: Path):
    # Use the actual repo root for a deterministic quick gate.  Browser/full tests
    # are covered separately so unit runs stay fast.
    root = Path(__file__).resolve().parent
    payload = build_release_readiness(root, full=False, include_browser=False)
    assert payload["status"] == "PASS", payload
    assert latest_release_readiness_ok(root)
    assert (root / "docs" / "NOVA_RELEASE_READINESS_LATEST.json").exists()


def test_release_package_blocks_without_passed_gate(tmp_path: Path):
    root = tmp_path / "mini"
    (root / "winlocalassistant").mkdir(parents=True)
    for rel in [
        "app.py",
        "README.md",
        "CHANGELOG.md",
        "start_windows_assistant.bat",
        "winlocalassistant/__init__.py",
        "winlocalassistant/core.py",
        "winlocalassistant/tools.py",
        "winlocalassistant/webui.py",
    ]:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# placeholder\n", encoding="utf-8")
    payload = build_release_package(root, require_readiness=True, out_dir=tmp_path / "out")
    assert not payload["ok"]
    assert "release-readiness" in payload["summary"]


def test_common_plain_prompts_return_useful_answers(tmp_path: Path):
    core = make_core(tmp_path)
    cases = {
        "help": ["/help", "/command-help"],
        "explain your tools": ["slash commands", "/verify"],
        "run a command safely": ["/verify", "python --version"],
        "code me a hello script": ["/code", "/do"],
        "write a file": ["/write", "/do"],
    }
    for prompt, expected_bits in cases.items():
        reply = core.chat(prompt)
        lower = reply.lower()
        assert reply.strip(), prompt
        assert any(bit.lower() in lower for bit in expected_bits), (prompt, reply)


def test_write_read_verify_code_do_routes_remain_useful(tmp_path: Path, monkeypatch):
    import winlocalassistant.core as core_module
    import winlocalassistant.tools as tools_module

    monkeypatch.setattr(core_module, "model_chat", lambda *args, **kwargs: None)
    monkeypatch.setattr(tools_module, "model_chat", lambda *args, **kwargs: None)
    core = make_core(tmp_path)

    write = core.chat("/write notes.txt hello nova")
    assert "notes.txt" in write.lower() or "wrote" in write.lower() or "ok" in write.lower()
    read = core.chat("/read notes.txt")
    assert "notes.txt" in read.lower()
    assert (tmp_path / "notes.txt").read_text(encoding="utf-8") == "hello nova"
    verify = core.chat("/verify python --version")
    assert "verification" in verify.lower() or "python" in verify.lower()
    code = core.chat("/code show a tiny python print example")
    assert code.strip()
    do = core.chat("/do")
    assert "usage" in do.lower() and "/do goal" in do.lower()
