from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class ProjectBlueprint:
    goal: str
    artifact_type: str
    likely_files: list[str]
    must_have: list[str]
    must_not_have: list[str]
    validation_rules: list[str]
    repair_hints: list[str]
    confidence: float


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def build_project_blueprint(goal: str) -> dict[str, Any]:
    raw = (goal or "").strip()
    toks = _tokens(raw)
    must_have: list[str] = []
    must_not: list[str] = ["unrelated default template", "fake README claims", "broken HTML/JS wiring"]
    files = ["index.html", "style.css", "app.js", "README.md"]
    artifact = "html_css_js_app" if toks & {"app", "page", "html", "website", "dashboard", "notes", "localstorage", "export"} else "generic_project"
    if toks & {"note", "notes", "notepad"}:
        must_have += ["add notes", "list saved notes", "delete notes"]
    if toks & {"localstorage", "local", "saving", "save", "saved"}:
        must_have.append("localStorage persistence")
    if toks & {"export", "json", "download"}:
        must_have.append("JSON export")
    if toks & {"game", "dodge", "platformer"}:
        artifact = "game"
        must_have += ["interactive controls", "game loop or scoring feedback"]
    else:
        must_not += ["Dodge Game", "game controls or score unless requested"]
    if toks & {"voice", "mic", "microphone"}:
        must_have += ["microphone preflight", "clear permission error messages"]
    if not must_have:
        must_have = ["matches the user request", "clear run/open instructions", "visible useful behaviour"]
    validation = [
        "all blueprint files exist or are intentionally omitted",
        "HTML references local CSS/JS files that exist",
        "JS handlers referenced by HTML exist",
        "README claims are implemented in code",
        "must_not_have terms are absent unless explicitly requested",
        "project can be opened or syntax-checked without obvious errors",
    ]
    if "localStorage persistence" in must_have:
        validation.append("app.js uses localStorage with safe JSON parse fallback")
    if "JSON export" in must_have:
        validation.append("app.js creates a JSON Blob/download or equivalent export")
    confidence = 0.85 if raw else 0.35
    bp = ProjectBlueprint(raw or "general project", artifact, files, sorted(set(must_have)), sorted(set(must_not)), validation, ["repair only the smallest failing requirement first", "do not switch templates unless the prompt requires it"], confidence)
    return asdict(bp)


def score_candidate(goal: str, files: dict[str, str] | None = None, text: str = "") -> dict[str, Any]:
    blueprint = build_project_blueprint(goal)
    corpus = "\n".join((files or {}).values()) + "\n" + (text or "")
    lower = corpus.lower()
    positives = []
    missing = []
    for item in blueprint["must_have"]:
        key = item.lower()
        checks = [key]
        if "localstorage" in key:
            checks = ["localstorage"]
        if "json export" in key:
            checks = ["json", "blob", "download"]
        if "delete notes" in key:
            checks = ["delete", "remove"]
        if any(c in lower for c in checks):
            positives.append(item)
        else:
            missing.append(item)
    forbidden = [item for item in blueprint["must_not_have"] if item.lower() in lower]
    expected_files = blueprint["likely_files"]
    present_files = sorted((files or {}).keys())
    file_score = 100 if not files else round(100 * len([f for f in expected_files if f in files]) / max(1, len(expected_files)), 1)
    req_score = round(100 * len(positives) / max(1, len(blueprint["must_have"])), 1)
    penalty = min(60, 20 * len(forbidden))
    overall = max(0, round((req_score * 0.55) + (file_score * 0.25) + (100 * 0.20) - penalty, 1))
    return {"goal": goal, "overall_percent": overall, "requirement_score": req_score, "file_score": file_score, "forbidden_penalty": penalty, "present_files": present_files, "matched_requirements": positives, "missing_requirements": missing, "forbidden_hits": forbidden, "blueprint": blueprint, "passed": overall >= 75 and not forbidden and not missing}


def build_candidate_set(goal: str) -> dict[str, Any]:
    bp = build_project_blueprint(goal)
    candidates = [
        {"name": "minimal", "strategy": "smallest complete implementation", "risk": "low", "expected_strength": "fast and easy to repair"},
        {"name": "polished", "strategy": "better UI, same core behaviours", "risk": "medium", "expected_strength": "more user-facing quality"},
        {"name": "robust", "strategy": "adds validation, empty-state handling and README evidence", "risk": "medium", "expected_strength": "best for release-quality output"},
    ]
    for c in candidates:
        c["score_hint"] = 88 if c["name"] == "robust" else 82 if c["name"] == "polished" else 76
        c["validation"] = bp["validation_rules"]
    return {"goal": goal, "blueprint": bp, "candidates": candidates, "recommended": "robust" if len(bp["must_have"]) > 2 else "minimal"}


def render_blueprint_markdown(blueprint: dict[str, Any]) -> str:
    lines = ["# Project Blueprint", "", f"Goal: {blueprint.get('goal','')}", f"Artifact type: `{blueprint.get('artifact_type','')}`", f"Confidence: **{blueprint.get('confidence',0):.2f}**", "", "## Likely files"]
    lines += [f"- `{f}`" for f in blueprint.get("likely_files", [])]
    lines += ["", "## Must have"] + [f"- {x}" for x in blueprint.get("must_have", [])]
    lines += ["", "## Must not have"] + [f"- {x}" for x in blueprint.get("must_not_have", [])]
    lines += ["", "## Validation rules"] + [f"- {x}" for x in blueprint.get("validation_rules", [])]
    lines += ["", "## Repair hints"] + [f"- {x}" for x in blueprint.get("repair_hints", [])]
    return "\n".join(lines)


def render_candidate_markdown(payload: dict[str, Any]) -> str:
    lines = ["# Candidate Build Plan", "", f"Goal: {payload.get('goal','')}", f"Recommended candidate: **{payload.get('recommended','')}**", "", "## Blueprint summary", render_blueprint_markdown(payload.get("blueprint", {})), "", "## Candidates"]
    for c in payload.get("candidates", []):
        lines += [f"### {c.get('name','candidate')}", f"- Strategy: {c.get('strategy','')}", f"- Risk: {c.get('risk','')}", f"- Score hint: {c.get('score_hint','')}", f"- Strength: {c.get('expected_strength','')}"]
    return "\n".join(lines)


def render_score_markdown(score: dict[str, Any]) -> str:
    lines = ["# Model Output / Candidate Score", "", f"Goal: {score.get('goal','')}", f"Overall: **{score.get('overall_percent')}%**", f"Passed: **{score.get('passed')}**", "", "## Matched requirements"]
    lines += [f"- {x}" for x in score.get("matched_requirements", [])] or ["- none"]
    lines += ["", "## Missing requirements"] + ([f"- {x}" for x in score.get("missing_requirements", [])] or ["- none"])
    lines += ["", "## Forbidden hits"] + ([f"- {x}" for x in score.get("forbidden_hits", [])] or ["- none"])
    return "\n".join(lines)
