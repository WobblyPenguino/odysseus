from __future__ import annotations

import base64
import json
import mimetypes
import os
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .safe_io import atomic_write_bytes, atomic_write_json, read_json_file, atomic_write_text

from .config import APP_DIR

MAX_TEXT_BYTES = 120_000
MAX_CONTEXT_CHARS = 16_000
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
CONTEXT_DIR_NAME = "shared_file_context"
TEXT_EXTS = {".txt", ".md", ".py", ".js", ".html", ".css", ".json", ".csv", ".xml", ".yaml", ".yml", ".toml", ".ini", ".log"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"}


@dataclass
class SharedFileContext:
    context_id: str
    original_name: str
    stored_path: str
    kind: str
    mime_type: str
    size_bytes: int
    summary: str
    context_text: str
    created_at: str
    source: str = "upload"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _now_id() -> str:
    return time.strftime("%Y%m%d_%H%M%S") + f"_{int(time.time() * 1000) % 1000:03d}"


def _safe_name(name: str) -> str:
    base = Path(name or "shared_file").name
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base).strip("._") or "shared_file"
    return base[:90]


def context_dir(profile_dir: Path | None = None) -> Path:
    root = Path(profile_dir) if profile_dir else APP_DIR
    return root / CONTEXT_DIR_NAME


def _detect_kind(path: Path, mime: str = "") -> str:
    ext = path.suffix.lower()
    if ext in IMAGE_EXTS or mime.startswith("image/"):
        return "image"
    if ext in TEXT_EXTS or mime.startswith("text/"):
        return "text"
    if ext == ".pdf" or mime == "application/pdf":
        return "pdf"
    return "binary"


def _read_text_sample(path: Path) -> str:
    data = path.read_bytes()[:MAX_TEXT_BYTES]
    for enc in ["utf-8", "utf-8-sig", "cp1252", "latin-1"]:
        try:
            text = data.decode(enc, errors="replace")
            break
        except Exception:
            continue
    else:
        text = data.decode("utf-8", errors="replace")
    if len(text) > MAX_CONTEXT_CHARS:
        text = text[:MAX_CONTEXT_CHARS] + "\n...[truncated for prompt context]"
    return text


def _png_size(data: bytes) -> tuple[int, int] | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
    return None


def _gif_size(data: bytes) -> tuple[int, int] | None:
    if (data.startswith(b"GIF87a") or data.startswith(b"GIF89a")) and len(data) >= 10:
        return int.from_bytes(data[6:8], "little"), int.from_bytes(data[8:10], "little")
    return None


def _jpeg_size(data: bytes) -> tuple[int, int] | None:
    if not data.startswith(b"\xff\xd8"):
        return None
    # JPEG dimensions live in Start Of Frame segments. Do not treat non-SOF
    # markers such as DHT (0xC4), JPG (0xC8), or DAC (0xCC) as dimensions.
    sof_markers = {
        0xC0, 0xC1, 0xC2, 0xC3,
        0xC5, 0xC6, 0xC7,
        0xC9, 0xCA, 0xCB,
        0xCD, 0xCE, 0xCF,
    }
    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        i += 2
        while marker == 0xFF and i < len(data):
            marker = data[i]
            i += 1
        if marker in {0xD8, 0xD9} or 0xD0 <= marker <= 0xD7:
            continue
        if i + 2 > len(data):
            break
        length = int.from_bytes(data[i:i + 2], "big")
        if length < 2 or i + length > len(data):
            break
        if marker in sof_markers and i + 7 <= len(data):
            h = int.from_bytes(data[i + 3:i + 5], "big")
            w = int.from_bytes(data[i + 5:i + 7], "big")
            return w, h
        i += length
    return None


def _svg_size(text: str) -> tuple[int, int] | None:
    match = re.search(r"<svg[^>]+(?:width=[\"']([0-9.]+)[\"'][^>]+height=[\"']([0-9.]+)[\"']|height=[\"']([0-9.]+)[\"'][^>]+width=[\"']([0-9.]+)[\"'])", text, re.I)
    if match:
        w = match.group(1) or match.group(4)
        h = match.group(2) or match.group(3)
        try:
            return int(float(w)), int(float(h))
        except Exception:
            return None
    viewbox = re.search(r"viewBox=[\"'][^\"']*?\s([0-9.]+)\s+([0-9.]+)[\"']", text, re.I)
    if viewbox:
        try:
            return int(float(viewbox.group(1))), int(float(viewbox.group(2)))
        except Exception:
            return None
    return None


def image_size(path: Path) -> tuple[int, int] | None:
    try:
        if path.suffix.lower() == ".svg":
            return _svg_size(path.read_text(encoding="utf-8", errors="replace")[:10000])
        data = path.read_bytes()[:512_000]
        return _png_size(data) or _gif_size(data) or _jpeg_size(data)
    except Exception:
        return None


def summarize_file(path: Path, kind: str, mime: str) -> tuple[str, str]:
    size = path.stat().st_size
    if kind == "text":
        sample = _read_text_sample(path)
        lines = sample.count("\n") + 1 if sample else 0
        summary = f"Text file {path.name} ({size} bytes, approx {lines} sampled lines)."
        context = f"Attached text file: {path.name}\nSize: {size} bytes\n--- File excerpt ---\n{sample}"
        return summary, context
    if kind == "image":
        dims = image_size(path)
        dim_text = f", {dims[0]}x{dims[1]}" if dims else ""
        summary = f"Image file {path.name} ({mime or 'image'}, {size} bytes{dim_text}). Use /image-analyze for vision-model analysis."
        context = f"Attached image: {path.name}\nType: {mime or path.suffix}\nSize: {size} bytes{dim_text}\nNote: Nova can pass this image to /image-analyze if a vision model is configured."
        return summary, context
    if kind == "pdf":
        summary = f"PDF file {path.name} ({size} bytes). PDF text extraction is not built in; use this as metadata unless converted to text."
        context = f"Attached PDF metadata: {path.name}\nSize: {size} bytes\nNote: Convert or paste text if exact PDF contents are needed."
        return summary, context
    summary = f"Binary file {path.name} ({size} bytes, {mime or 'unknown type'})."
    context = f"Attached binary file metadata: {path.name}\nSize: {size} bytes\nType: {mime or 'unknown'}\nNote: Binary contents are not inserted into prompts."
    return summary, context


def register_file_context_from_path(path: str | Path, *, profile_dir: Path | None = None, source: str = "local_path") -> SharedFileContext:
    src = Path(path).expanduser()
    if not src.exists() or not src.is_file():
        raise FileNotFoundError(f"File not found: {src}")
    out = context_dir(profile_dir)
    out.mkdir(parents=True, exist_ok=True)
    cid = _now_id()
    name = _safe_name(src.name)
    stored = out / f"{cid}_{name}"
    data = src.read_bytes()
    atomic_write_bytes(stored, data)
    return _context_from_stored(stored, original_name=src.name, context_id=cid, source=source)


def register_uploaded_file(name: str, data: bytes, *, mime_type: str = "", profile_dir: Path | None = None) -> SharedFileContext:
    if len(data) > MAX_UPLOAD_BYTES:
        raise ValueError(f"Upload is too large: {len(data)} bytes. Limit is {MAX_UPLOAD_BYTES} bytes.")
    out = context_dir(profile_dir)
    out.mkdir(parents=True, exist_ok=True)
    cid = _now_id()
    stored = out / f"{cid}_{_safe_name(name)}"
    atomic_write_bytes(stored, data)
    return _context_from_stored(stored, original_name=name, context_id=cid, source="upload", mime_type=mime_type)


def _context_from_stored(stored: Path, *, original_name: str, context_id: str, source: str, mime_type: str = "") -> SharedFileContext:
    mime = mime_type or mimetypes.guess_type(original_name or str(stored))[0] or ""
    kind = _detect_kind(Path(original_name), mime)
    summary, context_text = summarize_file(stored, kind, mime)
    ctx = SharedFileContext(
        context_id=context_id,
        original_name=original_name,
        stored_path=str(stored),
        kind=kind,
        mime_type=mime,
        size_bytes=stored.stat().st_size,
        summary=summary,
        context_text=context_text,
        created_at=time.strftime("%Y-%m-%d %H:%M:%S"),
        source=source,
    )
    atomic_write_json(stored.with_suffix(stored.suffix + ".context.json"), ctx.to_dict(), ensure_ascii=True)
    return ctx


def list_file_contexts(*, profile_dir: Path | None = None, limit: int = 12) -> list[SharedFileContext]:
    root = context_dir(profile_dir)
    if not root.exists():
        return []
    items: list[SharedFileContext] = []
    for meta in sorted(root.glob("*.context.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]:
        try:
            data = read_json_file(meta, {}, expected_type=dict, quarantine=True)
            items.append(SharedFileContext(**data))
        except Exception:
            continue
    return items


def clear_file_contexts(*, profile_dir: Path | None = None) -> int:
    root = context_dir(profile_dir)
    if not root.exists():
        return 0
    count = 0
    for path in root.iterdir():
        if path.is_file():
            try:
                path.unlink()
                count += 1
            except Exception:
                import logging as _wla_logging
                _wla_logging.getLogger(__name__).debug("Suppressed optional exception", exc_info=True)
    return count



def image_file_contexts(*, profile_dir: Path | None = None, limit: int = 20) -> list[SharedFileContext]:
    return [ctx for ctx in list_file_contexts(profile_dir=profile_dir, limit=limit) if ctx.kind == "image"]


def resolve_image_context(identifier: str = "", *, profile_dir: Path | None = None) -> SharedFileContext | None:
    """Resolve an uploaded/attached image by id, name, or latest/last.

    This lets /image-analyze work with web-uploaded photos, because those are
    stored in Nova's shared context directory rather than inside the project
    workspace.
    """
    raw = (identifier or "").strip().strip('"').strip("'")
    key = raw.lower()
    for prefix in ["context:", "ctx:", "id:"]:
        if key.startswith(prefix):
            key = key[len(prefix):].strip()
            raw = raw[len(prefix):].strip()
            break
    images = image_file_contexts(profile_dir=profile_dir, limit=50)
    if not images:
        return None
    if not raw or key in {"latest", "last", "photo", "image", "uploaded", "upload"}:
        return images[0]
    for ctx in images:
        if ctx.context_id == raw or ctx.context_id.lower().startswith(key):
            return ctx
    for ctx in images:
        if ctx.original_name.lower() == key or Path(ctx.stored_path).name.lower() == key:
            return ctx
    for ctx in images:
        if key in ctx.original_name.lower() or key in Path(ctx.stored_path).name.lower():
            return ctx
    return None

def build_prompt_context(contexts: list[SharedFileContext], *, max_chars: int = 22_000) -> str:
    parts = []
    used = 0
    for ctx in contexts:
        block = f"\n\n[Shared file context: {ctx.original_name} | {ctx.kind} | id={ctx.context_id}]\n{ctx.context_text}"
        if used + len(block) > max_chars:
            parts.append("\n\n[Additional shared file context omitted because prompt context limit was reached.]")
            break
        parts.append(block)
        used += len(block)
    return "".join(parts)


def create_svg_image(prompt: str, *, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9 _.-]+", "", prompt or "generated image").strip()[:80] or "generated image"
    path = output_dir / f"generated_image_{_now_id()}.svg"
    title = safe.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    svg = f"""<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1024\" height=\"640\" viewBox=\"0 0 1024 640\">
  <defs><linearGradient id=\"g\" x1=\"0\" x2=\"1\" y1=\"0\" y2=\"1\"><stop stop-color=\"#dbeafe\"/><stop offset=\"1\" stop-color=\"#f8fafc\"/></linearGradient></defs>
  <rect width=\"1024\" height=\"640\" fill=\"url(#g)\"/>
  <rect x=\"72\" y=\"82\" width=\"880\" height=\"476\" rx=\"32\" fill=\"white\" stroke=\"#2563eb\" stroke-width=\"4\"/>
  <text x=\"512\" y=\"230\" text-anchor=\"middle\" font-family=\"Segoe UI, Arial\" font-size=\"42\" font-weight=\"700\" fill=\"#0f172a\">Generated image draft</text>
  <text x=\"512\" y=\"305\" text-anchor=\"middle\" font-family=\"Segoe UI, Arial\" font-size=\"26\" fill=\"#1e3a8a\">{title}</text>
  <text x=\"512\" y=\"390\" text-anchor=\"middle\" font-family=\"Segoe UI, Arial\" font-size=\"20\" fill=\"#475569\">Local SVG placeholder. Connect an image model for photoreal generation.</text>
</svg>\n"""
    atomic_write_text(path, svg)
    return path
