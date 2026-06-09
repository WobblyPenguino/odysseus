from __future__ import annotations

import re
from pathlib import Path


def _webui_text() -> str:
    return Path("winlocalassistant/webui.py").read_text(encoding="utf-8")


def _webui_script() -> str:
    text = _webui_text()
    scripts = re.findall(r"<script>(.*?)</script>", text, re.S)
    assert scripts, "webui.py should embed a browser script"
    return "\n".join(scripts)


def test_webui_browser_script_references_existing_dom_ids() -> None:
    text = _webui_text()
    script = _webui_script()
    ids = set(re.findall(r'id="([^"]+)"', text))
    refs = set(re.findall(r"getElementById\(['\"]([^'\"]+)['\"]\)", script))
    missing = sorted(refs - ids)
    assert missing == []


def test_open_file_flow_uses_actual_editor_dom_contract() -> None:
    script = _webui_script()
    assert "document.getElementById('openFilePath')" not in script
    assert "document.getElementById('openFileContent')" not in script
    assert "if(openPath)openPath.textContent=currentFile" in script
    assert "const content=editor?.value||''" in script


def test_status_autonomous_and_architecture_panels_are_wired() -> None:
    text = _webui_text()
    assert 'id="statusChips"' in text
    assert 'id="autonomousLivePanel"' in text
    assert 'id="architectureMini"' in text
    assert "if(!box)return;const s=j.state||{}" in text


def test_tutorial_points_at_existing_avatar_presence_panel() -> None:
    text = _webui_text()
    assert "target:'#aiPresenceBox'" in text
    assert "target:'#avatarBox'" not in text
