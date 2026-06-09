import json
from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.model_registry import build_model_registry


def test_release_metadata_is_synchronised_for_v55_3_156() -> None:
    assert __version__ == "55.3.168"
    assert "v55.3.168" in VERSION_LABEL
    assert "natural research routing" in VERSION_LABEL
    readme = Path("README.md").read_text(encoding="utf-8")
    changelog = Path("CHANGELOG.md").read_text(encoding="utf-8")
    webui = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    manifest = json.loads(Path("RELEASE_MANIFEST.json").read_text(encoding="utf-8"))
    assert "Nova v55.3.168" in readme
    assert "v55.3.164" in changelog
    assert manifest["version"] == "55.3.168"
    assert "v55.3.168" in webui or "v55.3.164" in webui
    assert "qwen3-coder:30b" in webui


def test_model_registry_missing_models_are_deduplicated() -> None:
    payload = build_model_registry(installed=[])
    missing = payload["missing_models"]
    assert missing.count("qwen3-coder:30b") == 1
    assert "nomic-embed-text:latest" in missing
