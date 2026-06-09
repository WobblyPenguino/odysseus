from __future__ import annotations

import re
from typing import Any


def classify_failure(goal: str = "", failure: Any = None) -> dict[str, Any]:
    text = (str(goal or "") + "\n" + str(failure or "")).lower()
    if "game_missing_collision" in text or "collision" in text and "game" in text:
        return {"kind": "game_missing_collision", "recipe": "inject_collision_loop", "confidence": 0.95}
    if "getelementbyid" in text or "missing html" in text or "element" in text:
        return {"kind": "missing_html_element", "recipe": "align_html_js_ids", "confidence": 0.85}
    if "parseable json" in text or "json" in text and "model" in text:
        return {"kind": "model_json_failure", "recipe": "json_repair_or_deterministic_fallback", "confidence": 0.8}
    if "syntax" in text or "node --check" in text:
        return {"kind": "syntax_error", "recipe": "syntax_surgical_patch", "confidence": 0.75}
    if "unrelated" in text or "requested domain" in text:
        return {"kind": "domain_mismatch", "recipe": "domain_template_fallback", "confidence": 0.8}
    return {"kind": "unknown", "recipe": "inspect_then_patch", "confidence": 0.4}


def recipe_steps(kind: str) -> list[str]:
    recipes = {
        "game_missing_collision": [
            "Inject or verify rectsOverlap(a,b)",
            "Call collision logic inside the update loop",
            "Make collision change score/lives/game-over state",
            "Add restart path",
            "Run node --check and game runtime sanity check",
        ],
        "missing_html_element": [
            "Extract getElementById references from JS",
            "Extract id attributes from HTML",
            "Add missing elements or rename JS references to existing IDs",
            "Run static DOM contract check",
        ],
        "model_json_failure": [
            "Do not ask the model for the same full response again",
            "Extract any valid file snippets",
            "Use deterministic fallback if two parse failures occur",
        ],
        "domain_mismatch": [
            "Stop regenerating generic demo",
            "Build a minimal template around the user's domain words",
            "Run acceptance checks against the original goal",
        ],
    }
    return recipes.get(kind, ["Inspect current files", "Patch the smallest failing area", "Run targeted verification"])


def patch_candidate_for_failure(candidate: dict[str, Any], goal: str, failure: Any) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    info = classify_failure(goal, failure)
    files = dict(candidate.get("files") or {})
    edits: list[dict[str, Any]] = []
    if info["kind"] == "game_missing_collision" and "app.js" in files:
        js = str(files["app.js"])
        if "rectsOverlap" not in js:
            js += """

// Surgical fallback recipe: collision detection required by the game contract.
function rectsOverlap(a, b) {
  return a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
}
"""
            edits.append({"kind": "game_missing_collision", "file": "app.js", "detail": "Added rectsOverlap collision helper"})
        if "checkCollisions" not in js:
            js += """

function checkCollisions() {
  if (typeof player === 'undefined') return;
  const targets = Array.isArray(window.targets) ? window.targets : [];
  const hazards = Array.isArray(window.hazards) ? window.hazards : [];
  targets.forEach(t => { if (!t.collected && rectsOverlap(player, t)) { t.collected = true; window.score = (window.score || 0) + 1; } });
  hazards.forEach(h => { if (!window.gameOver && rectsOverlap(player, h)) { window.gameOver = true; } });
}
"""
            edits.append({"kind": "game_missing_collision", "file": "app.js", "detail": "Added checkCollisions game interaction path"})
        files["app.js"] = js
    out = dict(candidate)
    out["files"] = files
    if edits:
        out["notes"] = (str(out.get("notes") or "") + "\nApplied surgical recipe: " + "; ".join(e["detail"] for e in edits)).strip()
        out["surgical_recipe"] = info
    return out, edits
