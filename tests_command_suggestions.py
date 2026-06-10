from __future__ import annotations

from winlocalassistant.command_suggestions import suggest_next_commands


def _commands(text: str) -> list[str]:
    return [item.command for item in suggest_next_commands(text)]


def test_idle_text_suggests_idle_status_or_once() -> None:
    cmds = _commands("what is idle doing")
    assert "/idle status" in cmds or any(cmd.startswith("/idle once") for cmd in cmds)


def test_error_log_text_suggests_log_investigation() -> None:
    cmds = _commands("there was a traceback in the logs")
    assert any("investigate logs" in cmd for cmd in cmds)


def test_test_verify_text_suggests_test_all_or_test_proposal() -> None:
    cmds = _commands("please verify if it is broken")
    assert "/test-all" in cmds or any("add tests" in cmd for cmd in cmds)


def test_self_improve_text_does_not_suggest_automatic_self_improve() -> None:
    suggestions = suggest_next_commands("improve yourself safely")
    cmds = [item.command.lower() for item in suggestions]
    
    # Check that no dangerous commands are suggested
    disallowed_commands = ["/allow-internet on", "/internet-fetch", "/pip-install", "powershell", "pwsh", "cmd.exe", "/reset-project", "/idle start"]
    for cmd in cmds:
        assert cmd not in disallowed_commands, f"Found disallowed command: {cmd}"
    
    # Ensure that the suggestions include at least one valid command
    assert len(suggestions) > 0
    
    # Verify that when "self-improve" is mentioned, we get appropriate suggestions
    # but not automatic/self-starting commands
    idle_suggestions = [item for item in suggestions if "idle" in item.command.lower()]
    safe_improvement_suggestions = [item for item in suggestions if "safe" in item.command.lower() or "improve" in item.command.lower()]
    
    assert len(idle_suggestions) > 0 or len(safe_improvement_suggestions) > 0, "Should suggest idle-related or safe improvement commands"
    
    # Check that no automatic self-improve commands are suggested
    auto_commands = [item for item in suggestions if item.command.startswith("/idle start") or item.command.startswith("/self-improve")]
    assert len(auto_commands) == 0, "Should not suggest automatic self-improve commands"


def test_manual_self_improve_can_be_marked_high_risk() -> None:
    suggestions = suggest_next_commands("please use self-improve manually for a small guarded fix")
    high = [item for item in suggestions if item.command.startswith("/self-improve")]
    assert high
    assert high[0].risk == "high"


def test_suggestions_limited_to_three_and_no_dangerous_commands() -> None:
    suggestions = suggest_next_commands("idle logs failed test verify tools help self-improve")
    assert len(suggestions) <= 3
    joined = "\n".join(item.command.lower() for item in suggestions)
    for blocked in ["powershell", "pip install", "npm install", "/idle start", "/allow-internet on"]:
        assert blocked not in joined


def test_wla_own_code_review_suggests_source_review_tools() -> None:
    suggestions = suggest_next_commands("please review your own files and Nova coding capabilities")
    commands = [item.command for item in suggestions]
    assert "/codebase-audit" in commands
    assert "/code-review" in commands


def run_all(verbose: bool = False) -> None:
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        fn()
        if verbose:
            print(f"PASS {name}")


if __name__ == "__main__":
    run_all(verbose=True)


def test_gui_problem_suggests_adaptive_gui_checks() -> None:
    suggestions = suggest_next_commands("gui is broken, blank drawer panel in screenshot")
    commands = [item.command for item in suggestions]
    assert "/gui-visual-test" in commands
    assert any("tool-health-map" in cmd for cmd in commands)


def test_media_prompt_suggests_media_pipeline_not_generic_help() -> None:
    commands = _commands("make a video trailer and image storyboard")
    assert "/media-status" in commands
    assert any(cmd.startswith("/image-plan") or cmd.startswith("/video-package") for cmd in commands)


def test_remote_prompt_suggests_remote_preflight_and_health() -> None:
    commands = _commands("remote pc access from my phone and laptop using tailscale")
    assert "/remote-access-test" in commands
    assert "/remote-profile list" in commands
    assert any(cmd.startswith("/remote-api-health") for cmd in commands)


def test_tool_planning_prompt_suggests_tool_aware_routes() -> None:
    commands = _commands("ensure planning is adaptive and not a rigid template when it chooses tools")
    assert any(cmd.startswith("/tool-use-plan") for cmd in commands)
    assert any(cmd.startswith("/pipeline-route") or cmd.startswith("/role-router") for cmd in commands)

def test_reset_project_command_is_disallowed() -> None:
    from winlocalassistant.command_suggestions import _is_disallowed

    assert _is_disallowed("/reset-project")
    assert _is_disallowed("please run /reset-project before continuing")

