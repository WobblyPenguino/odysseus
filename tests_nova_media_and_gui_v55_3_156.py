from __future__ import annotations

from pathlib import Path

from winlocalassistant.image_generation import create_svg_draft
from winlocalassistant.nova_video import plan_video_manifest, write_video_preview_avi, write_video_preview_html

WEBUI = Path("winlocalassistant/webui.py").read_text(encoding="utf-8", errors="replace")


def test_live_activity_scroll_controls_are_present():
    for marker in [
        "activityScrollBtn",
        "toggleActivityAutoScroll",
        "activityShouldPreserveScroll",
        "restoreActivityScroll",
        "novaActivityAutoScrollLatest",
    ]:
        assert marker in WEBUI


def test_gui_exposes_safe_authority_and_subagent_buttons():
    assert "/authority-mode" in WEBUI
    assert "/allow-internet on" in WEBUI
    assert "/subagents improve Nova without regressions" in WEBUI
    assert "/autonomous start --continuous" in WEBUI


def test_media_proof_artifacts_can_be_generated_without_heavy_backends(tmp_path):
    image = create_svg_draft("neon rabbit mascot for Nova", output_dir=tmp_path / "images")
    assert image.exists()
    assert "SVG draft only" in image.read_text(encoding="utf-8")
    manifest = plan_video_manifest("Nova builds a project, validates it, and shows proof", project_id="media-proof")
    avi = write_video_preview_avi(manifest, tmp_path / "video")
    html = write_video_preview_html(manifest, tmp_path / "video", avi)
    assert avi.exists() and avi.read_bytes().startswith(b"RIFF")
    assert html.exists() and "preview.avi" in html.read_text(encoding="utf-8")
