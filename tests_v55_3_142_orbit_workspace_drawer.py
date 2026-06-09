from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.webui import HTML


def test_v55_3_142_release_metadata_mentions_workspace_drawer_hotfix():
    assert __version__ >= "55.3.142"
    assert "Orbit workspace drawer hotfix" in VERSION_LABEL
    assert "Nova_v55_3_142_orbit_workspace_drawer_hotfix_20260602.zip" in Path("README.md").read_text(encoding="utf-8")
    assert "v55.3.142 Orbit workspace drawer hotfix" in Path("CHANGELOG.md").read_text(encoding="utf-8")


def test_orbit_drawers_reserve_layout_space_instead_of_only_overlaying_chat():
    required = [
        "data-orbit-studio-shell",
        "orbitDrawerOpen main[data-ui-overhaul]",
        "calc(var(--orbit-left) + var(--orbit-drawer-width))",
        "orbit-right-open main[data-ui-overhaul]",
        "var(--orbit-right-width)",
        "toggleOrbitDrawer(target)",
        "toggleOrbitRight(target)",
    ]
    missing = [marker for marker in required if marker not in HTML]
    assert not missing


def test_chats_theme_activity_and_voice_state_are_real_orbit_controls():
    required = [
        "ensureOrbitChatsPanel",
        "orbitChatsPanel",
        "showChatsPopup(){openOrbitDrawer('chats')",
        "ensureOrbitThemePanel",
        "Theme customizer",
        "applyOrbitThemeFromInputs",
        "orbitMiniOrb",
        "orbitSubChatLine",
        "Distinct Hey Nova ready cue played",
        "chatWrap.appendChild(ad)",
        "sub.id='orbitSubChat'",
    ]
    missing = [marker for marker in required if marker not in HTML]
    assert not missing


def test_odysseus_style_capability_cards_are_mapped_to_existing_safe_routes():
    for marker in [
        "Odysseus-style apps mapped to Nova",
        "/research topic to investigate",
        "/compare A vs B",
        "toggleOrbitRight('voice')",
        "toggleOrbitActivity(true)",
        "openOrbitThemePanel()",
        "showOdysseusWorkspace()",
    ]:
        assert marker in HTML
