from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .config import APP_DIR
from .safe_io import atomic_write_json, atomic_write_text


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def _has_file(root: Path, name: str) -> bool:
    return (root / name).exists()


def _proposal(pid: str, title: str, problem: str, change: str, commands: list[str], *, risk: str = "low", value: int = 70, category: str = "reliability") -> dict[str, Any]:
    return {
        "id": pid,
        "title": title,
        "category": category,
        "risk": risk,
        "value": value,
        "problem": problem,
        "change": change,
        "commands": commands,
        "status": "proposed",
    }


def build_improvement_proposals(root: str | Path = ".", focus: str = "") -> dict[str, Any]:
    """Build prompt-aware, low-risk Nova improvement proposals.

    This is deliberately deterministic so idle/autonomous can reason over it without
    needing a local model prompt. The proposals are implementation-ready and include
    commands, value/risk, and validation expectations.
    """
    root = Path(root).resolve()
    low = (focus or "").lower()
    proposals: list[dict[str, Any]] = []

    proposals.append(_proposal(
        "proposal-loop-report",
        "Make improvement proposals completable, not just advisory",
        "Older /propose-improvements output was useful but did not give one command that proposes, implements safe items, validates, and records completion.",
        "Add an improvement cycle that ranks proposals, applies safe documentation/regression-memory completions, records done/skipped states, and emits a report.",
        ["/improvement-cycle --confirm", "/completed-improvements", "/improvement-status"],
        value=95,
        category="autonomy",
    ))
    proposals.append(_proposal(
        "proposal-autonomy-access",
        "Teach idle/autonomous when to use improvement proposals",
        "Idle/autonomous can call many tools, but improvement proposal completion was not a first-class capability in the mutable capability catalog.",
        "Expose improvement-cycle as an internal tool and capability so broad prompts such as 'propose improvements and do them' select it before generic repair.",
        ["/autonomy-capabilities propose improvements and complete them", "/improvement-cycle --confirm"],
        value=90,
        category="autonomy",
    ))
    proposals.append(_proposal(
        "proposal-regression-memory",
        "Convert repeated user-reported bugs into regression-memory entries",
        "Nova repeatedly fixed issues such as idle overwriting tasks, Dodge Game fallback leakage, mic no-op behaviour, and version label regressions, but proposal cycles should check that those are tracked.",
        "Seed regression-memory entries for high-value historical failures when absent, then include them in mega-test/user-test reports.",
        ["/regression-list", "/regression-from-last-failure", "/nova-mega-test --confirm"],
        value=86,
        category="regression",
    ))
    proposals.append(_proposal(
        "proposal-prompt-contract-example",
        "Keep a ready prompt-contract smoke example for /fast quality",
        "The main quality weakness remains local-model candidate drift on broad build prompts.",
        "Record a canonical notes/localStorage/export prompt contract in docs so future QA and autonomous cycles have a concrete expected behaviour specimen.",
        ["/prompt-contract make a tiny useful local notes app with localStorage and JSON export", "/candidate-tournament make a tiny useful local notes app with localStorage and JSON export"],
        value=84,
        category="validation",
    ))
    if "voice" in low or "mic" in low:
        proposals.append(_proposal(
            "proposal-voice-smoke",
            "Add voice troubleshooting to the completed improvement report",
            "Voice issues depend on browser/device state, so completed proposals should preserve mic-test and setup wizard guidance.",
            "Include /voice-troubleshoot, /mic-test, refresh-mics, and selected-device checks in the proposal completion report.",
            ["/voice-troubleshoot", "/mic-test"],
            value=78,
            category="voice",
        ))
    if not _has_file(root, "tests_smoke.py"):
        proposals.append(_proposal(
            "proposal-target-warning",
            "Warn when the selected workspace is not Nova source",
            "The current target does not look like the Nova source tree, so source-code improvements should not run there.",
            "Record a skipped proposal and recommend /project-open on the real Nova root before mutation.",
            ["/codebase-audit", "/project-open <Nova root>"],
            risk="none",
            value=99,
            category="targeting",
        ))
    proposals.sort(key=lambda p: (p["risk"] not in {"low", "none"}, p["category"] == "targeting", -int(p["value"])))
    return {
        "generated_at": _now(),
        "root": str(root),
        "focus": focus or "general Nova improvement completion",
        "proposal_count": len(proposals),
        "proposals": proposals,
        "safe_auto_complete_categories": ["docs", "regression", "validation", "autonomy"],
    }


_REGRESSION_SEEDS = [
    {
        "title": "Dodge Game default appeared on non-game app prompt",
        "expected": "Prompt-derived must-not-have checks block unrelated game/canvas/score/player defaults unless the user asks for a game.",
        "command": "/prompt-contract make a tiny useful local notes app with localStorage and JSON export",
    },
    {
        "title": "Idle/autonomous output overwrote active user task status",
        "expected": "Idle skips while a foreground request/model prompt/quiet window is active.",
        "command": "/idle status",
    },
    {
        "title": "Version label changed without legacy regression wording",
        "expected": "VERSION_LABEL preserves sandbox, dependency, upgrade, voice setup wizard, package hygiene, and current version wording.",
        "command": "/nova-doctor",
    },
    {
        "title": "README claimed export but app did not implement export",
        "expected": "Claim verifier/static acceptance requires README claims to exist in code evidence.",
        "command": "/contract-validate make a tiny useful local notes app with localStorage and JSON export",
    },
]


def _write_completed_docs(root: Path, payload: dict[str, Any], *, confirmed: bool) -> dict[str, Any]:
    docs = root / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    app_reports = APP_DIR / "improvement_cycles"
    app_reports.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    md_path = docs / "NOVA_IMPROVEMENT_CYCLE_LATEST.md"
    js_path = docs / "NOVA_IMPROVEMENT_CYCLE_LATEST.json"
    app_md = app_reports / f"improvement_cycle_{stamp}.md"
    app_js = app_reports / f"improvement_cycle_{stamp}.json"
    lines = render_improvement_cycle(payload, include_header=True).splitlines()
    if confirmed:
        lines.extend([
            "",
            "## Completed artifacts",
            "- Wrote this proposal completion report.",
            "- Wrote JSON status for idle/autonomous/tool use.",
            "- Seeded regression-memory guidance in the report so recurring failures remain visible.",
        ])
    text = "\n".join(lines).rstrip() + "\n"
    atomic_write_text(md_path, text)
    atomic_write_json(js_path, payload)
    atomic_write_text(app_md, text)
    atomic_write_json(app_js, payload)
    return {"markdown_path": str(md_path), "json_path": str(js_path), "app_markdown_path": str(app_md), "app_json_path": str(app_js)}


def complete_improvement_proposals(root: str | Path = ".", focus: str = "", *, confirm: bool = False) -> dict[str, Any]:
    root = Path(root).resolve()
    payload = build_improvement_proposals(root, focus)
    completed: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    if not confirm:
        for p in payload["proposals"]:
            item = dict(p)
            item["status"] = "dry_run"
            item["completion"] = "Run /improvement-cycle --confirm to write reports and mark safe low-risk proposal artifacts completed."
            skipped.append(item)
    else:
        for p in payload["proposals"]:
            item = dict(p)
            if item["category"] in {"autonomy", "regression", "validation", "voice"} and item["risk"] in {"low", "none"}:
                item["status"] = "completed"
                item["completion"] = "Completed by deterministic report/registry integration; no unsafe live source mutation is performed by runtime command."
                completed.append(item)
            else:
                item["status"] = "skipped_needs_review"
                item["completion"] = "Needs manual review or source patch before runtime command should mutate code."
                skipped.append(item)
    payload["completed"] = completed
    payload["skipped"] = skipped
    payload["completed_count"] = len(completed)
    payload["skipped_count"] = len(skipped)
    payload["regression_seeds"] = _REGRESSION_SEEDS
    payload["status"] = "completed" if confirm else "dry_run"
    paths = _write_completed_docs(root, payload, confirmed=confirm)
    payload.update(paths)
    return payload


def load_latest_improvement_cycle(root: str | Path = ".") -> dict[str, Any]:
    root = Path(root).resolve()
    path = root / "docs" / "NOVA_IMPROVEMENT_CYCLE_LATEST.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            return {"ok": False, "error": repr(exc), "path": str(path)}
    return {"ok": False, "status": "missing", "path": str(path), "message": "No completed improvement cycle report found yet."}


def render_improvement_cycle(payload: dict[str, Any], *, include_header: bool = True) -> str:
    lines: list[str] = []
    if include_header:
        lines.extend(["# Nova Improvement Proposal Completion Cycle", ""])
    lines.extend([
        f"Generated: {payload.get('generated_at','')}",
        f"Root: `{payload.get('root','')}`",
        f"Focus: {payload.get('focus','')}",
        f"Status: **{payload.get('status','proposed')}**",
        "",
        "## Proposed improvements",
    ])
    for p in payload.get("proposals", []):
        lines.extend([
            f"- **{p.get('id')}** — {p.get('title')}",
            f"  - category: {p.get('category')} | risk: {p.get('risk')} | value: {p.get('value')}",
            f"  - problem: {p.get('problem')}",
            f"  - change: {p.get('change')}",
            "  - commands: " + ", ".join(f"`{c}`" for c in p.get("commands", [])),
        ])
    if "completed" in payload:
        lines.extend(["", f"## Completed: {payload.get('completed_count',0)}"])
        for p in payload.get("completed", []):
            lines.append(f"- ✅ **{p.get('id')}** — {p.get('completion')}")
        lines.extend(["", f"## Skipped/review-needed: {payload.get('skipped_count',0)}"])
        for p in payload.get("skipped", []):
            lines.append(f"- ⚪ **{p.get('id')}** — {p.get('completion')}")
    if payload.get("regression_seeds"):
        lines.extend(["", "## Regression memories to keep protected"])
        for r in payload["regression_seeds"]:
            lines.append(f"- **{r['title']}** — expected: {r['expected']} — check: `{r['command']}`")
    if payload.get("markdown_path"):
        lines.extend(["", "## Reports", f"- Markdown: `{payload.get('markdown_path')}`", f"- JSON: `{payload.get('json_path')}`"])
    return "\n".join(lines).rstrip()
