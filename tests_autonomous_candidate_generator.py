import json
from pathlib import Path

from tools.generate_autonomous_idea_candidates import (
    build_evidence_bundle,
    collect_research_notes,
    main,
)


def test_generator_collects_research_notes(tmp_path: Path) -> None:
    research = tmp_path / "docs" / "research"
    research.mkdir(parents=True)
    (research / "a.md").write_text("Agent Browser evidence", encoding="utf-8")
    (research / "b.md").write_text("Validation evidence", encoding="utf-8")

    notes = collect_research_notes(tmp_path)

    assert "Agent Browser evidence" in notes
    assert "Validation evidence" in notes


def test_generator_builds_evidence_bundle_from_known_paths(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "local_ai_cycles" / "memory").mkdir(parents=True)

    (tmp_path / "docs" / "NOVA_TASK_LOOP_ROADMAP.md").write_text("roadmap", encoding="utf-8")
    (tmp_path / "local_ai_cycles" / "memory" / "NOVA_TASK_LOOP_SUMMARY_LATEST.md").write_text(
        "task-pool-exhausted",
        encoding="utf-8",
    )

    bundle = build_evidence_bundle(tmp_path)

    assert bundle.roadmap == "roadmap"
    assert "task-pool-exhausted" in bundle.latest_summary


def test_generator_cli_writes_json_and_markdown(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "local_ai_cycles" / "memory").mkdir(parents=True)
    (tmp_path / "local_ai_cycles" / "memory" / "NOVA_TASK_LOOP_SUMMARY_LATEST.md").write_text(
        "No sufficiently productive task remained.",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "generate_autonomous_idea_candidates.py",
            "--root",
            str(tmp_path),
            "--json",
            "out/candidates.json",
            "--md",
            "out/candidates.md",
        ],
    )

    assert main() == 0

    data = json.loads((tmp_path / "out" / "candidates.json").read_text(encoding="utf-8"))
    report = (tmp_path / "out" / "candidates.md").read_text(encoding="utf-8")

    assert data
    assert data[0]["Id"] == "candidate-factory-pool-exhaustion-summary-v1"
    assert "Nova Autonomous Idea Candidates Latest" in report
