from __future__ import annotations

import json
import tempfile
from pathlib import Path

import winlocalassistant.webui as webui_module


def _with_profile(profile: Path):
    class _Patch:
        def __enter__(self):
            self.old_app_dir = webui_module.APP_DIR
            webui_module.APP_DIR = profile
            return profile

        def __exit__(self, exc_type, exc, tb):
            webui_module.APP_DIR = self.old_app_dir

    return _Patch()


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def test_latest_idle_status_no_reports() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_webui_idle_empty_") as tmp:
        profile = Path(tmp) / "profile"
        with _with_profile(profile):
            payload = webui_module._latest_idle_status_payload()

    assert payload["status"] == "no-idle-reports"
    assert payload["message"] == "No idle self-improvement reports yet."
    assert payload["auto_apply_status"] == ""


def test_latest_idle_status_reads_idle_report_json() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_webui_idle_report_") as tmp:
        profile = Path(tmp) / "profile"
        report_path = profile / "idle_runs" / "idle_cycle_20260522_010101.json"
        _write_json(
            report_path,
            {
                "timestamp": "2026-05-22T01:01:01",
                "status": "proposal-only",
                "selected_candidate": {
                    "title": "Improve idle report quality",
                    "category": "report",
                    "value_score": 0.55,
                    "risk_score": 0.2,
                    "confidence_score": 0.8,
                    "final_score": 0.425,
                },
                "auto_apply_gate": {"status": "auto-apply-disabled"},
            },
        )
        with _with_profile(profile):
            payload = webui_module._latest_idle_status_payload()

    assert payload["latest_idle_report_path"] == str(report_path)
    assert payload["selected_candidate_title"] == "Improve idle report quality"
    assert payload["category"] == "report"
    assert payload["status"] == "proposal-only"
    assert payload["risk_score"] == 0.2
    assert payload["value_score"] == 0.55
    assert payload["confidence_score"] == 0.8
    assert payload["final_score"] == 0.425
    assert payload["auto_apply_status"] == "auto-apply-disabled"


def test_latest_idle_status_reads_idle_proposal_json() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_webui_idle_proposal_") as tmp:
        profile = Path(tmp) / "profile"
        proposal_path = profile / "idle_patch_proposals" / "idle_patch_proposal_20260522_020202.json"
        _write_json(
            proposal_path,
            {
                "timestamp": "2026-05-22T02:02:02",
                "status": "proposal-only",
                "candidate": {
                    "title": "Strengthen idle verification tests",
                    "category": "tests",
                    "value_score": 0.75,
                    "risk_score": 0.2,
                    "confidence_score": 0.85,
                    "final_score": 0.542,
                },
                "auto_apply_gate": {"status": "auto-apply-pending-patch"},
            },
        )
        with _with_profile(profile):
            payload = webui_module._latest_idle_status_payload()

    assert payload["latest_idle_proposal_path"] == str(proposal_path)
    assert payload["selected_candidate_title"] == "Strengthen idle verification tests"
    assert payload["category"] == "tests"
    assert payload["status"] == "proposal-only"
    assert payload["final_score"] == 0.542
    assert payload["auto_apply_status"] == "auto-apply-pending-patch"


def test_latest_idle_status_handles_corrupt_json_without_crashing() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_webui_idle_corrupt_") as tmp:
        profile = Path(tmp) / "profile"
        report_path = profile / "idle_runs" / "idle_cycle_20260522_030303.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text("{broken json", encoding="utf-8")
        with _with_profile(profile):
            payload = webui_module._latest_idle_status_payload()
            raw = webui_module._read_json_file(report_path)

    assert payload["status"] == "idle-report-read-error"
    assert "could not be read" in payload["message"]
    assert isinstance(raw, dict)
    assert "_read_error" in raw


def test_latest_json_file_returns_newest_matching_file() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_webui_idle_latest_") as tmp:
        root = Path(tmp)
        old = root / "idle_cycle_20260522_010101.json"
        new = root / "idle_cycle_20260522_020202.json"
        _write_json(old, {"status": "old"})
        _write_json(new, {"status": "new"})
        latest = webui_module._latest_json_file(root, "idle_cycle_*.json")

    assert latest == new


def test_webui_has_resizable_collapsible_panel_controls() -> None:
    html = webui_module.HTML
    assert "resizeRail leftRail" in html
    assert "resizeRail rightRail" in html
    assert "togglePanel('left')" in html
    assert "togglePanel('right')" in html
    assert "togglePanel('activity')" in html
    assert "setupSidebarSectionCollapse" in html
    assert "sectionCollapseBtn" in html
    assert "Workspace" in html


def test_webui_has_command_launcher_and_suggestion_buttons() -> None:
    html = webui_module.HTML
    source = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "Command Launcher" in html
    assert "COMMANDS=[" in html
    assert "renderCommandPalette()" in html
    assert "extractSuggestedCommands" in html
    assert "renderCommandSuggestions" in html
    assert "insertSuggestedCommand(this.dataset.command)" in html
    assert "j.command_suggestions" in html
    assert '"command_suggestions": suggestions' in source
    assert "suggest_next_commands" in source
    assert "quick(this.dataset.command)" not in html


def test_webui_auto_idle_starts_persistent_idle_until_confirmed_stop() -> None:
    html = webui_module.HTML
    assert "Permanent idle after 5 minutes inactive" in html
    assert "autoIdleActive" in html
    assert "startPermanentAutoIdle" in html
    assert "confirmAutoIdleStop" in html
    assert "quick('/idle start '+AUTO_IDLE_GOAL)" in html
    assert "quick('/idle stop')" in html
    assert "Stop idle mode now?" in html
    assert "quick('/idle once investigate logs and propose safe improvements')" not in html


def test_collapsed_panels_have_visible_restore_controls() -> None:
    html = webui_module.HTML
    assert 'id="restoreLeftPanel"' in html
    assert 'id="restoreRightPanel"' in html
    assert 'id="restoreActivityPanel"' in html
    assert "Show left panel" in html
    assert "Show right panel" in html
    assert "Show Live Activity" in html
    assert "body.collapse-left .panelRestore.leftRestore" in html
    assert "body.collapse-right .panelRestore.rightRestore" in html
    assert "body.collapse-activity .panelRestore.activityRestore" in html
    assert "togglePanel('left')" in html
    assert "togglePanel('right')" in html
    assert "togglePanel('activity')" in html


def test_webui_moves_research_database_controls_to_quick_commands_and_hides_context_bar() -> None:
    html = webui_module.HTML
    assert "Research topic" in html
    assert "DB list" in html
    assert "Research DB schema" in html
    assert "DB merge" in html
    assert "Remember project" in html
    assert "Loading research/database status..." not in html
    assert 'class="contextStatusLine" aria-hidden="true"' in html


def test_webui_live_activity_has_current_task_subtitle_and_compact_workspace() -> None:
    html = webui_module.HTML
    assert 'id="activitySubtitle"' in html
    assert "Current task:" in html
    assert "loadActivitySubtitle" in html
    assert "#generalPanel{padding:5px 12px" in html
    assert ".topbar{padding:6px 12px" in html


def run_all(verbose: bool = False) -> None:
    tests = [
        (name, fn)
        for name, fn in sorted(globals().items())
        if name.startswith("test_") and callable(fn)
    ]
    for name, fn in tests:
        fn()
        if verbose:
            print(f"PASS {name}")


if __name__ == "__main__":
    run_all(verbose=True)
