from __future__ import annotations

"""Comprehensive integration review for Nova's repo-inspired roadmap."""

import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .browser_worker import build_browser_task_plan
from .document_ingestion import ingest_document, search_ingested_document
from .model_registry import build_model_registry
from .nova_video import plan_video_manifest, validate_video_manifest
from .orchestration_foundation import JobQueue, NovaState, NovaStateMachine, validate_transition
from .repo_intelligence import build_patch_plan, build_repo_map


def build_integration_review(root: Path | str) -> dict[str, Any]:
    root = Path(root).resolve()
    repo_map = build_repo_map(root, max_files=260)
    state_machine = NovaStateMachine(NovaState.IDLE)
    transitions = [
        state_machine.transition(NovaState.PROCESSING, "test processing state"),
        validate_transition(NovaState.PROCESSING, NovaState.LISTENING, interrupt_enabled=False),
    ]
    queue = JobQueue(root / ".nova_runtime" / "integration_review_jobs.sqlite3")
    queued = queue.enqueue("review", "integration review smoke job", {"source": "integration_review"}, dedupe_key="integration-review-smoke")
    video_manifest = plan_video_manifest("A 10 second Nova trailer showing planning, testing and final delivery", project_id="integration-review-video")
    video_validation = validate_video_manifest(video_manifest)
    browser_plan = build_browser_task_plan("read a local documentation page and capture screenshot evidence")
    doc_payload = ingest_document(root / "README.md") if (root / "README.md").exists() else {"ok": False, "chunks": []}
    doc_search = search_ingested_document(doc_payload, "Nova local assistant", limit=3) if doc_payload.get("ok") else {"ok": False, "results": []}
    model_registry = build_model_registry()
    patch_plan = build_patch_plan("continue Nova integration improvements safely", repo_map)

    checks = [
        {"name": "state_machine_blocks_busy_listening", "ok": transitions[-1].ok is False},
        {"name": "durable_job_queue", "ok": bool(queued.job_id)},
        {"name": "repo_map_has_entrypoints", "ok": bool(repo_map.get("entrypoints"))},
        {"name": "video_manifest_valid", "ok": bool(video_validation.get("ok"))},
        {"name": "browser_worker_is_read_only_by_default", "ok": browser_plan.get("classification", {}).get("read_only") is True},
        {"name": "document_ingestion_chunks_readme", "ok": bool(doc_payload.get("chunks"))},
        {"name": "patch_plan_has_validation", "ok": bool(patch_plan.get("validation_commands"))},
    ]
    gaps = []
    if not model_registry.get("ok"):
        gaps.append("Local role models are not all installed/reachable in this environment; keep model checks advisory in CI.")
    if not (root / "winlocalassistant" / "webui.py").exists():
        gaps.append("GUI webui.py missing; browser smoke cannot run.")
    if not (root / "tests_nova_video_validation_v55_3_151.py").exists():
        gaps.append("Video validation test missing.")

    return {
        "ok": all(c["ok"] for c in checks),
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "checks": checks,
        "gaps": gaps,
        "repo_map_summary": {
            "files": len(repo_map.get("files", [])),
            "tests": len(repo_map.get("tests", [])),
            "entrypoints": repo_map.get("entrypoints", []),
            "risk_flags": repo_map.get("risk_flags", [])[:20],
        },
        "state_machine": [asdict(t) for t in transitions],
        "queue_summary": queue.summary(),
        "video_validation": video_validation,
        "browser_plan": browser_plan,
        "document_search_preview": doc_search,
        "model_registry": model_registry,
        "patch_plan": patch_plan,
        "research_alignment": [
            "OpenHands-style lifecycle: state machine + durable jobs + worker separation",
            "Aider-style repo map + patch plan + validation commands before edits",
            "browser-use/Playwright-style browser worker as a permission-gated plan with evidence",
            "MarkItDown-style document ingestion with chunks/citations when dependency is present",
            "ComfyUI/Remotion/FFmpeg video path kept manifest-first and backend-separated",
        ],
    }


def render_integration_review(payload: dict[str, Any]) -> str:
    lines = ["# Nova Comprehensive Integration Review", "", f"Status: {'PASS' if payload.get('ok') else 'REVIEW'}", f"Generated: {payload.get('generated_at')}", "", "## Checks"]
    for c in payload.get("checks", []):
        lines.append(f"- {'✅' if c.get('ok') else '❌'} {c.get('name')}")
    if payload.get("gaps"):
        lines += ["", "## Gaps / advisory notes", *[f"- {g}" for g in payload.get("gaps", [])]]
    r = payload.get("repo_map_summary", {})
    lines += ["", "## Repo map", f"- Files summarized: **{r.get('files')}**", f"- Tests found: **{r.get('tests')}**", f"- Entrypoints: {', '.join(r.get('entrypoints', []))}"]
    if r.get("risk_flags"):
        lines += ["", "## Risk flags sampled", *[f"- {x}" for x in r.get("risk_flags", [])[:12]]]
    lines += ["", "## Research alignment", *[f"- {x}" for x in payload.get("research_alignment", [])]]
    return "\n".join(lines)
