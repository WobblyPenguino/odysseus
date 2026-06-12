from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from nova_improvement_lab.autonomous_candidate_factory import (
    EvidenceBundle,
    build_autonomous_candidate_drafts,
    candidate_ids,
)


def _read(path: Path) -> str:
    try:
        if path.exists() and path.is_file():
            return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    return ""


def collect_research_notes(root: Path) -> str:
    research_dir = root / "docs" / "research"
    if not research_dir.exists():
        return ""

    chunks: list[str] = []
    for path in sorted(research_dir.glob("*.md")):
        chunks.append(_read(path))
    return "\n\n".join(chunk for chunk in chunks if chunk)


def build_evidence_bundle(root: Path, *, current_exhaustion_hint: str = "") -> EvidenceBundle:
    latest_summary = _read(root / "local_ai_cycles" / "memory" / "NOVA_TASK_LOOP_SUMMARY_LATEST.md")
    task_pool_exhausted = _read(root / "local_ai_cycles" / "memory" / "NOVA_TASK_POOL_EXHAUSTED_LATEST.md")
    if current_exhaustion_hint.strip():
        hint = current_exhaustion_hint.strip()
        latest_summary = "\n".join(part for part in [latest_summary, hint] if part)
        task_pool_exhausted = "\n".join(part for part in [task_pool_exhausted, hint] if part)

    return EvidenceBundle(
        roadmap=_read(root / "docs" / "NOVA_TASK_LOOP_ROADMAP.md"),
        latest_summary=latest_summary,
        task_pool_exhausted=task_pool_exhausted,
        failure_review=_read(root / "local_ai_cycles" / "memory" / "NOVA_TASK_FAILURE_REVIEW_LATEST.md"),
        audit=_read(root / "docs" / "NOVA_AUTONOMY_FULL_CODEBASE_AUDIT.md"),
        research_notes=collect_research_notes(root),
    )


def write_markdown(path: Path, candidates: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Nova Autonomous Idea Candidates Latest",
        "",
        "Purpose:",
        "- Generated locally from Nova evidence.",
        "- These are candidate drafts only.",
        "- Existing validators must accept a candidate before runtime use.",
        "",
        f"Candidate count: {len(candidates)}",
        "",
    ]

    for candidate in candidates:
        lines.extend(
            [
                f"## {candidate.get('Id', '')}",
                "",
                f"Goal: {candidate.get('Goal', '')}",
                "",
                f"Editable: {', '.join(candidate.get('Editable', []))}",
                f"RequiredChangedFiles: {', '.join(candidate.get('RequiredChangedFiles', []))}",
                f"RequiredDiffContains: {', '.join(candidate.get('RequiredDiffContains', []))}",
                f"Tests: {', '.join(candidate.get('Tests', []))}",
                "",
            ]
        )

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument(
        "--json",
        default="local_ai_cycles/config/NOVA_AUTONOMOUS_IDEA_CANDIDATES.json",
    )
    parser.add_argument(
        "--md",
        default="local_ai_cycles/memory/NOVA_AUTONOMOUS_IDEA_CANDIDATES_LATEST.md",
    )
    parser.add_argument(
        "--current-exhaustion-hint",
        default="",
        help="Current-cycle task-pool exhaustion hint supplied by the task loop before the exhaustion report is written.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    bundle = build_evidence_bundle(root, current_exhaustion_hint=args.current_exhaustion_hint)
    candidates = build_autonomous_candidate_drafts(bundle, limit=args.limit)

    json_path = root / args.json
    md_path = root / args.md

    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(candidates, indent=2) + "\n", encoding="utf-8")
    write_markdown(md_path, candidates)

    print(f"autonomous candidate count={len(candidates)}")
    print(f"autonomous candidate ids={', '.join(candidate_ids(candidates))}")
    print(f"autonomous candidate json={json_path}")
    print(f"autonomous candidate report={md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
