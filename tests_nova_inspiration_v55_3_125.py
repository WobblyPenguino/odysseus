from __future__ import annotations

from winlocalassistant.core import AssistantCore
from winlocalassistant.nova_inspiration_engine import (
    build_handoff_plan,
    build_improvement_preflight,
    build_nova_inspiration_radar,
    build_tool_context_pack,
)


def test_tool_context_pack_prioritises_prompt_relevant_tools() -> None:
    tools = {"voice_audit", "feature_continuity_audit", "regression_sweep", "status", "command_catalog", "analytics"}
    payload = build_tool_context_pack("improve voice without regression", tools, max_tools=8)
    selected = set(payload["selected_tool_names"])
    assert "voice_audit" in selected
    assert "feature_continuity_audit" in selected
    assert "regression_sweep" in selected
    assert "no tool is executed" in payload["policy"].lower()


def test_handoff_plan_contains_verifier_and_reporter() -> None:
    payload = build_handoff_plan("fix GUI and verify no regression", {"command_catalog", "tool_context_pack", "regression_sweep", "release_package"})
    names = [step["name"] for step in payload["steps"]]
    assert "Verifier" in names
    assert "Reporter" in names
    assert "deterministic handoff plan" in payload["policy"]


def test_improvement_preflight_flags_protected_files() -> None:
    payload = build_improvement_preflight(
        "add inspiration workflow helpers",
        changed_files=["winlocalassistant/tools.py", "tests_nova_inspiration_v55_3_125.py"],
        intended_commands=["/status"],
    )
    assert payload["risk"] == "high"
    assert any(finding["item"] == "winlocalassistant/tools.py" for finding in payload["findings"])
    assert any("tests_nova_inspiration_v55_3_125.py" in command for command in payload["validation_plan"])


def test_inspiration_radar_reports_implemented_commands(tmp_path) -> None:
    (tmp_path / "AGENTS.md").write_text("rules", encoding="utf-8")
    (tmp_path / "tests_smoke.py").write_text("print('ok')", encoding="utf-8")
    payload = build_nova_inspiration_radar(
        tmp_path,
        {"tool_context_pack", "handoff_plan", "improvement_preflight", "inspiration_radar", "analytics"},
        focus="workflow",
    )
    assert "tool_context_pack" in payload["available_inspired_commands"]
    assert payload["ideas"][0]["implemented_now"].startswith("/")
    assert payload["snapshot"]["files"]["agents_md"] is True


def test_registry_inspiration_commands_return_markdown() -> None:
    core = AssistantCore.load()
    checks = {
        "inspiration_radar": (dict(focus="voice"), "Nova Inspiration Radar"),
        "tool_context_pack": (dict(prompt="improve voice without regression"), "Nova Tool Context Pack"),
        "handoff_plan": (dict(prompt="improve GUI and verify"), "Nova Handoff Plan"),
        "improvement_preflight": (dict(goal="add inspiration tools", files="winlocalassistant/tools.py"), "Nova Improvement Preflight"),
    }
    for command, (kwargs, marker) in checks.items():
        result = core.tools.call(command, **kwargs)
        assert result.ok, f"{command} failed: {result.summary}"
        assert marker in str((result.data or {}).get("message", ""))


def test_core_chat_routes_new_inspiration_slash_commands() -> None:
    core = AssistantCore.load()
    assert "Nova Inspiration Radar" in core.chat("/inspiration-radar workflow")
    assert "Nova Tool Context Pack" in core.chat("/tool-context-pack improve voice")
    assert "Nova Handoff Plan" in core.chat("/handoff-plan improve GUI")
    assert "Nova Improvement Preflight" in core.chat("/improvement-preflight add tool => winlocalassistant/tools.py")


def run_all(verbose: bool = False) -> None:
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            if name == "test_inspiration_radar_reports_implemented_commands":
                # tmp_path is provided by pytest; direct smoke covers command-level behaviour below.
                continue
            fn()
            if verbose:
                print(f"PASS {name}")


if __name__ == "__main__":
    run_all(True)
