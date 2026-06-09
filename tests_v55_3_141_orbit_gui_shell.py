from pathlib import Path

from winlocalassistant import VERSION_LABEL, __version__
from winlocalassistant.webui import HTML


def test_orbit_gui_shell_metadata_and_docs():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 142)
    assert "Orbit GUI shell" in VERSION_LABEL
    assert "Nova_v55_3_142_orbit_workspace_drawer_hotfix_20260602.zip" in Path("README.md").read_text(encoding="utf-8")
    assert "Orbit workspace drawer hotfix" in Path("CHANGELOG.md").read_text(encoding="utf-8")


def test_orbit_shell_reframes_the_layout_not_just_old_studio_css():
    required = [
        "data-orbit-studio-shell",
        "nova-orbit-shell",
        "orbitNav",
        "orbitLegacyDrawer",
        "orbitRightDrawer",
        "orbitActivityDrawer",
        "grid-template-columns:var(--orbit-left) 0 minmax(0,1fr) 0 0",
        "background-size:auto,auto,24px 24px,24px 24px",
        "Local AI workspace. Chat stays centred",
    ]
    missing = [marker for marker in required if marker not in HTML]
    assert not missing


def test_orbit_shell_keeps_existing_feature_ids_for_backend_wiring():
    for marker in [
        'id="projects"',
        'id="files"',
        'id="customTools"',
        'id="communicationCentreBoard"',
        'id="activityLog"',
        'id="assistantBoxText"',
        'id="editor"',
        'id="msg"',
        "toggleWakeWordListening",
        "loadActivity",
        "loadProjects",
    ]:
        assert marker in HTML
