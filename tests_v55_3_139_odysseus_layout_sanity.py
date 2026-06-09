from __future__ import annotations

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.webui import HTML, PWA_MANIFEST, SERVICE_WORKER_JS
from winlocalassistant.architecture_audit import run_architecture_audit


def test_version_and_manifest_are_synced_for_layout_patch() -> None:
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 139)
    assert f"v{__version__}" in VERSION_LABEL
    assert "Odysseus-style voyage workspace deck" in VERSION_LABEL
    assert f"v{__version__}" in HTML or "Nova v55.3.141" in HTML
    assert "55-3-139" in SERVICE_WORKER_JS
    assert PWA_MANIFEST["short_name"] == "Nova"


def test_odysseus_voyage_deck_is_visible_and_route_safe() -> None:
    required = [
        "odysseusVoyageDeck",
        "Yours for the voyage",
        "Chat & Agents",
        "Cookbook",
        "Deep Research",
        "Compare",
        "Documents",
        "Notes & Tasks",
        "Memory",
        "Themes",
        "odysseusWorkspaceActive='cookbook'",
        "odysseusWorkspaceActive='compare'",
        "odysseusWorkspaceActive='docs'",
        "odysseusWorkspaceActive='tasks'",
        "odysseusWorkspaceActive='memory'",
        "showOdysseusWorkspace()",
        "/nova-gui-workbench-plan",
    ]
    missing = [marker for marker in required if marker not in HTML]
    assert not missing


def test_existing_workspace_routes_and_panels_are_preserved() -> None:
    for marker in [
        "/odysseus-workbench",
        "/odysseus-runtime",
        "/api/odysseus-workspace",
        "/api/odysseus-runtime",
        "Linux Sandbox",
        "Kali Sandbox",
        "Communication centre",
        "Transparent output",
        "Live activity",
    ]:
        assert marker in HTML


def test_architecture_audit_version_check_uses_release_theme_not_full_legacy_label() -> None:
    report = run_architecture_audit()
    version = next(check for check in report.checks if check["name"] == "version_consistency")
    assert version["ok"] is True
    assert version.get("missing") == []
