from __future__ import annotations

"""Small local-first document ingestion and citation helpers."""

import hashlib
import json
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class DocChunk:
    chunk_id: str
    source: str
    start_line: int
    end_line: int
    text: str


def _read_as_markdown(path: Path) -> tuple[str, str]:
    try:
        if path.suffix.lower() in {".txt", ".md", ".py", ".json", ".toml", ".yaml", ".yml"}:
            return path.read_text(encoding="utf-8", errors="replace"), "plain_text"
        if path.suffix.lower() == ".pdf":
            try:
                from pypdf import PdfReader
                reader = PdfReader(str(path))
                text = "\n\n".join(page.extract_text() or "" for page in reader.pages).strip()
                if text:
                    return text, "pypdf"
            except Exception as exc:
                pdf_error = exc
            else:
                pdf_error = RuntimeError("PDF text extraction returned no text")
        try:
            from markitdown import MarkItDown  # type: ignore
            converted = MarkItDown().convert(str(path))
            return str(converted.text_content), "markitdown"
        except Exception as exc:
            if path.suffix.lower() == ".pdf":
                raise RuntimeError(f"PDF ingestion needs pypdf or markitdown. pypdf error: {pdf_error}; markitdown error: {exc}") from exc
            return path.read_text(encoding="utf-8", errors="replace"), f"fallback_text:{exc.__class__.__name__}"
    except Exception as exc:
        raise RuntimeError(f"Could not ingest {path}: {exc}") from exc


def chunk_markdown(text: str, source: str, *, max_chars: int = 1200) -> list[DocChunk]:
    lines = text.splitlines()
    chunks: list[DocChunk] = []
    current: list[str] = []
    start_line = 1
    for idx, line in enumerate(lines, start=1):
        if not current:
            start_line = idx
        current.append(line)
        if sum(len(x) + 1 for x in current) >= max_chars:
            blob = "\n".join(current).strip()
            cid = hashlib.sha1(f"{source}:{start_line}:{idx}:{blob[:64]}".encode("utf-8", errors="ignore")).hexdigest()[:12]
            chunks.append(DocChunk(cid, source, start_line, idx, blob))
            current = []
    if current:
        end = len(lines) or 1
        blob = "\n".join(current).strip()
        cid = hashlib.sha1(f"{source}:{start_line}:{end}:{blob[:64]}".encode("utf-8", errors="ignore")).hexdigest()[:12]
        chunks.append(DocChunk(cid, source, start_line, end, blob))
    return chunks or [DocChunk("empty", source, 1, 1, "")]


def ingest_document(path: Path | str, *, out_dir: Path | str | None = None) -> dict[str, Any]:
    path = Path(path).resolve()
    text, converter = _read_as_markdown(path)
    chunks = chunk_markdown(text, path.name)
    payload = {
        "ok": True,
        "source": str(path),
        "converter": converter,
        "ingested_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "chunk_count": len(chunks),
        "chunks": [asdict(chunk) for chunk in chunks],
    }
    if out_dir:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        target = out / (path.stem + ".nova_ingest.json")
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        payload["artifact"] = str(target)
    return payload


def search_ingested_document(payload: dict[str, Any], query: str, *, limit: int = 5) -> dict[str, Any]:
    terms = [t.lower() for t in re.findall(r"[a-zA-Z0-9_]+", query or "") if len(t) > 1]
    results = []
    for chunk in payload.get("chunks", []):
        low = str(chunk.get("text", "")).lower()
        score = sum(low.count(term) for term in terms)
        if score:
            results.append({"score": score, **chunk})
    results.sort(key=lambda item: (-int(item.get("score", 0)), int(item.get("start_line", 0))))
    return {"ok": True, "query": query, "results": results[: max(1, int(limit))]}


def render_document_ingestion(payload: dict[str, Any]) -> str:
    lines = ["# Nova Document Ingestion", "", f"Source: `{payload.get('source')}`", f"Converter: `{payload.get('converter')}`", f"Chunks: **{payload.get('chunk_count')}**"]
    if payload.get("artifact"):
        lines.append(f"Artifact: `{payload.get('artifact')}`")
    lines += ["", "## Citation examples"]
    for chunk in (payload.get("chunks") or [])[:5]:
        lines.append(f"- `{chunk.get('chunk_id')}` lines {chunk.get('start_line')}-{chunk.get('end_line')}: {str(chunk.get('text',''))[:120].replace(chr(10), ' ')}")
    return "\n".join(lines)
