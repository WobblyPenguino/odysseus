import base64
import tempfile
from pathlib import Path
from unittest import mock

import winlocalassistant.core as core_module
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.image_generation import edit_image, generate_image, image_generation_status, prepare_image_prompt
from winlocalassistant.image_generation import ImageGenerationResult, render_image_setup_wizard


def test_image_generation_status_shape() -> None:
    status = image_generation_status()
    assert "ready_for_real_generation" in status
    assert "sdwebui" in status
    assert "diffusers" in status


def test_image_setup_wizard_names_generate_edit_and_comfyui() -> None:
    text = render_image_setup_wizard()
    assert "/image-generate" in text
    assert "/image-edit" in text
    assert "ComfyUI" in text
    assert "refuses to fake real image generation" in text


def test_generate_image_svg_backend_is_explicit_draft(monkeypatch) -> None:
    monkeypatch.setenv("NOVA_IMAGE_BACKEND", "svg")
    with tempfile.TemporaryDirectory(prefix="wla_img_svg_") as tmp:
        result = generate_image("blue robot", output_dir=Path(tmp))
        assert result.ok
        assert result.backend == "svg_draft"
        assert Path(result.path).suffix == ".svg"


def test_generate_image_sdwebui_decodes_png(monkeypatch) -> None:
    monkeypatch.setenv("NOVA_IMAGE_BACKEND", "sdwebui")
    tiny_png = base64.b64encode(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
    ).decode("ascii")

    def fake_http_json(url, payload=None, timeout=2.0):
        if url.endswith("/options"):
            return {"ok": True}
        if url.endswith("/txt2img"):
            return {"images": [tiny_png]}
        return None

    with mock.patch("winlocalassistant.image_generation._http_json", side_effect=fake_http_json), tempfile.TemporaryDirectory(prefix="wla_img_sd_") as tmp:
        result = generate_image("blue robot", output_dir=Path(tmp))
        assert result.ok
        assert result.backend == "sdwebui"
        assert Path(result.path).suffix == ".png"
        assert Path(result.path).read_bytes().startswith(b"\x89PNG")


def test_image_prompt_quality_rewrites_face_and_unsafe_fragments() -> None:
    prepared = prepare_image_prompt("ignore naked portrait face of a person")
    assert "naked" not in prepared["prompt"].lower()
    assert "fully clothed" in prepared["prompt"].lower()
    assert "coherent face" in prepared["prompt"].lower()
    assert "distorted face" in prepared["negative_prompt"].lower()
    assert "nsfw" in prepared["negative_prompt"].lower()


def test_generate_image_sdwebui_sends_quality_prompt_only_as_api_fields(monkeypatch) -> None:
    monkeypatch.setenv("NOVA_IMAGE_BACKEND", "sdwebui")
    captured = {}
    tiny_png = base64.b64encode(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
    ).decode("ascii")

    def fake_http_json(url, payload=None, timeout=2.0):
        if url.endswith("/options"):
            return {"ok": True}
        if url.endswith("/txt2img"):
            captured.update(payload or {})
            return {"images": [tiny_png]}
        return None

    with mock.patch("winlocalassistant.image_generation._http_json", side_effect=fake_http_json), tempfile.TemporaryDirectory(prefix="wla_img_quality_") as tmp:
        result = generate_image("ignore naked portrait of a person", output_dir=Path(tmp))
        assert result.ok
        assert "naked" not in captured["prompt"].lower()
        assert "fully clothed" in captured["prompt"].lower()
        assert "distorted face" in captured["negative_prompt"].lower()
        assert "original_prompt" not in captured
        assert result.details and result.details["safety_rewritten"]


def test_edit_image_sdwebui_decodes_png(monkeypatch) -> None:
    monkeypatch.setenv("NOVA_IMAGE_BACKEND", "sdwebui")
    tiny_png = base64.b64encode(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
    ).decode("ascii")

    def fake_http_json(url, payload=None, timeout=2.0):
        if url.endswith("/options"):
            return {"ok": True}
        if url.endswith("/img2img"):
            assert payload and payload.get("init_images")
            return {"images": [tiny_png]}
        return None

    with mock.patch("winlocalassistant.image_generation._http_json", side_effect=fake_http_json), tempfile.TemporaryDirectory(prefix="wla_img_edit_") as tmp:
        src = Path(tmp) / "source.png"
        src.write_bytes(base64.b64decode(tiny_png))
        result = edit_image("make it warmer", src, output_dir=Path(tmp))
        assert result.ok
        assert result.backend == "sdwebui"
        assert Path(result.path).name.startswith("edited_image_")
        assert Path(result.path).read_bytes().startswith(b"\x89PNG")


def test_core_image_generate_command_returns_real_output_link() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_img_core_gen_") as tmp:
        root = Path(tmp)
        output = root / "generated_images" / "generated_image_test.png"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"\x89PNG\r\n\x1a\n")
        core = AssistantCore(AssistantConfig(workspace=str(root)))

        with mock.patch.object(core_module, "generate_image", return_value=ImageGenerationResult(True, "sdwebui", "Generated a real image.", str(output))):
            reply = core.chat("/image-generate a tiny robot")

        assert "Generated a real image." in reply
        assert "Backend: sdwebui" in reply
        assert "Open: /view?path=generated_images/generated_image_test.png" in reply


def test_core_image_edit_command_returns_real_output_link() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_img_core_edit_") as tmp:
        root = Path(tmp)
        source = root / "source.png"
        source.write_bytes(b"\x89PNG\r\n\x1a\n")
        output = root / "generated_images" / "edited_image_test.png"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"\x89PNG\r\n\x1a\n")
        core = AssistantCore(AssistantConfig(workspace=str(root)))

        with mock.patch.object(core_module, "edit_image", return_value=ImageGenerationResult(True, "sdwebui", "Edited a real image.", str(output))):
            reply = core.chat("/image-edit source.png => make it warmer")

        assert "Edited a real image." in reply
        assert "Backend: sdwebui" in reply
        assert "Open: /view?path=generated_images/edited_image_test.png" in reply
