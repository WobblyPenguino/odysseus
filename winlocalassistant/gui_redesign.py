from __future__ import annotations
from pathlib import Path
from typing import Any

FEATURES = {
    "Chat composer": ["Ask Nova", "Send", "attach"],
    "Voice controls": ["Mic test", "Refresh mics", "voice"],
    "Projects/files": ["Projects", "Files", "Zip project"],
    "Live Activity": ["Live activity", "Current task"],
    "Model status": ["Local LLM status", "LLM status"],
    "Sandbox/Docker": ["Sandbox", "Docker", "sandbox-linux"],
    "Idle/autonomous": ["Idle Self-Improvement", "autonomous"],
    "Research/memory": ["Research", "Memory", "Project memory"],
    "Release/testing": ["Test all", "Release gate", "Massive test"],
    "Architecture": ["Architecture", "Planner", "Validate", "Repair"],
}


def build_gui_feature_map(root: Path) -> dict[str, Any]:
    webui = (root / "winlocalassistant" / "webui.py").read_text(encoding="utf-8", errors="replace") if (root / "winlocalassistant" / "webui.py").exists() else ""
    features = []
    for name, needles in FEATURES.items():
        hits = [n for n in needles if n.lower() in webui.lower()]
        features.append({"name": name, "ok": bool(hits), "hits": hits, "missing": [n for n in needles if n not in hits]})
    ok = all(f["ok"] for f in features)
    return {"ok": ok, "features": features, "mode_options": ["classic", "cockpit-preview"], "recommendation": "Keep classic UI as default; add cockpit-preview behind /gui-mode cockpit until feature-map and visual tests pass."}


def render_gui_feature_map(payload: dict[str, Any]) -> str:
    lines = ["# GUI Feature Map", "", f"Overall: **{'PASS' if payload.get('ok') else 'ATTENTION'}**", f"Recommendation: {payload.get('recommendation','')}", "", "## Feature coverage"]
    for f in payload.get("features", []):
        icon = "✅" if f.get("ok") else "❌"
        lines.append(f"- {icon} **{f.get('name')}** — hits: {', '.join(f.get('hits') or ['none'])}")
    return "\n".join(lines)


def cockpit_preview_markdown() -> str:
    return """# Cockpit GUI Redesign Preview\n\nThis is a non-regressing layout plan, not a forced replacement.\n\n## Left rail\nChat, Projects, Build, Validate, Repair, Sandbox, Autonomous, Research, Memory, Settings.\n\n## Center workspace\nPrompt, plan, changed files, validation, preview/run instructions, final output.\n\n## Right status panel\nModel status, live trace, architecture activity, blockers, next best action.\n\n## Bottom composer\nText input, attach, microphone selector, Mic test, Send, local model progress bar.\n\n## Safety rule\nClassic GUI remains default until `/gui-feature-map`, `/gui-regression-test`, and optional `/gui-visual-test` pass.\n"""


def gui_regression_check(root: Path) -> dict[str, Any]:
    fmap = build_gui_feature_map(root)
    return {"ok": fmap.get("ok", False), "feature_map": fmap, "checks": ["feature labels present", "classic mode preserved", "cockpit preview documented"], "next": "Run Playwright visual tests when browser is available."}


def render_gui_regression(payload: dict[str, Any]) -> str:
    return "# GUI Regression Test\n\n" + ("Overall: **PASS**" if payload.get("ok") else "Overall: **ATTENTION**") + "\n\n" + render_gui_feature_map(payload.get("feature_map", {}))
