from __future__ import annotations

import tempfile
from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.tools import ToolRegistry


def _registry() -> ToolRegistry:
    tmp = tempfile.TemporaryDirectory(prefix="wla_json_recovery_")
    # Keep tempdir alive by attaching it to registry.
    reg = ToolRegistry(AssistantConfig(workspace=tmp.name))
    reg._tmp = tmp  # type: ignore[attr-defined]
    return reg


def test_extract_json_tolerates_windows_paths_and_js_single_quote_escapes() -> None:
    reg = _registry()
    text = r'''
Here is the project:
{
  "folder": "interactive_app",
  "main_file": "index.html",
  "run_command": "start .\index.html",
  "verify_command": "python -c \"print('ok')\"",
  "notes": "demo",
  "human_summary": "demo",
  "files": {
    "app.js": "document.getElementById('message').innerHTML = '<div id=\'success\'>ok</div>';"
  }
}
'''
    data = reg._extract_json_object(text)
    assert data is not None
    assert data["folder"] == "interactive_app"
    assert "app.js" in data["files"]
    assert "success" in data["files"]["app.js"]


def test_extract_json_strips_markdown_fence_and_commentary() -> None:
    reg = _registry()
    text = '```json\n{"folder":"x","files":{"index.html":"<html></html>"}}\n```'
    data = reg._extract_json_object(text)
    assert data is not None
    assert data["folder"] == "x"


def run_all(verbose: bool = False) -> None:
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        fn()
        if verbose:
            print(f"PASS {name}")


if __name__ == "__main__":
    run_all(verbose=True)
