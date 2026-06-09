from __future__ import annotations

import json

from winlocalassistant.nova_video import (
    plan_video_manifest,
    render_video_manifest_markdown,
    save_video_manifest,
    video_stack_status,
    write_video_preview_avi,
    write_video_preview_html,
)


def test_nova_video_manifest_plans_script_to_shots(tmp_path):
    prompt = "Rainy neon alley. Courier finds a coded radio signal. Drone shot over city."
    manifest = plan_video_manifest(prompt, project_id="demo-video")

    assert manifest.project_id == "demo-video"
    assert len(manifest.shots) >= 3
    assert manifest.shots[0].backend == "comfyui"
    assert manifest.shots[0].workflow_id == "wan22_ti2v_5b_i2v"
    assert manifest.edit["output"] == "outputs/final.mp4"
    assert "ffmpeg" in manifest.style["fallback_backends"]


def test_nova_video_manifest_can_be_saved(tmp_path):
    path = save_video_manifest("Make a 10 second cinematic ocean science video", tmp_path / "video_job")
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["project_id"] == "video_job"
    assert data["shots"]
    assert data["audio"]["voice_provider"] == "piper"
    assert data["edit"]["output"].endswith(".mp4")


def test_nova_video_preview_proof_can_be_saved_without_ffmpeg(tmp_path):
    manifest = plan_video_manifest("Nova plans, validates and previews a tiny movie", project_id="proof-video")
    avi = write_video_preview_avi(manifest, tmp_path / "video_job")
    html = write_video_preview_html(manifest, tmp_path / "video_job", avi)

    data = avi.read_bytes()
    assert data.startswith(b"RIFF")
    assert b"AVI " in data[:16]
    assert avi.stat().st_size > 100_000
    assert html.exists()
    assert "preview.avi" in html.read_text(encoding="utf-8")


def test_nova_video_manifest_markdown_mentions_pipeline():
    manifest = plan_video_manifest("A robot builds a tiny app")
    text = render_video_manifest_markdown(manifest)

    assert "Nova Video Manifest" in text
    assert "Primary backend" in text
    assert "Shots" in text
    assert "Final output" in text


def test_nova_video_stack_status_is_read_only():
    status = video_stack_status("http://127.0.0.1:9")
    assert "tools" in status
    assert "comfyui" in status
    assert status["primary_backend"] == "comfyui"
