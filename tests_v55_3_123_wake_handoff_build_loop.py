from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.config import AssistantConfig
from winlocalassistant.feature_continuity import build_feature_continuity_audit
from winlocalassistant.tools import ToolRegistry
from winlocalassistant.validation_matrix import build_validation_matrix

WEBUI = Path("winlocalassistant/webui.py")
TOOLS = Path("winlocalassistant/tools.py")


def test_version_123_label_mentions_wake_handoff_and_layout():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 123)
    assert f"v{__version__}" in VERSION_LABEL
    assert "wake-listener handoff" in VERSION_LABEL
    assert "hidden-panel layout" in VERSION_LABEL


def test_wake_word_handoff_pauses_always_listener_until_command_finishes():
    src = WEBUI.read_text(encoding="utf-8", errors="replace")
    for marker in [
        "wakeRestartPausedForCommand",
        "finishPostWakeCapture",
        "restartWakeAfterCommand",
        "requestWakeResumeAfterVoiceProcessing",
        "maybeResumeWakeAfterProcessing",
        "voiceRequestInFlight",
        "novaSpeechActive",
        "pendingWakeResumeAfterProcessing",
        "rec.continuous=true",
        "armSilence",
        "Wake accepted. Listening for your request",
        "wake-followup",
    ]:
        assert marker in src
    # The always-on wake listener must not immediately restart over the post-wake command recogniser.
    assert "if(uiSettings.wakeWordEnabled&&!wakeUserStopped&&!wakeCaptureActive&&!wakeRestartPausedForCommand)" in src
    assert "restartWakeAfterCommand(1800)" not in src
    assert "issueVoiceToChat(wakeCandidateText,'wake-followup');requestWakeResumeAfterVoiceProcessing" in src
    assert "setVoiceRequestInFlight(true" in src
    assert "setVoiceRequestInFlight(false" in src
    assert "setNovaSpeechActive(true" in src
    assert "setNovaSpeechActive(false" in src


def test_first_run_wake_capture_allowed_before_voice_profile_exists():
    src = WEBUI.read_text(encoding="utf-8", errors="replace")
    assert "function ensureVoiceProfileForWake()" in src
    assert "if(!profile)" in src
    assert "command execution remains gated" in src
    assert "Wake word heard. Listening for the request" in src


def test_hidden_panels_reclaim_grid_space():
    src = WEBUI.read_text(encoding="utf-8", errors="replace")
    assert "hidden-panel layout reclaim" in src
    assert "body.collapse-left main" in src
    assert "grid-template-columns:0 0 minmax" in src
    assert "body.collapse-left.collapse-right main" in src


def test_voice_board_and_middle_layout_controls_are_regression_protected():
    src = WEBUI.read_text(encoding="utf-8", errors="replace")
    for marker in [
        "voicePipelineState",
        "voiceWakeResumeState",
        "voiceLastCommand",
        "voiceAudioState",
        "diagnoseVoiceInput()",
        "refreshVoiceDeviceSelect()",
        "function toggleControlDrawer",
        "wlaControlDrawerCollapsed",
        "controlDrawerToggle",
        "function setupMiddlePanelResize",
        "wlaMiddlePanelHeights",
        "middleResizeRail",
        "row-resize",
        "role=\"separator\"",
        "aria-valuenow",
        "aria-controls",
        "function resetPanelLayout",
    ]:
        assert marker in src


def test_desktop_voice_launcher_and_noninteractive_batch_start_exist():
    bat = Path("start_windows_assistant.bat").read_text(encoding="utf-8", errors="replace")
    ps1 = Path("start_nova_desktop_voice_listener.ps1").read_text(encoding="utf-8", errors="replace")
    launcher_bat = Path("start_nova_desktop_voice_listener.bat").read_text(encoding="utf-8", errors="replace")
    assert "NOVA_START_CHOICE" in bat
    assert "System.Speech.Recognition" in ps1
    assert "hey nova" in ps1.lower()
    assert "start_windows_assistant.bat" in ps1
    assert "start_nova_desktop_voice_listener.ps1" in launcher_bat


def test_game_runtime_sanity_accepts_rects_hit_collision_helper(tmp_path):
    (tmp_path / "index.html").write_text("<canvas id='game'></canvas><script src='app.js'></script>", encoding="utf-8")
    (tmp_path / "app.js").write_text(
        """
        const player={x:0,y:0,w:10,h:10};
        const target={x:5,y:5,w:10,h:10};
        let score=0;
        function rectsHit(a,b){return a.x<b.x+b.w&&a.x+a.w>b.x&&a.y<b.y+b.h&&a.y+a.h>b.y;}
        function update(){ if(rectsHit(player,target)){ score += 1; } }
        function draw(){}
        requestAnimationFrame(function loop(){ update(); draw(); requestAnimationFrame(loop); });
        document.addEventListener('keydown',()=>{});
        """,
        encoding="utf-8",
    )
    registry = ToolRegistry(AssistantConfig(workspace=str(tmp_path)))
    ok, problems = registry._game_runtime_sanity_check(tmp_path, "make a game for me")
    assert ok, problems


def test_project_repair_loop_guard_is_present():
    src = TOOLS.read_text(encoding="utf-8", errors="replace")
    assert "review_loop_guard" in src
    assert "Accepted verified project without another local-model review loop" in src
    assert "rectshit" in src


def test_feature_continuity_and_validation_matrix_preserve_latest_markers():
    continuity = build_feature_continuity_audit(Path.cwd())
    assert continuity["ok"], continuity.get("failed")
    matrix = build_validation_matrix(Path.cwd(), goal="wake handoff and no-regression")
    assert matrix["ok"], matrix.get("failed")
