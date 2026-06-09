from pathlib import Path

from winlocalassistant.planner import make_plan

ROOT = Path(__file__).resolve().parent
WEBUI = (ROOT / "winlocalassistant" / "webui.py").read_text(encoding="utf-8")


def test_project_library_review_request_is_not_new_project_generation() -> None:
    plan = make_plan("all our projects and identify the projects that need improvements and then make the improvements")
    tools = [step.tool for step in plan.steps]
    assert plan.mode == "project_library_review"
    assert "ai_create_project" not in tools
    assert "projects" in tools
    assert "regression_sweep" in tools
    assert "bug_review" in tools


def test_functionality_validation_followup_routes_to_qa_not_generation() -> None:
    plan = make_plan("and test each individual functionality to ensure it works and once you ensure it works validate the results and display them")
    tools = [step.tool for step in plan.steps]
    assert plan.mode in {"qa", "project_qa"}
    assert "ai_create_project" not in tools
    assert any(tool in tools for tool in ["regression_sweep", "bug_review", "release_hygiene", "user_test_suite", "final_project_check"])


def test_orbit_live_activity_and_terminal_evidence_markers_are_present() -> None:
    assert "v55.3.144 readability and evidence indicators" in WEBUI
    assert "messageTerminalHtml" in WEBUI
    assert "msgTime" in WEBUI
    assert "msgTerminal" in WEBUI
    assert "toggleOrbitActivity(true)" in WEBUI
    assert "Still working. Polling live activity and active run" in WEBUI
    assert "Checking active run, Live Activity and autonomous status" in WEBUI


def test_voice_ready_cue_and_spoken_summary_are_less_noisy() -> None:
    assert "novaReadyCue" in WEBUI
    assert "Ready cue played. Start speaking now." in WEBUI
    assert "Ready cue could not play until browser audio is unlocked" in WEBUI
    assert "The local model did not return usable output" in WEBUI
    assert "Check Live Activity for details." in WEBUI
    assert "redacted.push('Long technical details available on screen.');" in WEBUI


def test_subchat_transcript_spam_is_hidden_but_voice_trace_remains() -> None:
    assert "#orbitSubChat{display:none!important}" in WEBUI
    assert "ignoreKinds" in WEBUI
    assert "live transcript" in WEBUI
    assert "Live communication trace" in WEBUI


def test_current_cache_and_launcher_markers_are_updated() -> None:
    assert "nova-orbit-shell-v55-3-147" in WEBUI
    assert "nova_ui=v55.3.147" in (ROOT / "start_windows_assistant.bat").read_text(encoding="utf-8")
