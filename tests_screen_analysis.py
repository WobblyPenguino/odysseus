from winlocalassistant.screen_analysis import (
    parse_screen_analysis_request,
    render_screen_analysis_prompt_help,
    build_screen_analysis_prompt,
    classify_screen_context_need,
    should_request_screen_context,
)


def test_classifies_terminal_screenshot_requests():
    text = "look at this PowerShell terminal screenshot and tell me the error"
    assert classify_screen_context_need(text) == "terminal"
    assert should_request_screen_context(text) is True


def test_classifies_gui_layout_requests():
    text = "the GUI panel and bottom composer overlap, screenshot attached"
    assert classify_screen_context_need(text) == "gui"


def test_classifies_browser_visual_requests():
    text = "browser layout is broken in Chromium viewport screenshot"
    assert classify_screen_context_need(text) == "browser"


def test_classifies_generic_image_requests():
    text = "what is visible in this image?"
    assert classify_screen_context_need(text) == "image"


def test_ignores_plain_text_code_requests():
    text = "refactor this helper function and add unit tests"
    assert classify_screen_context_need(text) == "none"
    assert should_request_screen_context(text) is False


def test_builds_safe_screen_analysis_prompt():
    prompt = build_screen_analysis_prompt("terminal", "PowerShell error screenshot")
    assert "Screen analysis kind: terminal" in prompt
    assert "PowerShell error screenshot" in prompt
    assert "Use only visible evidence" in prompt
    assert "Do not enable continuous screen watching" in prompt


def test_ignores_media_generation_image_storyboard_requests():
    text = "make a video trailer and image storyboard"
    assert classify_screen_context_need(text) == "none"


def test_parses_explicit_screen_analysis_prompt_kind():
    kind, text = parse_screen_analysis_request("terminal PowerShell traceback screenshot")
    assert kind == "terminal"
    assert text == "PowerShell traceback screenshot"


def test_renders_manual_screen_analysis_prompt_help():
    rendered = render_screen_analysis_prompt_help("gui", "drawer overlaps composer")
    assert "# Nova Screen Analysis Prompt" in rendered
    assert "Kind: `gui`" in rendered
    assert "does not capture the screen" in rendered
    assert "/image-analyze latest =>" in rendered
    assert "Do not enable continuous screen watching" in rendered


def test_screen_analysis_prompt_command_is_registered_static():
    from pathlib import Path

    core = Path("winlocalassistant/core.py").read_text(encoding="utf-8")
    tools = Path("winlocalassistant/tools.py").read_text(encoding="utf-8")

    assert '"/screen-analysis-prompt"' in core
    assert 'self.tools.call("screen_analysis_prompt", request=rest)' in core
    assert '"screen_analysis_prompt": self.screen_analysis_prompt_tool' in tools
    assert "def screen_analysis_prompt_tool" in tools
