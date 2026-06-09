from __future__ import annotations

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.webui import HTML


def test_gui_version_matches_package_version() -> None:
    major_minor_patch = __version__.rsplit(".", 1)[0]
    assert f"Nova v{major_minor_patch}" in HTML or f"Nova {__version__}" in HTML
    assert "game" in HTML.lower() or "game" in VERSION_LABEL.lower()


def test_plan_before_run_panel_and_update_helper_exist() -> None:
    assert "planningVisibilityPanel" in HTML
    assert "Plan before run" in HTML
    assert "function updatePlanningVisibility" in HTML
    assert "Intent confidence" in HTML or "Confidence:" in HTML


def run_all(verbose: bool = False) -> None:
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        fn()
        if verbose:
            print(f"PASS {name}")


if __name__ == "__main__":
    run_all(verbose=True)
