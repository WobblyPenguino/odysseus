from pathlib import Path

from winlocalassistant.planner import make_plan
from winlocalassistant.tools import ToolRegistry
from winlocalassistant.config import AssistantConfig

ROOT = Path(__file__).resolve().parent
WEBUI = (ROOT / "winlocalassistant" / "webui.py").read_text(encoding="utf-8")
TOOLS = (ROOT / "winlocalassistant" / "tools.py").read_text(encoding="utf-8")


def test_orbit_shell_loads_without_legacy_flash_and_cache_regression():
    assert '<body class="nova-orbit-shell">' in WEBUI
    assert "nova-orbit-shell-v55-3-147" in WEBUI
    assert "fetch(req, {cache:'no-store'})" in WEBUI
    assert "must-revalidate" in WEBUI
    assert "nova_ui=v55.3.147" in (ROOT / "start_windows_assistant.bat").read_text(encoding="utf-8")


def test_command_ready_artifact_removed_and_state_pill_present():
    assert "Command ready</b>" not in WEBUI
    assert "orbitStatePill" in WEBUI
    assert "orbitStateLabel" in WEBUI
    assert "command filled" in WEBUI


def test_chat_drawer_has_mute_edit_delete_controls():
    assert "renderLocalChatDrawer" in WEBUI
    assert "toggleChatMuteById" in WEBUI
    assert "renameLocalChatSession" in WEBUI
    assert "deleteLocalChatSession" in WEBUI
    assert "editLocalChatSession" in WEBUI


def test_voice_challenge_and_concise_speech_guards_exist():
    assert "generateVoiceChallengePhrase" in WEBUI
    assert "guardAdminVoiceForCommand" in WEBUI
    assert "Different voice detected" in WEBUI
    assert "autoSpeakVoiceMode:false" in WEBUI
    assert "Done. The checks passed." in WEBUI


def test_voice_state_speech_voice_helpers_are_defined_before_startup_use():
    helpers = [
        "function populateSpeechVoices",
        "function saveSpeechVoiceChoice",
        "function selectedSpeechVoice",
        "function preferredSpeechVoice",
        "function speakText",
        "function testSpeechOutput",
    ]
    for helper in helpers:
        assert helper in WEBUI
    assert WEBUI.index("function populateSpeechVoices") < WEBUI.index("safeApplyUiSettings();populateSpecChoices();renderVoiceAuth();populateSpeechVoices();")


def test_orbit_inline_gui_handlers_have_function_wrappers():
    for helper in [
        "function showMainTab",
        "function toggleTopbar",
        "function loadSandboxStatus",
        "function loadDockerStatus",
        "function sandboxStart",
        "function sandboxStop",
        "function sandboxExec",
    ]:
        assert helper in WEBUI


def test_odysseus_style_file_window_markers_exist():
    assert "orbitFileWindow" in WEBUI
    assert "startOrbitWindowDrag" in WEBUI
    assert "openFileWorkspaceWindow" in WEBUI
    assert "runOpenFileFromWindow" in WEBUI


def test_current_project_test_followup_routes_to_project_qa_not_create():
    plan = make_plan("and test each individual functionality to ensure it works and once you ensure it works validate the results and display them")
    assert plan.mode == "project_qa"
    assert "ai_create_project" not in [s.tool for s in plan.steps]
    assert [s.tool for s in plan.steps] == ["user_test_suite", "regression_sweep", "bug_review", "nova_doctor"]


def test_string_search_script_fallback_is_domain_specific(tmp_path):
    cfg = AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True)
    registry = ToolRegistry(cfg)
    fallback = registry._fallback_project_for_goal("make a script that looks for a certain string inside any file type", "create")
    assert fallback is not None
    assert fallback["main_file"] == "file_string_search.py"
    code = fallback["files"]["file_string_search.py"].lower()
    assert "search for a string" in code
    assert "rglob" in code
    assert "read_bytes" in code
    assert "--json" in code
