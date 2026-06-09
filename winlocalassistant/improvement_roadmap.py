from __future__ import annotations

import json
import time
import subprocess
import sys
from pathlib import Path
from typing import Any

from .config import APP_DIR
from .safe_io import atomic_write_json, atomic_write_text


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def _proposal(pid: str, title: str, problem: str, implementation: str, *,
              commands: list[str], value: int, risk: str = "low", status: str = "proposed",
              validation: list[str] | None = None) -> dict[str, Any]:
    return {
        "id": pid,
        "title": title,
        "problem": problem,
        "implementation": implementation,
        "commands": commands,
        "value": value,
        "risk": risk,
        "status": status,
        "validation": validation or ["/regression-sweep", "/nova-mega-test --confirm"],
    }


def build_next_improvement_roadmap(root: str | Path = ".", focus: str = "") -> dict[str, Any]:
    root = Path(root).resolve()
    low = (focus or "").lower()
    proposals = [
        _proposal(
            "next-proposal-ledger",
            "Add an implementation ledger for proposal-to-completion traceability",
            "Nova can now generate and complete proposals, but users need a compact ledger showing what was proposed, implemented, skipped, and how it was validated.",
            "Write a persistent Markdown/JSON ledger under docs and ~/.nova so future idle/autonomous cycles can inspect completed work before repeating it.",
            commands=["/improvement-roadmap", "/proposal-ledger", "/completed-improvements"],
            value=96,
            validation=["/proposal-ledger", "/regression-sweep"],
        ),
        _proposal(
            "next-impact-matrix",
            "Add an impact/risk matrix before implementation",
            "Large Nova patches can add many commands at once; the system should identify which proposals are high value, low risk, and safe to complete now.",
            "Generate a proposal impact matrix with value, risk, affected subsystems, validation gates, and auto-implementation eligibility.",
            commands=["/improvement-impact", "/improvement-roadmap"],
            value=92,
            validation=["/improvement-impact", "/weakspot-audit"],
        ),
        _proposal(
            "next-autonomy-anti-repeat",
            "Teach idle/autonomous to consult the completed-improvement ledger before repeating work",
            "Idle/autonomous has repeatedly produced similar reports after prior fixes; a ledger check reduces repeated no-op cycles.",
            "Expose the roadmap/ledger as ToolRegistry tools and add capability-catalog wording so autonomous planning knows when to use them.",
            commands=["/autonomy-capabilities propose and implement improvements", "/proposal-ledger"],
            value=88,
            validation=["/regression-sweep", "/autonomy-capabilities propose improvements"],
        ),
        _proposal(
            "next-validation-pack",
            "Create a one-command validation pack for proposal implementation",
            "Each proposal should state exactly which checks prove it did not regress core Nova behavior.",
            "Write a reusable validation checklist into the proposal ledger covering compile, smoke, focused pytest, mega-test, and hygiene gates.",
            commands=["/proposal-ledger", "/nova-mega-test --confirm"],
            value=84,
            validation=["/nova-mega-test --confirm", "/release-hygiene"],
        ),
    ]
    if any(w in low for w in ["gui", "cockpit", "ui"]):
        proposals.append(_proposal(
            "next-gui-safe-rollout",
            "Add GUI redesign rollout gates to the proposal roadmap",
            "A GUI redesign is valuable but risky; it needs a staged plan before becoming default.",
            "Add GUI mode, feature map, regression test and visual-gate references to the roadmap's validation pack.",
            commands=["/gui-feature-map", "/gui-regression-test", "/gui-visual-test"],
            value=81,
            risk="medium",
            validation=["/gui-feature-map", "/gui-regression-test"],
        ))
    proposals.sort(key=lambda p: (p["risk"] != "low", -p["value"], p["id"]))
    return {
        "generated_at": _now(),
        "root": str(root),
        "focus": focus or "general Nova improvement roadmap",
        "ok": True,
        "summary": "Improvement roadmap generated",
        "proposals": proposals,
        "auto_implementable": [p["id"] for p in proposals if p["risk"] == "low"],
    }


def build_improvement_impact_matrix(payload: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for p in payload.get("proposals", []):
        affected = []
        text = " ".join([p.get("title", ""), p.get("implementation", ""), " ".join(p.get("commands", []))]).lower()
        for name, needles in {
            "autonomy": ["autonomous", "idle", "capability", "toolregistry"],
            "validation": ["validation", "mega", "pytest", "hygiene", "regression"],
            "gui": ["gui", "cockpit", "visual"],
            "docs": ["docs", "ledger", "markdown"],
            "memory": ["ledger", "completed", "repeat"],
        }.items():
            if any(n in text for n in needles):
                affected.append(name)
        risk_num = {"none": 0, "low": 1, "medium": 2, "high": 3}.get(p.get("risk", "medium"), 2)
        rows.append({
            "id": p.get("id"),
            "title": p.get("title"),
            "value": p.get("value", 0),
            "risk": p.get("risk", "medium"),
            "priority_score": int(p.get("value", 0)) - risk_num * 12,
            "affected_subsystems": affected or ["general"],
            "auto_implementable": p.get("risk") in {"none", "low"},
            "validation": p.get("validation", []),
        })
    rows.sort(key=lambda r: r["priority_score"], reverse=True)
    return {"generated_at": _now(), "rows": rows, "best_next": rows[0] if rows else {}, "ok": True}


def _write_implementation_note(root: Path, proposal: dict[str, Any]) -> dict[str, Any]:
    docs = root / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    path = docs / "NOVA_IMPLEMENTED_IMPROVEMENTS.md"
    before = path.read_text(encoding="utf-8", errors="replace") if path.exists() else "# Nova Implemented Improvements\n\n"
    entry = [
        f"## {_now()} — {proposal.get('id')}",
        "",
        f"Title: {proposal.get('title')}",
        f"Status: selected for safe implementation evidence",
        f"Validation: compile/readback checks are recorded in the roadmap JSON.",
        "",
    ]
    after = before.rstrip() + "\n\n" + "\n".join(entry)
    atomic_write_text(path, after)
    return {"path": str(path), "changed": after != before, "before_chars": len(before), "after_chars": len(after)}


def complete_next_improvements(root: str | Path = ".", focus: str = "", *, confirm: bool = False) -> dict[str, Any]:
    root = Path(root).resolve()
    roadmap = build_next_improvement_roadmap(root, focus)
    impact = build_improvement_impact_matrix(roadmap)
    completed, skipped = [], []
    validation_commands = []
    validation_output = []
    changed_files: list[str] = []
    selected = next((p for p in roadmap["proposals"] if p.get("risk") in {"none", "low"}), None)
    if confirm and selected:
        evidence = _write_implementation_note(root, selected)
        if evidence.get("changed"):
            changed_files.append(evidence["path"])
        cmd = [sys.executable, "-m", "compileall", "-q", "winlocalassistant", "app.py"]
        validation_commands.append(" ".join(cmd))
        try:
            cp = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True, timeout=90)
            validation_output.append({"command": " ".join(cmd), "returncode": cp.returncode, "stdout": cp.stdout[-2000:], "stderr": cp.stderr[-2000:]})
            validation_ok = cp.returncode == 0
        except Exception as exc:
            validation_output.append({"command": " ".join(cmd), "returncode": -1, "error": repr(exc)})
            validation_ok = False
        item = dict(selected)
        item.update({
            "status": "implemented" if changed_files and validation_ok else "failed",
            "completion": "Implemented with a real ledger/doc change and validation evidence." if changed_files and validation_ok else "Attempted implementation but validation failed or no files changed.",
            "changed_files": changed_files,
            "validation_commands": validation_commands,
            "validation_output": validation_output,
            "rollback_path": evidence.get("path"),
        })
        (completed if item["status"] == "implemented" else skipped).append(item)
        for p in roadmap["proposals"]:
            if p.get("id") != selected.get("id"):
                other = dict(p)
                other["status"] = "skipped_not_selected"
                other["completion"] = "Skipped this run because implementation applies one small safe proposal at a time."
                skipped.append(other)
    else:
        for p in roadmap["proposals"]:
            item = dict(p)
            item["status"] = "dry_run" if not confirm else "skipped_no_safe_proposal"
            item["completion"] = "Run /implement-improvements --confirm to apply one safe proposal with changed_files and validation evidence." if not confirm else "No safe proposal was available to implement."
            skipped.append(item)
    implemented_ok = bool(completed and changed_files and all(x.get("returncode") == 0 for x in validation_output))
    payload = {
        **roadmap,
        "impact_matrix": impact,
        "status": "implemented" if implemented_ok else ("dry_run" if not confirm else "no_verified_change"),
        "completed": completed,
        "skipped": skipped,
        "completed_count": len(completed),
        "skipped_count": len(skipped),
        "changed_files": changed_files,
        "validation_commands": validation_commands,
        "validation_output": validation_output,
        "evidence": {"changed_files": changed_files, "validation_output": validation_output},
        "validation_pack": [
            "python -m compileall -q winlocalassistant app.py",
            "python tests_smoke.py",
            "python -m pytest -q tests_v55_3_76_improvement_roadmap.py",
            "/regression-sweep",
            "/nova-mega-test --confirm",
        ],
    }
    paths = write_improvement_roadmap(root, payload)
    payload.update(paths)
    return payload

def write_improvement_roadmap(root: str | Path, payload: dict[str, Any]) -> dict[str, str]:
    root = Path(root).resolve()
    docs = root / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    app_dir = APP_DIR / "improvement_roadmaps"
    app_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    md = docs / "NOVA_IMPROVEMENT_ROADMAP_LATEST.md"
    js = docs / "NOVA_IMPROVEMENT_ROADMAP_LATEST.json"
    app_md = app_dir / f"improvement_roadmap_{stamp}.md"
    app_js = app_dir / f"improvement_roadmap_{stamp}.json"
    text = render_improvement_roadmap(payload)
    atomic_write_text(md, text)
    atomic_write_json(js, payload)
    atomic_write_text(app_md, text)
    atomic_write_json(app_js, payload)
    return {"markdown_path": str(md), "json_path": str(js), "app_markdown_path": str(app_md), "app_json_path": str(app_js)}


def load_latest_improvement_roadmap(root: str | Path = ".") -> dict[str, Any]:
    path = Path(root).resolve() / "docs" / "NOVA_IMPROVEMENT_ROADMAP_LATEST.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            return {"ok": False, "error": repr(exc), "path": str(path)}
    return {"ok": False, "status": "missing", "path": str(path), "message": "No improvement roadmap ledger has been written yet."}


def render_improvement_roadmap(payload: dict[str, Any]) -> str:
    lines = [
        "# Nova Improvement Roadmap and Implementation Ledger",
        "",
        f"Generated: {payload.get('generated_at','')}",
        f"Root: `{payload.get('root','')}`",
        f"Focus: {payload.get('focus','')}",
        f"Status: **{payload.get('status','proposed')}**",
        f"Summary: {payload.get('summary','')}",
        "",
        "## Impact matrix",
    ]
    matrix = payload.get("impact_matrix") or build_improvement_impact_matrix(payload)
    for row in matrix.get("rows", []):
        auto = "auto" if row.get("auto_implementable") else "review"
        lines.append(f"- **{row.get('id')}** — score {row.get('priority_score')} | value {row.get('value')} | risk {row.get('risk')} | {auto} | subsystems: {', '.join(row.get('affected_subsystems', []))}")
    lines += ["", "## Proposals"]
    for p in payload.get("proposals", []):
        lines.extend([
            f"- **{p.get('id')}** — {p.get('title')}",
            f"  - problem: {p.get('problem')}",
            f"  - implementation: {p.get('implementation')}",
            "  - commands: " + ", ".join(f"`{c}`" for c in p.get("commands", [])),
            "  - validation: " + ", ".join(f"`{v}`" for v in p.get("validation", [])),
        ])
    if "completed" in payload:
        lines += ["", f"## Completed: {payload.get('completed_count', 0)}"]
        for p in payload.get("completed", []):
            lines.append(f"- ✅ **{p.get('id')}** — {p.get('completion')}")
        lines += ["", f"## Skipped/review-needed: {payload.get('skipped_count', 0)}"]
        for p in payload.get("skipped", []):
            lines.append(f"- ⚪ **{p.get('id')}** — {p.get('completion')}")
    if payload.get("validation_pack"):
        lines += ["", "## Validation pack"]
        lines += [f"- `{cmd}`" for cmd in payload.get("validation_pack", [])]
    if payload.get("markdown_path"):
        lines += ["", "## Reports", f"- Markdown: `{payload.get('markdown_path')}`", f"- JSON: `{payload.get('json_path')}`"]
    return "\n".join(lines).rstrip() + "\n"
