from __future__ import annotations

import base64
import json
import os
import tempfile
from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.file_context import (
    build_prompt_context,
    clear_file_contexts,
    image_size,
    list_file_contexts,
    register_file_context_from_path,
    register_uploaded_file,
    resolve_image_context,
)


class _FakeImageEditResult:
    ok = True
    backend = "fake"
    message = "Edited a real image with fake backend."
    details = {}

    def __init__(self, path: Path) -> None:
        self.path = str(path)


def test_attach_text_file_and_build_prompt_context() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_filectx_") as tmp:
        root = Path(tmp)
        src = root / "notes.txt"
        src.write_text("hello from shared file\nsecond line", encoding="utf-8")
        ctx = register_file_context_from_path(src, profile_dir=root)
        assert ctx.kind == "text"
        assert "hello from shared file" in ctx.context_text
        contexts = list_file_contexts(profile_dir=root)
        assert len(contexts) == 1
        prompt = build_prompt_context(contexts)
        assert "Shared file context" in prompt
        assert "notes.txt" in prompt
        assert clear_file_contexts(profile_dir=root) >= 2


def test_upload_png_image_context_records_dimensions() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_imgctx_") as tmp:
        # 1x1 transparent PNG
        png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII=")
        ctx = register_uploaded_file("photo.png", png, mime_type="image/png", profile_dir=Path(tmp))
        assert ctx.kind == "image"
        assert "1x1" in ctx.context_text or "1x1" in ctx.summary
        assert "image-analyze" in ctx.context_text



def test_resolve_uploaded_image_by_latest_and_id() -> None:
    clear_file_contexts()
    try:
        png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII=")
        ctx = register_uploaded_file("latest_photo.png", png, mime_type="image/png")
        assert resolve_image_context("latest").context_id == ctx.context_id
        assert resolve_image_context(f"context:{ctx.context_id}").original_name == "latest_photo.png"
        assert resolve_image_context("latest_photo").context_id == ctx.context_id
    finally:
        clear_file_contexts()


def test_core_image_analyze_accepts_uploaded_latest(monkeypatch=None) -> None:
    clear_file_contexts()
    try:
        png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII=")
        register_uploaded_file("ui_photo.png", png, mime_type="image/png")
        from winlocalassistant import tools as tools_mod
        fake_vision = lambda *args, **kwargs: "fake vision analysis ok"
        old_vision = getattr(tools_mod, "ollama_vision_chat")
        if monkeypatch is not None:
            monkeypatch.setattr(tools_mod, "ollama_vision_chat", fake_vision)
        else:
            tools_mod.ollama_vision_chat = fake_vision
        try:
            with tempfile.TemporaryDirectory(prefix="wla_img_analyze_") as tmp:
                core = AssistantCore(AssistantConfig(workspace=tmp, allow_mutating_tools=False))
                out = core.chat("/image-analyze latest => describe it")
                assert "Vision analysis completed" in out
                assert "fake vision analysis ok" in out
        finally:
            if monkeypatch is None:
                tools_mod.ollama_vision_chat = old_vision
    finally:
        clear_file_contexts()


def test_core_image_analyze_reports_ollama_error(monkeypatch=None) -> None:
    from winlocalassistant import tools as tools_mod

    old_vision = getattr(tools_mod, "ollama_vision_chat")
    old_busy = getattr(tools_mod, "ollama_busy_state")

    def fake_busy_state():
        return {"last_prompt": {"result": "http_500", "error": "unknown model architecture"}}

    if monkeypatch is not None:
        monkeypatch.setattr(tools_mod, "ollama_vision_chat", lambda *args, **kwargs: None)
        monkeypatch.setattr(tools_mod, "ollama_busy_state", fake_busy_state)
    else:
        tools_mod.ollama_vision_chat = lambda *args, **kwargs: None
        tools_mod.ollama_busy_state = fake_busy_state
    try:
        with tempfile.TemporaryDirectory(prefix="wla_img_analyze_error_") as tmp:
            root = Path(tmp)
            png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII=")
            (root / "photo.png").write_bytes(png)
            core = AssistantCore(AssistantConfig(workspace=tmp, allow_mutating_tools=False, vision_model="bad-vision:model"))
            out = core.chat("/image-analyze photo.png => describe it")
            assert "Vision model did not return a response" in out
            assert "unknown model architecture" in out
            assert "gemma3:12b" in out
    finally:
        if monkeypatch is None:
            tools_mod.ollama_vision_chat = old_vision
            tools_mod.ollama_busy_state = old_busy

def test_core_attach_file_command_lists_and_clears_context() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_core_filectx_") as tmp:
        src = Path(tmp) / "brief.md"
        src.write_text("# Project brief\nMake a useful app.", encoding="utf-8")
        cfg = AssistantConfig(workspace=tmp, allow_mutating_tools=False)
        core = AssistantCore(cfg)
        out = core.chat(f"/attach-file {src}")
        assert "Attached file context" in out
        listing = core.chat("/context-files")
        assert "brief.md" in listing
        cleared = core.chat("/context-files clear")
        assert "Cleared" in cleared


def test_image_draft_creates_svg_in_workspace() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_svggen_") as tmp:
        core = AssistantCore(AssistantConfig(workspace=tmp, allow_mutating_tools=True))
        out = core.chat("/image-draft blue robot mascot")
        assert "SVG draft placeholder" in out
        assert "/view?path=generated_images/" in out
        assert list((Path(tmp) / "generated_images").glob("*.svg"))


def test_image_generate_does_not_fake_real_generation_without_backend() -> None:
    keys = ["NOVA_IMAGE_BACKEND", "NOVA_DIFFUSERS_MODEL", "NOVA_ALLOW_DIFFUSERS_DOWNLOAD"]
    old_env = {key: os.environ.get(key) for key in keys}
    for key in keys:
        os.environ.pop(key, None)
    with tempfile.TemporaryDirectory(prefix="wla_real_img_") as tmp:
        try:
            core = AssistantCore(AssistantConfig(workspace=tmp, allow_mutating_tools=True))
            out = core.chat("/image-generate blue robot mascot")
            assert "not ready" in out.lower() or "no real image-generation backend" in out.lower()
            assert not list((Path(tmp) / "generated_images").glob("*.svg"))
        finally:
            for key, value in old_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


def test_core_image_edit_accepts_uploaded_latest(monkeypatch=None) -> None:
    clear_file_contexts()
    try:
        png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII=")
        register_uploaded_file("edit_source.png", png, mime_type="image/png")
        from winlocalassistant import core as core_mod

        def fake_edit_image(prompt, source, output_dir, **kwargs):
            output_dir.mkdir(parents=True, exist_ok=True)
            out = output_dir / "edited_image_fake.png"
            out.write_bytes(png)
            assert "warmer" in prompt
            assert Path(source).exists()
            return _FakeImageEditResult(out)

        old_edit = getattr(core_mod, "edit_image")
        if monkeypatch is not None:
            monkeypatch.setattr(core_mod, "edit_image", fake_edit_image)
        else:
            core_mod.edit_image = fake_edit_image
        try:
            with tempfile.TemporaryDirectory(prefix="wla_img_edit_cmd_") as tmp:
                core = AssistantCore(AssistantConfig(workspace=tmp, allow_mutating_tools=True))
                out = core.chat("/image-edit latest => make it warmer")
                assert "Edited a real image" in out
                assert "/view?path=generated_images/edited_image_fake.png" in out
        finally:
            if monkeypatch is None:
                core_mod.edit_image = old_edit
    finally:
        clear_file_contexts()


def run_all(verbose: bool = False) -> None:
    for fn in [
        test_attach_text_file_and_build_prompt_context,
        test_upload_png_image_context_records_dimensions,
        test_resolve_uploaded_image_by_latest_and_id,
        test_core_image_analyze_accepts_uploaded_latest,
        test_core_image_analyze_reports_ollama_error,
        test_core_attach_file_command_lists_and_clears_context,
        test_image_draft_creates_svg_in_workspace,
        test_image_generate_does_not_fake_real_generation_without_backend,
        test_core_image_edit_accepts_uploaded_latest,
    ]:
        fn()
        if verbose:
            print(f"PASS {fn.__name__}")
