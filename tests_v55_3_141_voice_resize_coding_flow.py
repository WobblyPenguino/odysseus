from pathlib import Path

from winlocalassistant import VERSION_LABEL, __version__
from winlocalassistant.planner import make_plan
from winlocalassistant.webui import HTML


def test_v55_3_141_version_metadata_and_docs_are_current():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 141)
    assert "Voice cue" in VERSION_LABEL
    assert "Voice cue" in VERSION_LABEL or "voice cue" in VERSION_LABEL.lower()
    assert "v55.3.141" in Path("CHANGELOG.md").read_text(encoding="utf-8")
    assert "Nova_v55_3_141_voice_resize_coding_flow_20260602.zip" in Path("README.md").read_text(encoding="utf-8")


def test_wake_ready_cue_and_processing_pause_are_wired():
    assert "function novaReadyCue()" in HTML
    assert "novaReadyCue();" in HTML
    assert "Hey Nova wake cue played" in HTML
    assert "function pauseWakeUntilProcessingDone" in HTML
    assert "pauseWakeUntilProcessingDone('Chat request running.')" in HTML
    assert "setVoiceRequestInFlight(true,'Chat request is running; wake listener paused.')" in HTML
    assert "Wake listener paused until the reply is finished" in HTML
    assert "err==='no-speech'" in HTML
    assert "Wake listener ready. Say “Hey Nova”." in HTML


def test_middle_resize_targets_cover_banner_workspace_and_activity():
    assert "validationCommandDock" in HTML
    assert "function middleResizeTargets()" in HTML
    for marker in ["topbar", "odysseusVoyageDeck", "validationCommandDock", "smartTopStrip", "chatTabs", "liveActivityPanel"]:
        assert marker in HTML
    assert "setupMiddlePanelResize()" in HTML
    assert "Resize chat and live activity split" in HTML
    assert "resize panel" in HTML


def test_live_activity_refresh_preserves_manual_scroll():
    assert "const previousTop=box.scrollTop||0" in HTML
    assert "const userReviewing=previousTop>24" in HTML
    assert "box.scrollTop=Math.min(box.scrollHeight, previousTop+delta)" in HTML
    assert "fetch('/api/activity?since=0',{cache:'no-store'})" in HTML


def test_functionality_test_request_routes_to_qa_tools_not_project_generation():
    plan = make_plan("a test to test all of your functionality")
    assert plan.mode == "qa"
    tools = [step.tool for step in plan.steps]
    assert "ai_create_project" not in tools
    assert tools == ["user_test_suite", "regression_sweep", "bug_review", "nova_doctor"]


def test_coding_fallback_hardening_markers_exist():
    tools = Path("winlocalassistant/tools.py").read_text(encoding="utf-8")
    assert "_should_use_early_deterministic_project_fallback" in tools
    assert "_try_early_project_fallback" in tools
    assert "llm_early_fallback_used" in tools
    assert "v55.3.141 accepted deterministic verification for a simple app/game" in tools


def test_manual_feedback_test_command_exists():
    core = Path("winlocalassistant/core.py").read_text(encoding="utf-8")
    assert "/user-feedback-tests" in core
    assert "/full-functionality-test-commands" in core
    assert "Nova manual user-feedback test commands" in core


def test_one_shot_non_slash_cli_uses_core_chat_not_removed_method():
    main_py = Path("winlocalassistant/main.py").read_text(encoding="utf-8")
    assert "core.chat(command)" in main_py
    assert "handle_user_message" not in main_py


def test_qa_plan_does_not_show_created_file_footer():
    core = Path("winlocalassistant/core.py").read_text(encoding="utf-8")
    assert 'self.last_plan.mode == "qa"' in core
    assert 'QA run complete. No project files were created' in core
    assert 'project_output_mode and final_run_path' in core
