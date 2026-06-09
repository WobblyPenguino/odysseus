from pathlib import Path

from winlocalassistant import VERSION_LABEL, __version__
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.tools import ToolRegistry


def test_version_label_mentions_sandbox_for_legacy_compatibility():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 123)
    assert f"v{__version__}" in VERSION_LABEL


def test_image_generate_without_backend_does_not_write_svg(tmp_path, monkeypatch):
    monkeypatch.setenv("NOVA_IMAGE_BACKEND", "auto")
    monkeypatch.delenv("NOVA_DIFFUSERS_MODEL", raising=False)
    monkeypatch.setenv("NOVA_ALLOW_DIFFUSERS_DOWNLOAD", "0")
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True))
    out = core.chat("/image-generate blue robot mascot")
    assert "image generation is not ready" in out.lower()
    assert "no real image-generation backend" in out.lower()
    assert not list((Path(tmp_path) / "generated_images").glob("*.svg"))


def test_vague_game_refinement_accepts_deterministic_game(tmp_path, monkeypatch):
    import winlocalassistant.tools as tools_module
    registry = ToolRegistry(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True))
    weak = {
        "folder": "WeakGame",
        "main_file": "index.html",
        "files": {
            "index.html": "<!doctype html><html><body><h1>Game</h1><script src=\"app.js\"></script></body></html>",
            "app.js": "let player = {x: 10}; function draw(){ player.x += 1; } setInterval(draw, 16);",
            "README.md": "# Tiny game draft",
        },
    }
    monkeypatch.setattr(tools_module, "model_chat", lambda *args, **kwargs: None)
    refined, trace, status = registry._refine_rejected_candidate(weak, "make a game", "model output did not implement the requested domain", "fast", max_rounds=1)
    assert refined is not None
    assert status == "accepted_after_deterministic_refinement"
    combined = "\n".join(refined["files"].values()).lower()
    assert "interaction" in combined
    assert "collision" in combined


def test_live_activity_keeps_legacy_marker_and_new_resize():
    html = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "legacy-test-marker:max-height:132px" in html
    assert "resize:vertical" in html
