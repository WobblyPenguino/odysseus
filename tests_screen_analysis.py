from winlocalassistant.screen_analysis import (
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
