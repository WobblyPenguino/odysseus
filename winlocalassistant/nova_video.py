from __future__ import annotations

"""Nova manifest-first video planning helpers.

This module is intentionally dependency-light. It gives Nova a testable
"prompt -> script/scenes/shots -> manifest" control plane before any heavy
video backend such as ComfyUI, WanGP, Remotion, or FFmpeg is installed.
"""

import json
import re
import shutil
import time
from html import escape
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal
from urllib.error import URLError
from urllib.request import urlopen

Backend = Literal["comfyui", "wangp", "stock", "remotion"]
Mode = Literal["t2v", "i2v", "flf2v", "stock", "motion-graphics"]


@dataclass(slots=True)
class VideoShot:
    id: str
    scene_id: str
    backend: Backend = "comfyui"
    workflow_id: str | None = "wan22_ti2v_5b_i2v"
    mode: Mode = "i2v"
    prompt: str = ""
    negative_prompt: str = "blurry, low quality, text artefacts, extra limbs"
    duration_s: float = 4.0
    fps: int = 24
    size: str = "1280x704"
    seed: int = 42
    storyboard_image: str | None = None
    start_frame: str | None = None
    end_frame: str | None = None
    output_path: str | None = None


@dataclass(slots=True)
class AudioSpec:
    narration_script: str = ""
    voice_provider: str = "piper"
    music_mode: str = "library"
    sfx_mode: str = "library"


@dataclass(slots=True)
class VideoManifest:
    project_id: str
    title: str
    logline: str
    style: dict[str, Any] = field(default_factory=dict)
    shots: list[VideoShot] = field(default_factory=list)
    audio: AudioSpec = field(default_factory=AudioSpec)
    edit: dict[str, Any] = field(default_factory=dict)


def slugify(text: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", (text or "").strip().lower()).strip("-")
    return value[:60] or "nova-video"


def _split_scenes(prompt: str) -> list[str]:
    cleaned = (prompt or "").strip()
    parts = [p.strip() for p in re.split(r"[.;\n]+", cleaned) if p.strip()]
    if not parts:
        parts = ["A short cinematic Nova video."]
    return parts[:6]


def plan_video_manifest(prompt: str, *, project_id: str | None = None) -> VideoManifest:
    """Create a deterministic manifest-first video plan from a user prompt."""
    prompt = (prompt or "").strip() or "A short cinematic Nova video."
    project_id = project_id or f"{slugify(prompt)}-{int(time.time())}"
    title = prompt.splitlines()[0][:80].strip() or "Nova Video"
    scenes = _split_scenes(prompt)

    shots: list[VideoShot] = []
    for index, scene in enumerate(scenes, start=1):
        scene_id = f"scene_{index}"
        shot_id = f"{scene_id}_shot_1"
        shots.append(
            VideoShot(
                id=shot_id,
                scene_id=scene_id,
                prompt="cinematic video shot, coherent subject continuity, " + scene,
                seed=42 + index,
                storyboard_image=f"assets/storyboards/{shot_id}.png",
                output_path=f"renders/{shot_id}.mp4",
            )
        )

    return VideoManifest(
        project_id=project_id,
        title=title,
        logline=prompt[:240],
        style={
            "aspect_ratio": "16:9",
            "fps": 24,
            "size": "1280x704",
            "pipeline": "script -> scenes -> shots -> storyboards -> visual jobs -> audio -> edit -> final mp4",
            "primary_backend": "comfyui",
            "optional_sidecar": "wangp",
            "fallback_backends": ["stock", "remotion", "ffmpeg"],
            "workflow_policy": "generate still/storyboard anchors first, then animate where possible",
        },
        shots=shots,
        audio=AudioSpec(narration_script=prompt),
        edit={
            "clips": [shot.output_path for shot in shots],
            "subtitles": "outputs/subtitles.srt",
            "output": "outputs/final.mp4",
        },
    )


def manifest_to_dict(manifest: VideoManifest) -> dict[str, Any]:
    return asdict(manifest)


def _chunk(tag: bytes, payload: bytes) -> bytes:
    pad = b"\0" if len(payload) % 2 else b""
    return tag + len(payload).to_bytes(4, "little") + payload + pad


def _list_chunk(kind: bytes, payload: bytes) -> bytes:
    body = kind + payload
    pad = b"\0" if len(body) % 2 else b""
    return b"LIST" + len(body).to_bytes(4, "little") + body + pad


def _rgb_frame(width: int, height: int, frame_index: int, total_frames: int, shot_index: int, shot_count: int) -> bytes:
    row_pad = (4 - (width * 3) % 4) % 4
    rows: list[bytes] = []
    base_r = (48 + shot_index * 57) % 210
    base_g = (104 + shot_index * 43) % 210
    base_b = (152 + shot_index * 71) % 210
    progress = frame_index / max(total_frames - 1, 1)
    cx = int(width * (0.18 + 0.64 * progress))
    cy = int(height * (0.38 + 0.14 * ((shot_index % 3) - 1)))
    radius = max(8, min(width, height) // 8)
    band_h = max(4, height // 18)
    progress_w = int(width * progress)
    for y in range(height - 1, -1, -1):
        row = bytearray()
        for x in range(width):
            wave = (x * 37 // max(width, 1) + y * 23 // max(height, 1) + frame_index * 5) % 64
            r = (base_r + wave + x * 44 // max(width, 1)) % 256
            g = (base_g + wave + y * 52 // max(height, 1)) % 256
            b = (base_b + wave) % 256
            if (x - cx) * (x - cx) + (y - cy) * (y - cy) < radius * radius:
                r, g, b = 244, 236, 192
            if y >= height - band_h:
                if x <= progress_w:
                    r, g, b = 230, 104, 255
                else:
                    r, g, b = 28, 32, 42
            if x < 3 or y < 3 or x >= width - 3 or y >= height - 3:
                r, g, b = 8, 12, 18
            row.extend((b, g, r))
        if row_pad:
            row.extend(b"\0" * row_pad)
        rows.append(bytes(row))
    return b"".join(rows)


def write_video_preview_avi(
    manifest: VideoManifest | dict[str, Any],
    output_dir: Path | str,
    *,
    filename: str = "preview.avi",
    width: int = 320,
    height: int = 180,
    fps: int = 12,
    frames_per_shot: int = 10,
) -> Path:
    """Write a dependency-free AVI preview proving the planned shots are playable locally."""
    data = manifest_to_dict(manifest) if isinstance(manifest, VideoManifest) else dict(manifest or {})
    shots = data.get("shots") or [{"id": "scene_1_shot_1"}]
    shot_count = max(1, len(shots))
    frames_per_shot = max(2, min(int(frames_per_shot or 10), 36))
    fps = max(1, min(int(fps or 12), 30))
    width = max(64, min(int(width or 320), 640))
    height = max(48, min(int(height or 180), 360))
    total_frames = shot_count * frames_per_shot
    row_size = ((width * 3 + 3) // 4) * 4
    frame_size = row_size * height

    import struct

    avih = struct.pack(
        "<IIIIIIIIIIIIII",
        int(1_000_000 / fps),
        frame_size * fps,
        0,
        0x10,
        total_frames,
        0,
        1,
        frame_size,
        width,
        height,
        0,
        0,
        0,
        0,
    )
    strh = struct.pack(
        "<4s4sIHHIIIIIIIIiiii",
        b"vids",
        b"DIB ",
        0,
        0,
        0,
        0,
        1,
        fps,
        0,
        total_frames,
        frame_size,
        0xFFFFFFFF,
        0,
        0,
        0,
        width,
        height,
    )
    strf = struct.pack(
        "<IiiHHIIiiII",
        40,
        width,
        height,
        1,
        24,
        0,
        frame_size,
        0,
        0,
        0,
        0,
    )

    hdrl = _list_chunk(b"hdrl", _chunk(b"avih", avih) + _list_chunk(b"strl", _chunk(b"strh", strh) + _chunk(b"strf", strf)))
    movi_payload = bytearray()
    index_entries: list[bytes] = []
    offset = 4
    for shot_index in range(shot_count):
        for local_frame in range(frames_per_shot):
            frame_index = shot_index * frames_per_shot + local_frame
            payload = _rgb_frame(width, height, frame_index, total_frames, shot_index, shot_count)
            frame_chunk = _chunk(b"00db", payload)
            movi_payload.extend(frame_chunk)
            index_entries.append(struct.pack("<4sIII", b"00db", 0x10, offset, len(payload)))
            offset += len(frame_chunk)
    movi = _list_chunk(b"movi", bytes(movi_payload))
    idx1 = _chunk(b"idx1", b"".join(index_entries))
    body = b"AVI " + hdrl + movi + idx1

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename
    path.write_bytes(b"RIFF" + len(body).to_bytes(4, "little") + body)
    return path


def write_video_preview_html(manifest: VideoManifest | dict[str, Any], output_dir: Path | str, preview_video: Path | str | None = None) -> Path:
    data = manifest_to_dict(manifest) if isinstance(manifest, VideoManifest) else dict(manifest or {})
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    preview_name = Path(preview_video).name if preview_video else "preview.avi"
    shots = data.get("shots") or []
    shot_rows = "\n".join(
        f"<li><b>{escape(str(shot.get('id') or 'shot'))}</b>: {escape(str(shot.get('prompt') or ''))}</li>"
        for shot in shots
    )
    project_id = escape(str(data.get("project_id") or "nova-video"))
    final_target = escape(str((data.get("edit") or {}).get("output") or "outputs/final.mp4"))
    html = f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<title>Nova Video Proof - {project_id}</title>
<style>
body{{margin:0;background:#080b12;color:#e9edf8;font-family:Segoe UI,Arial,sans-serif}}
main{{max-width:920px;margin:0 auto;padding:28px}}
video{{width:100%;max-height:70vh;background:#000;border:1px solid #5d6b8a}}
.panel{{border:1px solid #2f3b56;background:#101726;padding:16px;margin-top:18px}}
li{{margin:8px 0}}
</style>
<main>
<h1>Nova Video Proof</h1>
<video src="{preview_name}" controls autoplay muted loop></video>
<div class="panel">
<p><b>Project:</b> {project_id}</p>
<p><b>Final target:</b> {final_target}</p>
<p>This AVI is a dependency-free local preview/proof. Final MP4 rendering still uses the configured video backend.</p>
<ol>{shot_rows}</ol>
</div>
</main>
</html>
"""
    path = output_dir / "preview.html"
    path.write_text(html, encoding="utf-8")
    return path


def save_video_manifest(prompt: str, output_dir: Path | str) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = plan_video_manifest(prompt, project_id=output_dir.name)
    path = output_dir / "manifest.json"
    path.write_text(json.dumps(manifest_to_dict(manifest), indent=2), encoding="utf-8")
    return path


def render_video_manifest_markdown(manifest: VideoManifest) -> str:
    lines = [
        "# Nova Video Manifest",
        "",
        f"Project: `{manifest.project_id}`",
        f"Title: {manifest.title}",
        f"Logline: {manifest.logline}",
        "",
        "## Pipeline",
        f"- Primary backend: `{manifest.style.get('primary_backend', 'comfyui')}`",
        f"- Optional sidecar: `{manifest.style.get('optional_sidecar', 'wangp')}`",
        f"- Fallbacks: {', '.join(str(x) for x in manifest.style.get('fallback_backends', []))}",
        "",
        "## Shots",
    ]
    for shot in manifest.shots:
        lines.append(
            f"- `{shot.id}` [{shot.backend}/{shot.mode}] {shot.duration_s:.1f}s "
            f"seed={shot.seed}: {shot.prompt}"
        )
    lines += [
        "",
        "## Audio",
        f"- Voice provider: `{manifest.audio.voice_provider}`",
        f"- Music mode: `{manifest.audio.music_mode}`",
        "",
        "## Assembly",
        f"- Clips: {', '.join(str(x) for x in manifest.edit.get('clips', []))}",
        f"- Final output: `{manifest.edit.get('output', 'outputs/final.mp4')}`",
    ]
    return "\n".join(lines)


def video_stack_status(comfy_url: str = "http://127.0.0.1:8188") -> dict[str, Any]:
    """Return local video toolchain readiness without requiring the tools."""
    tools = {
        "ffmpeg": bool(shutil.which("ffmpeg")),
        "node": bool(shutil.which("node")),
        "npx": bool(shutil.which("npx")),
    }
    comfy = {"url": comfy_url, "reachable": False, "error": ""}
    try:
        with urlopen(comfy_url.rstrip("/") + "/system_stats", timeout=2) as resp:
            comfy["reachable"] = 200 <= getattr(resp, "status", 200) < 500
    except Exception as exc:  # pragma: no cover - depends on local services
        if isinstance(exc, URLError):
            comfy["error"] = str(exc.reason)
        else:
            comfy["error"] = repr(exc)
    return {
        "ok": bool(tools.get("ffmpeg")) or bool(tools.get("node")) or comfy["reachable"],
        "tools": tools,
        "comfyui": comfy,
        "primary_backend": "comfyui",
        "fallbacks": ["stock", "remotion", "ffmpeg"],
        "note": "Nova can plan video manifests without these tools; rendering MP4 needs at least one assembly/generation backend.",
    }

# NOVA_VIDEO_VALIDATION_V55_3_151

def validate_video_manifest(manifest: VideoManifest | dict[str, Any]) -> dict[str, Any]:
    """Validate Nova's video manifest boundary before heavy render backends run."""
    data = manifest_to_dict(manifest) if isinstance(manifest, VideoManifest) else dict(manifest or {})
    issues: list[dict[str, str]] = []
    shots = data.get("shots") or []
    style = data.get("style") or {}
    edit = data.get("edit") or {}
    if not data.get("project_id"):
        issues.append({"severity": "high", "field": "project_id", "message": "project_id is required for resumable video jobs"})
    if not shots:
        issues.append({"severity": "high", "field": "shots", "message": "at least one shot is required"})
    for idx, shot in enumerate(shots):
        sid = str(shot.get("id") or f"shot_{idx+1}")
        if not shot.get("prompt"):
            issues.append({"severity": "high", "field": sid + ".prompt", "message": "shot prompt is required"})
        if float(shot.get("duration_s") or 0) <= 0:
            issues.append({"severity": "high", "field": sid + ".duration_s", "message": "duration_s must be positive"})
        if shot.get("backend") not in {"comfyui", "wangp", "stock", "remotion"}:
            issues.append({"severity": "medium", "field": sid + ".backend", "message": "unknown backend; use comfyui, wangp, stock or remotion"})
        if shot.get("backend") == "comfyui" and not shot.get("workflow_id"):
            issues.append({"severity": "medium", "field": sid + ".workflow_id", "message": "ComfyUI shots should name a verified workflow_id"})
    if style.get("primary_backend") == "comfyui" and "ffmpeg" not in (style.get("fallback_backends") or []):
        issues.append({"severity": "low", "field": "style.fallback_backends", "message": "ffmpeg fallback should remain available for assembly"})
    if not str(edit.get("output") or "").endswith(".mp4"):
        issues.append({"severity": "medium", "field": "edit.output", "message": "final output should be an .mp4 path"})
    high = [i for i in issues if i["severity"] == "high"]
    return {
        "ok": not high,
        "issue_count": len(issues),
        "issues": issues,
        "shot_count": len(shots),
        "estimated_duration_s": round(sum(float(s.get("duration_s") or 0) for s in shots), 2),
        "render_policy": "Plan and validate manifest first; render through ComfyUI/WanGP/stock/Remotion/FFmpeg only after boundary checks pass.",
    }


def build_video_execution_plan(manifest: VideoManifest | dict[str, Any]) -> dict[str, Any]:
    """Build a deterministic execution plan for future video workers."""
    data = manifest_to_dict(manifest) if isinstance(manifest, VideoManifest) else dict(manifest or {})
    shots = data.get("shots") or []
    steps: list[dict[str, Any]] = []
    for shot in shots:
        steps.append({
            "stage": "storyboard",
            "shot_id": shot.get("id"),
            "action": "create_or_select_storyboard_anchor",
            "output": shot.get("storyboard_image"),
        })
        steps.append({
            "stage": "visual_generation",
            "shot_id": shot.get("id"),
            "backend": shot.get("backend", "comfyui"),
            "workflow_id": shot.get("workflow_id"),
            "mode": shot.get("mode"),
            "output": shot.get("output_path"),
        })
    steps.extend([
        {"stage": "audio", "action": "synthesise_narration_or_use_library_fallback", "provider": (data.get("audio") or {}).get("voice_provider", "piper")},
        {"stage": "assembly", "action": "normalise_concat_subtitle_and_mix", "backend": "ffmpeg/remotion", "output": (data.get("edit") or {}).get("output", "outputs/final.mp4")},
        {"stage": "qa", "action": "verify_manifest_outputs_and_retry_failed_shots", "fallbacks": (data.get("style") or {}).get("fallback_backends", [])},
    ])
    return {"ok": True, "steps": steps, "step_count": len(steps), "note": "Execution plan is dry-run/testable until render backends are installed."}


def render_video_validation_markdown(validation: dict[str, Any], execution: dict[str, Any] | None = None) -> str:
    lines = [
        "# Nova Video Validation",
        "",
        f"Status: {'PASS' if validation.get('ok') else 'REVIEW'}",
        f"Shots: {validation.get('shot_count', 0)}",
        f"Estimated duration: {validation.get('estimated_duration_s', 0)}s",
        "",
        validation.get("render_policy", ""),
    ]
    if validation.get("issues"):
        lines += ["", "## Issues"]
        for issue in validation.get("issues", []):
            lines.append(f"- {issue.get('severity','?').upper()} `{issue.get('field','')}` — {issue.get('message','')}")
    if execution:
        lines += ["", "## Execution plan"]
        for step in execution.get("steps", [])[:30]:
            bits = [str(step.get("stage", "step"))]
            if step.get("shot_id"):
                bits.append(str(step.get("shot_id")))
            if step.get("backend"):
                bits.append(str(step.get("backend")))
            if step.get("action"):
                bits.append(str(step.get("action")))
            lines.append("- " + " / ".join(bits))
    return "\n".join(lines)


def video_user_test_scenarios() -> list[dict[str, Any]]:
    """Manual/simulated user tests for Nova video UX."""
    return [
        {"name": "tiny_trailer", "prompt": "10 second cinematic trailer about Nova building a project", "expect": ["manifest.json", "shots", "final.mp4"]},
        {"name": "continuity_edit", "prompt": "make shot 2 moodier but keep character continuity", "expect": ["same project_id", "changed shot prompt only", "retry plan"]},
        {"name": "backend_missing", "prompt": "video when ComfyUI is offline", "expect": ["status explains fallback", "manifest still produced", "no crash"]},
    ]


# NOVA_MEDIA_V55_3_160

def build_video_image_prompt_plan(manifest: VideoManifest | dict[str, Any]) -> dict[str, Any]:
    """Map each video shot to storyboard, keyframe and final-frame image prompts."""
    data = manifest_to_dict(manifest) if isinstance(manifest, VideoManifest) else dict(manifest or {})
    shots = data.get("shots") or []
    items: list[dict[str, Any]] = []
    for idx, shot in enumerate(shots, start=1):
        base = str(shot.get("prompt") or "cinematic Nova shot")
        items.append({
            "shot_id": shot.get("id") or f"shot_{idx}",
            "storyboard_prompt": f"storyboard frame, clean readable composition, {base}",
            "start_keyframe_prompt": f"first frame for image-to-video, stable subject identity, {base}",
            "end_keyframe_prompt": f"final frame for image-to-video, consistent subject and camera direction, {base}",
            "negative_prompt": shot.get("negative_prompt") or "blurry, low quality, text artifacts",
            "seed": shot.get("seed", 42) + 1000,
            "size": shot.get("size", "1280x704"),
        })
    return {"ok": True, "project_id": data.get("project_id"), "shot_count": len(items), "items": items}


def write_storyboard_svg(manifest: VideoManifest | dict[str, Any], output_dir: Path | str, *, filename: str = "storyboard.svg") -> Path:
    """Write a dependency-free visual storyboard sheet for the planned video."""
    data = manifest_to_dict(manifest) if isinstance(manifest, VideoManifest) else dict(manifest or {})
    shots = data.get("shots") or []
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    cols = 2
    card_w, card_h = 520, 300
    rows = max(1, (len(shots) + cols - 1) // cols)
    width, height = cols * card_w + 60, rows * card_h + 120
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    parts.append('<rect width="100%" height="100%" fill="#080b12"/>')
    title = escape(str(data.get("title") or "Nova Video Storyboard"))
    parts.append(f'<text x="30" y="42" fill="#e9d5ff" font-family="Segoe UI, Arial" font-size="26" font-weight="700">{title}</text>')
    for idx, shot in enumerate(shots or [{"id": "shot_1", "prompt": "Nova video shot"}]):
        col = idx % cols
        row = idx // cols
        x = 30 + col * card_w
        y = 70 + row * card_h
        hue = (idx * 47) % 360
        sid = escape(str(shot.get("id") or f"shot_{idx+1}"))
        prompt = escape(str(shot.get("prompt") or "")[:180])
        parts.append(f'<rect x="{x}" y="{y}" width="{card_w-24}" height="{card_h-28}" rx="18" fill="hsl({hue},45%,16%)" stroke="#a855f7" stroke-width="2"/>')
        parts.append(f'<rect x="{x+18}" y="{y+18}" width="{card_w-60}" height="150" rx="14" fill="hsl({hue},55%,28%)"/>')
        parts.append(f'<circle cx="{x+90}" cy="{y+92}" r="36" fill="#fef3c7" opacity="0.95"/>')
        parts.append(f'<path d="M{x+170} {y+145} C{x+240} {y+80}, {x+340} {y+110}, {x+440} {y+45}" fill="none" stroke="#f0abfc" stroke-width="7" stroke-linecap="round" opacity="0.8"/>')
        parts.append(f'<text x="{x+18}" y="{y+200}" fill="#ffffff" font-family="Segoe UI, Arial" font-size="18" font-weight="700">{sid}</text>')
        # wrap prompt crudely in 2 lines
        line1, line2 = prompt[:80], prompt[80:160]
        parts.append(f'<text x="{x+18}" y="{y+230}" fill="#dbeafe" font-family="Segoe UI, Arial" font-size="14">{line1}</text>')
        if line2:
            parts.append(f'<text x="{x+18}" y="{y+252}" fill="#dbeafe" font-family="Segoe UI, Arial" font-size="14">{line2}</text>')
    parts.append('</svg>')
    path = output_dir / filename
    path.write_text("\n".join(parts), encoding="utf-8")
    return path


def write_shotlist_csv(manifest: VideoManifest | dict[str, Any], output_dir: Path | str, *, filename: str = "shotlist.csv") -> Path:
    data = manifest_to_dict(manifest) if isinstance(manifest, VideoManifest) else dict(manifest or {})
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    import csv
    path = output_dir / filename
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "scene_id", "backend", "mode", "duration_s", "fps", "size", "seed", "prompt", "output_path"])
        writer.writeheader()
        for shot in data.get("shots") or []:
            writer.writerow({k: shot.get(k, "") for k in writer.fieldnames})
    return path


def build_ffmpeg_assembly_plan(manifest: VideoManifest | dict[str, Any]) -> dict[str, Any]:
    data = manifest_to_dict(manifest) if isinstance(manifest, VideoManifest) else dict(manifest or {})
    clips = [str(x) for x in (data.get("edit") or {}).get("clips", [])]
    output = str((data.get("edit") or {}).get("output") or "outputs/final.mp4")
    concat_lines = [f"file '{clip}'" for clip in clips]
    commands = [
        "# Write these lines to concat.txt after shot clips exist:",
        *concat_lines,
        "",
        "# Then assemble:",
        f"ffmpeg -y -f concat -safe 0 -i concat.txt -c:v libx264 -pix_fmt yuv420p -movflags +faststart {output}",
    ]
    return {"ok": True, "clips": clips, "output": output, "concat_txt": "\n".join(concat_lines), "commands": commands}


def write_video_render_package(prompt: str, output_dir: Path | str) -> dict[str, Any]:
    """Create a full safe video planning package before expensive rendering."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = plan_video_manifest(prompt, project_id=output_dir.name)
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest_to_dict(manifest), indent=2), encoding="utf-8")
    preview = write_video_preview_avi(manifest, output_dir)
    preview_html = write_video_preview_html(manifest, output_dir, preview)
    storyboard = write_storyboard_svg(manifest, output_dir)
    shotlist = write_shotlist_csv(manifest, output_dir)
    validation = validate_video_manifest(manifest)
    execution = build_video_execution_plan(manifest)
    validation_md = output_dir / "VIDEO_VALIDATION.md"
    validation_md.write_text(render_video_validation_markdown(validation, execution), encoding="utf-8")
    prompt_plan = build_video_image_prompt_plan(manifest)
    prompt_plan_path = output_dir / "video_image_prompts.json"
    prompt_plan_path.write_text(json.dumps(prompt_plan, indent=2), encoding="utf-8")
    ffmpeg = build_ffmpeg_assembly_plan(manifest)
    ffmpeg_path = output_dir / "ffmpeg_assembly_plan.txt"
    ffmpeg_path.write_text("\n".join(ffmpeg.get("commands", [])), encoding="utf-8")
    return {
        "ok": bool(validation.get("ok")),
        "project_dir": str(output_dir),
        "manifest_path": str(manifest_path),
        "preview_video_path": str(preview),
        "preview_html_path": str(preview_html),
        "storyboard_path": str(storyboard),
        "shotlist_path": str(shotlist),
        "validation_path": str(validation_md),
        "image_prompts_path": str(prompt_plan_path),
        "ffmpeg_plan_path": str(ffmpeg_path),
        "manifest": manifest_to_dict(manifest),
        "validation": validation,
        "execution_plan": execution,
        "image_prompt_plan": prompt_plan,
        "ffmpeg_plan": ffmpeg,
    }


def render_video_render_package_markdown(package: dict[str, Any]) -> str:
    lines = [
        "# Nova Video Render Package",
        "",
        f"Status: {'PASS' if package.get('ok') else 'REVIEW'}",
        f"Project folder: `{package.get('project_dir')}`",
        "",
        "## Files written",
    ]
    for key in ["manifest_path", "storyboard_path", "shotlist_path", "image_prompts_path", "preview_video_path", "preview_html_path", "validation_path", "ffmpeg_plan_path"]:
        lines.append(f"- {key}: `{package.get(key,'')}`")
    validation = package.get("validation") or {}
    lines += ["", "## Validation", f"- Shots: {validation.get('shot_count', 0)}", f"- Estimated duration: {validation.get('estimated_duration_s', 0)}s", f"- Issues: {validation.get('issue_count', 0)}"]
    lines += ["", "## How to continue", "- Review `storyboard.svg` and `video_image_prompts.json` before rendering.", "- Generate storyboard/keyframes with `/image-generate` or your chosen image backend.", "- Render/animate shots through ComfyUI/WanGP/Remotion when available.", "- Use `ffmpeg_assembly_plan.txt` once shot clips exist."]
    return "\n".join(lines)


def media_status_summary(image_status: dict[str, Any] | None = None, video_status: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "ok": True,
        "image": image_status or {},
        "video": video_status or {},
        "recommended_flow": [
            "/image-plan PROMPT to create prompt variants before heavy generation",
            "/image-status to confirm SD WebUI/Diffusers readiness",
            "/video-package PROMPT to create manifest/storyboard/preview/shotlist",
            "/video-status to confirm FFmpeg/Node/ComfyUI readiness",
        ],
    }
