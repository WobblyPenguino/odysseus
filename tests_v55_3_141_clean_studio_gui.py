from pathlib import Path

from winlocalassistant import VERSION_LABEL, __version__
from winlocalassistant.webui import HTML


def test_clean_studio_gui_hotfix_metadata_and_docs():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 141)
    assert "Clean Studio GUI shell" in VERSION_LABEL
    assert "Nova_v55_3_141_clean_studio_gui_hotfix_20260602.zip" in Path("README.md").read_text(encoding="utf-8")
    assert "Clean Studio GUI shell hotfix" in Path("CHANGELOG.md").read_text(encoding="utf-8")


def test_clean_studio_shell_replaces_default_voyage_clutter():
    required = [
        "studioHome",
        "data-clean-studio-shell",
        "Nova Studio",
        "Chat in the centre. Tools on the left. State on the right.",
        "Clean VS Code / ChatGPT style shell",
        "odysseusWorkspaceActive='runtime';showOdysseusWorkspace()",
        "odysseusVoyageDeck",
        "max-height:0!important",
        "pointer-events:none",
    ]
    missing = [marker for marker in required if marker not in HTML]
    assert not missing


def test_clean_resize_and_voice_clutter_overrides_are_present():
    assert ".middleResizeRail.visible{height:4px!important" in HTML
    assert ".middleResizeRail.visible:after{content:''!important}" in HTML
    assert ".composer .voiceWaveRow{display:none!important}" in HTML
    assert "grid-template-columns:minmax(280px,var(--left-col)) 5px minmax(560px,1fr) 5px minmax(320px,var(--right-col))" in HTML


def test_existing_major_features_remain_wired_in_clean_shell():
    for marker in [
        "Communication centre",
        "Project files",
        "AI Toolbox",
        "Live activity",
        "Hey Nova",
        "Linux Sandbox",
        "Kali Sandbox",
        "Docker Diagnostics",
        "Transparent output",
        "Bridge receipts",
        "/user-feedback-tests",
        "/doctor",
    ]:
        assert marker in HTML
