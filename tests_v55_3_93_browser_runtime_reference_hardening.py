from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.tools import ToolRegistry


def test_webui_defines_all_runtime_functions_seen_in_browser_console():
    html = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    required = [
        "function maybeSpeakReply",
        "function stripEmojiForSpeech",
        "async function loadIdleStatus",
        "function checkModelSetup",
        "function closeModelSetup",
        "function confirmInterrupt",
        "function toggleAvatarAudio",
        "function downloadOpenFile",
        "function askEditOpenFile",
        "async function loadRecentModelContext",
    ]
    missing = [name for name in required if name not in html]
    assert not missing


def test_model_candidate_static_validation_blocks_literal_backslash_n_before_write(tmp_path):
    reg = ToolRegistry(AssistantConfig(workspace=str(tmp_path)))
    candidate = {
        "files": {
            "index.html": '<div id="result"></div><script src="app.js"></script>',
            "app.js": "function clear(){document.getElementById('result').innerHTML = '';\\n}",
        }
    }
    ok, reason = reg._validate_model_project(candidate, "make a tiny local app")
    assert not ok
    assert "literal" in reason.lower()
    assert "before writing" in reason.lower()


def test_deterministic_candidate_refinement_repairs_backslash_n_transport_artifact(tmp_path):
    reg = ToolRegistry(AssistantConfig(workspace=str(tmp_path)))
    candidate = {
        "folder": "Demo",
        "files": {
            "index.html": '<div id="result"></div><script src="app.js"></script>',
            "app.js": "function clear(){document.getElementById('result').innerHTML = '';\\n}",
        },
    }
    refined, edits = reg._deterministic_refine_candidate(candidate, "make a tiny local app", "candidate JavaScript contains literal")
    assert "\\n}" not in refined["files"]["app.js"]
    assert "\n}" in refined["files"]["app.js"]
    assert any(edit.get("kind") == "candidate_js_transport_newline" for edit in edits)


def test_candidate_static_validation_blocks_missing_dom_id(tmp_path):
    reg = ToolRegistry(AssistantConfig(workspace=str(tmp_path)))
    candidate = {
        "files": {
            "index.html": '<main><button id="save">Save</button></main><script src="app.js"></script>',
            "app.js": "const missing = document.getElementById('result'); console.log(missing);",
        }
    }
    ok, reason = reg._validate_model_project(candidate, "make a tiny local app")
    assert not ok
    assert "missing html id" in reason.lower()
