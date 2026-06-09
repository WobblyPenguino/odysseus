from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.core import AssistantCore
from winlocalassistant.config import AssistantConfig
from winlocalassistant.tools import ToolRegistry
from winlocalassistant.release_hygiene import clean_release_hygiene_artifacts, find_release_hygiene_findings


def test_version_metadata_mentions_new_sandbox_and_model_helper_features():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 123)
    low = VERSION_LABEL.lower()
    assert f"v{__version__}" in VERSION_LABEL
    assert "voice" in low


def test_browser_static_acceptance_catches_broken_dom_ids(tmp_path: Path):
    root = tmp_path / "BrokenApp"
    root.mkdir()
    (root / "index.html").write_text('<form id="noteForm"><input id="noteInput"><button onclick="saveNote()">Save</button></form><script src="app.js"></script>', encoding="utf-8")
    (root / "app.js").write_text("const x=document.getElementById('newNote');document.getElementById('missingForm').addEventListener('submit',()=>{});", encoding="utf-8")
    cfg = AssistantConfig(workspace=str(root))
    reg = ToolRegistry(cfg)
    ok, problems = reg._static_acceptance_check(root, "make a tiny notes app with localStorage and JSON export")
    assert ok is False
    kinds = {p.get("kind") for p in problems}
    assert "broken_dom_reference" in kinds
    assert "broken_inline_handler" in kinds


def test_sandbox_dev_mode_commands_are_visible_and_nonblocking(tmp_path: Path):
    cfg = AssistantConfig(workspace=str(tmp_path))
    app = AssistantCore(cfg)
    assert "copied workspace" in app.sandbox_dev_mode_command("status").lower()
    help_text = app.handle_command("/help")
    assert "/sandbox-dev-run" in help_text
    assert "/model-help-plan" in help_text
    assert "/beyond-thinking" in help_text


def test_release_hygiene_clean_removes_cache_artifacts(tmp_path: Path):
    cache = tmp_path / "__pycache__"
    cache.mkdir()
    (cache / "x.pyc").write_bytes(b"bad")
    assert find_release_hygiene_findings(tmp_path)
    result = clean_release_hygiene_artifacts(tmp_path)
    assert result["ok"] is True
    assert not find_release_hygiene_findings(tmp_path)
