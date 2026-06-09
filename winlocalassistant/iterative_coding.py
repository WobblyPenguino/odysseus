from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

from .safe_io import atomic_write_json, atomic_write_text


def _read(path: Path, limit: int = 120000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except Exception:
        return ""


def _project_files(root: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for name in ("index.html", "app.js", "script.js", "style.css", "README.md", "PROJECT_MANIFEST.json", "TEST_REPORT.md"):
        p = root / name
        if p.exists() and p.is_file():
            files[name] = _read(p)
    return files


def _words(goal: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9_]{3,}", (goal or "").lower()))


def _handler_names(html: str) -> set[str]:
    names = set(re.findall(r"on\w+\s*=\s*['\"]\s*([a-zA-Z_$][\w$]*)\s*\(", html or ""))
    return names


def _declared_functions(js: str) -> set[str]:
    names = set(re.findall(r"function\s+([a-zA-Z_$][\w$]*)\s*\(", js or ""))
    names.update(re.findall(r"(?:const|let|var)\s+([a-zA-Z_$][\w$]*)\s*=\s*(?:async\s*)?\(?[^=]*?\)?\s*=>", js or ""))
    names.update(re.findall(r"window\.([a-zA-Z_$][\w$]*)\s*=", js or ""))
    return names


def _ids(html: str) -> set[str]:
    return set(re.findall(r"id\s*=\s*['\"]([^'\"]+)['\"]", html or "", flags=re.I))


def _referenced_ids(js: str) -> set[str]:
    refs = set(re.findall(r"getElementById\(\s*['\"]([^'\"]+)['\"]\s*\)", js or ""))
    refs.update(re.findall(r"querySelector\(\s*['\"]#([^'\"]+)['\"]\s*\)", js or ""))
    return refs


def classify_iterative_coding_state(root: str | Path, goal: str = "", failure: Any = None) -> dict[str, Any]:
    root = Path(root).expanduser().resolve()
    files = _project_files(root)
    html = "\n".join(v for k, v in files.items() if k.endswith(".html"))
    js = "\n".join(v for k, v in files.items() if k.endswith(".js"))
    readme = files.get("README.md", "")
    goal_words = _words(goal)
    code_text = "\n".join(files.values()).lower()
    matched_goal_words = sorted(w for w in goal_words if w in code_text)[:40]
    missing_handlers = sorted(_handler_names(html) - _declared_functions(js))
    missing_ids = sorted(_referenced_ids(js) - _ids(html))
    warnings: list[dict[str, Any]] = []
    if missing_handlers:
        warnings.append({"kind": "missing_handler", "detail": "HTML inline event handler has no JS function", "items": missing_handlers})
    if missing_ids:
        warnings.append({"kind": "missing_dom_id", "detail": "JavaScript references DOM IDs not present in HTML", "items": missing_ids})
    low_goal = (goal or "").lower()
    if any(w in low_goal for w in ("localstorage", "save", "persist")) and "localstorage" not in code_text:
        warnings.append({"kind": "missing_localstorage", "detail": "Prompt implies persistence but code does not mention localStorage"})
    if any(w in low_goal for w in ("export", "download", "json")) and not any(w in code_text for w in ("blob", "download", "json.stringify")):
        warnings.append({"kind": "missing_export", "detail": "Prompt implies export/download but code lacks export evidence"})
    if "dodge" in code_text and "dodge" not in low_goal:
        warnings.append({"kind": "unrelated_default_template", "detail": "Dodge-game/default-template evidence appears despite prompt not asking for it"})
    if "export" in readme.lower() and not any(w in js.lower() for w in ("blob", "download", "json.stringify")):
        warnings.append({"kind": "readme_claim_not_implemented", "detail": "README claims export but JS does not clearly implement it"})
    score = 100
    score -= min(60, len(warnings) * 15)
    if goal_words and len(matched_goal_words) < max(1, min(4, len(goal_words)//3)):
        score -= 15
        warnings.append({"kind": "weak_prompt_match", "detail": "Few prompt concepts appear in actual files", "matched": matched_goal_words})
    state = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "root": str(root),
        "goal": goal,
        "file_count": len(files),
        "files_seen": sorted(files),
        "score": max(0, min(100, score)),
        "warnings": warnings,
        "matched_goal_words": matched_goal_words,
        "missing_handlers": missing_handlers,
        "missing_dom_ids": missing_ids,
        "failure_preview": str(failure or "")[:1200],
    }
    return state


def build_surgical_fallback_plan(root: str | Path, goal: str = "", failure: Any = None) -> dict[str, Any]:
    state = classify_iterative_coding_state(root, goal, failure)
    actions: list[dict[str, Any]] = []
    for warning in state["warnings"]:
        kind = warning.get("kind")
        if kind == "missing_handler":
            actions.append({"type": "minimal_js_patch", "target": "app.js", "reason": warning.get("detail"), "instruction": "Add missing function(s) with the smallest implementation and expose them on window when HTML uses inline handlers.", "items": warning.get("items", [])})
        elif kind == "missing_dom_id":
            actions.append({"type": "minimal_html_or_js_patch", "target": "index.html/app.js", "reason": warning.get("detail"), "instruction": "Either add the missing HTML element IDs or change the JS selectors to IDs that actually exist.", "items": warning.get("items", [])})
        elif kind == "readme_claim_not_implemented":
            actions.append({"type": "claim_sync", "target": "README.md/app.js", "reason": warning.get("detail"), "instruction": "Implement the claim if it is required by the prompt; otherwise remove the README claim."})
        elif kind == "unrelated_default_template":
            actions.append({"type": "domain_correction", "target": "project files", "reason": warning.get("detail"), "instruction": "Replace unrelated default-template concepts with prompt-specific UI and behaviour; do not regenerate unrelated games/apps."})
        else:
            actions.append({"type": "contract_repair", "target": "project files", "reason": warning.get("detail"), "instruction": "Patch the smallest file set needed to satisfy the prompt contract."})
    if not actions:
        actions.append({"type": "verify_only", "target": ".", "reason": "No obvious static surgical repair target found", "instruction": "Run prompt-contract, build-quality, browser-runtime and final checks before broad regeneration."})
    return {
        "ok": True,
        "summary": f"Surgical fallback plan built with {len(actions)} action(s)",
        "state": state,
        "actions": actions,
        "policy": {
            "rewrite_order": ["one selector/handler", "one README claim", "one missing feature", "one file rewrite", "full regeneration only as last resort"],
            "live_tree_rule": "Prefer copied workspace/sandbox validation before promoting edits.",
            "stop_rule": "Stop after the same rejection reason repeats twice; switch to deterministic template or ask for a narrower target.",
        },
    }


def build_iterative_coding_loop(root: str | Path, goal: str = "", max_passes: int = 3) -> dict[str, Any]:
    state = classify_iterative_coding_state(root, goal)
    passes = []
    for i in range(1, max(1, min(int(max_passes or 3), 6)) + 1):
        passes.append({
            "pass": i,
            "steps": [
                {"tool": "prompt_contract", "why": "compile prompt-specific must-have and must-not-have checks"},
                {"tool": "build_quality_report", "why": "score current files against prompt and claim truth"},
                {"tool": "browser_runtime_test", "why": "exercise UI/storage/export behaviour where possible"},
                {"tool": "surgical_fallback_v2", "why": "choose minimal patch targets from concrete evidence"},
                {"tool": "model_output_coach", "why": "tighten local-model prompt only if deterministic repair is insufficient"},
                {"tool": "prompt_test_run", "why": "re-run the contract after any edit"},
            ],
            "advance_condition": "quality score improves or a warning is removed",
            "stop_condition": "prompt contract + build quality + runtime checks pass, or the same blocker repeats twice",
        })
    return {
        "ok": True,
        "summary": "Iterative coding loop planned",
        "root": str(Path(root).expanduser().resolve()),
        "goal": goal,
        "initial_state": state,
        "passes": passes,
        "promotion_gate": ["py_compile if Python changed", "node --check for JS when available", "prompt_test_run", "build_quality_report", "browser_runtime_test", "final_project_check"],
    }


def render_iterative_coding_markdown(payload: dict[str, Any]) -> str:
    lines = ["# Iterative Coding / Surgical Fallback", "", f"Summary: {payload.get('summary','')}", ""]
    state = payload.get("state") or payload.get("initial_state") or {}
    if state:
        lines += ["## Current evidence", f"- Root: `{state.get('root','')}`", f"- Score: **{state.get('score','?')}**", f"- Files seen: {', '.join(state.get('files_seen') or []) or 'none'}", ""]
        warnings = state.get("warnings") or []
        lines.append("## Warnings")
        if warnings:
            for w in warnings:
                lines.append(f"- **{w.get('kind')}**: {w.get('detail')}")
                if w.get("items"):
                    lines.append("  - items: " + ", ".join(map(str, w.get("items") or [])))
        else:
            lines.append("- none")
        lines.append("")
    if payload.get("actions"):
        lines.append("## Minimal repair actions")
        for i, a in enumerate(payload.get("actions") or [], 1):
            lines.append(f"{i}. **{a.get('type')}** → `{a.get('target')}`")
            lines.append(f"   - why: {a.get('reason')}")
            lines.append(f"   - do: {a.get('instruction')}")
        lines.append("")
    if payload.get("passes"):
        lines.append("## Iterative loop")
        for p in payload.get("passes") or []:
            lines.append(f"### Pass {p.get('pass')}")
            for s in p.get("steps") or []:
                lines.append(f"- `{s.get('tool')}` — {s.get('why')}")
            lines.append(f"- advance: {p.get('advance_condition')}")
            lines.append(f"- stop: {p.get('stop_condition')}")
        lines.append("")
    if payload.get("promotion_gate"):
        lines.append("## Promotion gate")
        lines += [f"- {x}" for x in payload.get("promotion_gate") or []]
    return "\n".join(lines)


def write_iterative_coding_report(root: str | Path, goal: str = "") -> tuple[Path, Path, dict[str, Any]]:
    root = Path(root).expanduser().resolve()
    payload = build_iterative_coding_loop(root, goal)
    docs = root / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    stem = "ITERATIVE_CODING_LOOP_LATEST"
    md = docs / f"{stem}.md"
    js = docs / f"{stem}.json"
    atomic_write_text(md, render_iterative_coding_markdown(payload))
    atomic_write_json(js, payload)
    return md, js, payload
