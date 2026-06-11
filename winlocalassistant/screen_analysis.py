"""Screen and image analysis routing helpers for Nova.

This module is intentionally pure and side-effect free. It does not capture the
screen, open files, call OCR, or call a vision model. It only classifies when
screen/image context would be useful and builds a safe prompt for a later vision
adapter.
"""

from __future__ import annotations

from typing import Literal

ScreenContextKind = Literal["none", "image", "gui", "terminal", "browser"]

_TERMINAL_TERMS = (
    "terminal",
    "powershell",
    "command prompt",
    "cmd",
    "console",
    "shell",
    "traceback",
    "stack trace",
    "error output",
    "terminal output",
)

_GUI_TERMS = (
    "gui",
    "button",
    "panel",
    "drawer",
    "composer",
    "popup",
    "overlap",
    "layout",
    "window",
    "screen size",
    "ui",
)

_BROWSER_TERMS = (
    "browser",
    "web page",
    "chromium",
    "playwright",
    "html",
    "css",
    "viewport",
    "responsive",
)

_IMAGE_TERMS = (
    "screenshot",
    "screen shot",
    "image",
    "picture",
    "photo",
    "see my screen",
    "look at my screen",
    "visible",
    "visual",
)


_MEDIA_GENERATION_TERMS = (
    "make a video",
    "create a video",
    "video trailer",
    "storyboard",
    "image storyboard",
    "generate image",
    "render",
    "comfyui",
)

_VISUAL_INSPECTION_TERMS = (
    "screenshot",
    "screen shot",
    "look at",
    "visible",
    "what is visible",
    "what is shown",
    "attached",
    "see my screen",
    "terminal output",
    "error output",
)


def _normalise_text(user_text: str | None) -> str:
    return " ".join(str(user_text or "").lower().split())


def classify_screen_context_need(user_text: str | None) -> ScreenContextKind:
    """Classify whether a user request would benefit from screen/image context."""

    text = _normalise_text(user_text)
    if not text:
        return "none"

    if any(term in text for term in _MEDIA_GENERATION_TERMS) and not any(
        term in text for term in _VISUAL_INSPECTION_TERMS
    ):
        return "none"

    has_image_signal = any(term in text for term in _IMAGE_TERMS)
    has_terminal_signal = any(term in text for term in _TERMINAL_TERMS)
    has_gui_signal = any(term in text for term in _GUI_TERMS)
    has_browser_signal = any(term in text for term in _BROWSER_TERMS)

    if has_terminal_signal and (has_image_signal or "output" in text or "error" in text):
        return "terminal"
    if has_browser_signal and (has_image_signal or has_gui_signal):
        return "browser"
    if has_gui_signal and (has_image_signal or "fix" in text or "broken" in text):
        return "gui"
    if has_image_signal:
        return "image"

    return "none"


def should_request_screen_context(user_text: str | None) -> bool:
    """Return True when Nova should ask for or use a screenshot/image."""

    return classify_screen_context_need(user_text) != "none"


def build_screen_analysis_prompt(kind: ScreenContextKind, user_text: str | None) -> str:
    """Build a safe prompt for a later vision/OCR adapter."""

    if kind == "none":
        kind = classify_screen_context_need(user_text)

    if kind not in {"image", "gui", "terminal", "browser"}:
        return "No screen/image analysis is needed for this request."

    request = str(user_text or "").strip()
    focus = {
        "image": "Identify the visible content and only describe what is shown.",
        "gui": "Inspect visible GUI layout, overlap, clipped controls, broken panels, and usability issues.",
        "terminal": "Inspect visible terminal output, errors, commands, paths, and the next safe debugging step.",
        "browser": "Inspect visible browser layout, viewport issues, rendering problems, and evidence useful for Playwright/browser tests.",
    }[kind]

    return (
        f"Screen analysis kind: {kind}\n"
        f"User request: {request}\n\n"
        f"{focus}\n"
        "Rules:\n"
        "- Use only visible evidence from the provided screenshot/image.\n"
        "- Do not assume hidden windows, private files, or unseen terminal output.\n"
        "- Prefer concrete observations and next actions.\n"
        "- Mention uncertainty when text is too small, cropped, or unreadable.\n"
        "- Do not enable continuous screen watching; use explicit user-provided or manually captured images only.\n"
    )
