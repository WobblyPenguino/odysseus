from pathlib import Path
import shutil
import subprocess

from winlocalassistant.game_design import build_generic_canvas_game_project


def test_generic_game_fallback_javascript_passes_node_check(tmp_path):
    project = build_generic_canvas_game_project("make a fishing game with rocks and score")
    js = project["files"]["app.js"]
    assert "function update" in js
    assert "function loop" in js
    js_path = tmp_path / "app.js"
    js_path.write_text(js, encoding="utf-8")
    node = shutil.which("node")
    if node:
        cp = subprocess.run([node, "--check", str(js_path)], capture_output=True, text=True, timeout=20)
        assert cp.returncode == 0, (cp.stdout + cp.stderr)


def test_webui_has_clickable_planning_choices_and_chat_keyboard_shortcuts():
    html = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "replyActiveRun()" in html
    assert "Click a choice button to continue" in html
    assert "setupChatKeyboard" in html
    assert "e.key==='Enter'&&!e.shiftKey" in html
    assert "ArrowUp" in html and "ArrowDown" in html


def test_webui_llm_status_is_human_readable_and_models_are_expandable():
    html = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "renderModelCards" in html
    assert "Installed models and Nova use" in html
    assert "Active model runtime" in html
    assert "Raw diagnostic details" in html


def test_webui_created_output_can_be_closed_and_refresh_shows_spinner():
    html = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "createdClose" in html
    assert "artifactPanel.style.display" in html
    assert "refreshSpinner" in html
    assert "refreshProjectsBtn" in html
    assert "refreshFilesBtn" in html


def test_webui_has_compact_live_activity_and_project_multiselect():
    html = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "body.collapse-activity .activity{display:block!important" in html
    assert "Project/file lists" in html
    assert "projectSelect" in html
    assert "bulkDeleteSelectedProjects" in html


def run_all(verbose: bool = False):
    tests = [
        test_generic_game_fallback_javascript_passes_node_check,
        test_webui_has_clickable_planning_choices_and_chat_keyboard_shortcuts,
        test_webui_llm_status_is_human_readable_and_models_are_expandable,
        test_webui_created_output_can_be_closed_and_refresh_shows_spinner,
        test_webui_has_compact_live_activity_and_project_multiselect,
    ]
    import tempfile
    from pathlib import Path
    for fn in tests:
        if fn.__name__ == 'test_generic_game_fallback_javascript_passes_node_check':
            with tempfile.TemporaryDirectory() as d:
                fn(Path(d))
        else:
            fn()
        if verbose:
            print('PASS', fn.__name__)
