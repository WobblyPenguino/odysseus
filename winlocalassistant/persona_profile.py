from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from .config import APP_DIR
from .safe_io import atomic_write_json, append_jsonl, read_json_file

LOGGER = logging.getLogger(__name__)

PERSONA_SCHEMA_VERSION = 1
PERSONA_PATH = APP_DIR / "persona_profile.json"
VOICE_AUDIT_PATH = APP_DIR / "voice_audit.jsonl"

DEFAULT_PERSONA: dict[str, Any] = {
    "schema_version": PERSONA_SCHEMA_VERSION,
    "assistant_name": "Nova",
    "identity": "Nova is a local-first Windows AI assistant for Daniel's Nova workspace: practical, honest, evidence-driven, and careful with files.",
    "self_model": "I am Nova, the conversational face of Nova. I can chat, plan, run Nova tools, inspect projects, prepare patches, validate work, and explain exactly what happened.",
    "response_contract": "Be conversational first. Give a short useful summary before details. Never claim work was done unless a receipt/tool/validation result proves it. For technical actions, say what changed, what was verified, and what still needs attention.",
    "core_traits": ["reliable", "transparent", "practical", "curious", "careful"],
    "beliefs": [
        "Verified evidence beats confident guesses.",
        "Preserve working functionality when improving the UI or codebase.",
        "Patch and validate before claiming success.",
        "Ask or gate before risky file, shell, browser, sidecar, or system actions.",
    ],
    "avoid": [
        "Do not read raw hashes, JSON dumps, markdown fences, or long stack traces aloud.",
        "Do not replace a working app with an unrelated demo.",
        "Do not treat user complaints as new app-generation requests.",
    ],
    "sliders": {
        "formality": 0.35,
        "creativity": 0.55,
        "humor": 0.25,
        "empathy": 0.70,
        "verbosity": 0.45,
        "technical_depth": 0.70,
        "proactivity": 0.55,
    },
    "modes": {
        "default": "warm technical partner",
        "debugging": "concise root-cause investigator",
        "voice": "brief conversational operator",
        "autonomous": "careful mission executor with receipts",
        "idle": "quiet observer that proposes before editing unless policy permits",
    },
    "custom_system_note": "",
}


def _clamp_float(value: Any, default: float = 0.5) -> float:
    try:
        f = float(value)
    except Exception:
        return default
    return max(0.0, min(1.0, f))


def load_persona_profile() -> dict[str, Any]:
    data = read_json_file(PERSONA_PATH, {}, expected_type=dict, quarantine=True)
    if not data:
        data = dict(DEFAULT_PERSONA)
    merged = json.loads(json.dumps(DEFAULT_PERSONA))
    for key, value in data.items():
        if key == "sliders" and isinstance(value, dict):
            merged["sliders"].update({k: _clamp_float(v, merged["sliders"].get(k, 0.5)) for k, v in value.items()})
        elif key in merged:
            merged[key] = value
    merged["schema_version"] = PERSONA_SCHEMA_VERSION
    return merged


def save_persona_profile(profile: dict[str, Any]) -> dict[str, Any]:
    clean = load_persona_profile()
    for key, value in profile.items():
        if key == "sliders" and isinstance(value, dict):
            clean["sliders"].update({k: _clamp_float(v, clean["sliders"].get(k, 0.5)) for k, v in value.items()})
        elif key in clean:
            clean[key] = value
    clean["schema_version"] = PERSONA_SCHEMA_VERSION
    atomic_write_json(PERSONA_PATH, clean, ensure_ascii=False)
    return clean


def update_persona_from_tokens(tokens: str) -> dict[str, Any]:
    """Update persona fields from key=value tokens used by /persona-set.

    Supports e.g. `/persona-set formality=0.8 humor=0.1 assistant_name=Nova`.
    Values containing spaces can be supplied as JSON via /persona-json.
    """
    profile = load_persona_profile()
    sliders = profile.setdefault("sliders", {})
    for raw in (tokens or "").split():
        if "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        key = key.strip().lower().replace("-", "_")
        value = value.strip().strip('"')
        if key in sliders:
            sliders[key] = _clamp_float(value, sliders.get(key, 0.5))
        elif key in {"assistant_name", "identity", "self_model", "response_contract", "custom_system_note"}:
            profile[key] = value
        elif key in {"trait", "traits"}:
            profile["core_traits"] = [item.strip() for item in value.split(",") if item.strip()]
    profile["sliders"] = sliders
    return save_persona_profile(profile)


def update_persona_from_json(raw_json: str) -> dict[str, Any]:
    data = json.loads(raw_json or "{}")
    if not isinstance(data, dict):
        raise ValueError("Persona JSON must be an object")
    return save_persona_profile(data)


def persona_style_labels(profile: dict[str, Any] | None = None) -> dict[str, str]:
    profile = profile or load_persona_profile()
    s = profile.get("sliders", {}) or {}
    def pick(key: str, low: str, mid: str, high: str) -> str:
        v = _clamp_float(s.get(key, 0.5))
        return low if v < 0.34 else high if v > 0.66 else mid
    return {
        "formality": pick("formality", "casual", "balanced", "formal"),
        "creativity": pick("creativity", "literal", "balanced", "inventive"),
        "humor": pick("humor", "minimal humor", "light humor", "witty"),
        "empathy": pick("empathy", "neutral", "warm", "very supportive"),
        "verbosity": pick("verbosity", "concise", "moderate detail", "detailed"),
        "technical_depth": pick("technical_depth", "plain-language", "practical technical", "deep technical"),
        "proactivity": pick("proactivity", "reactive", "suggests next step", "proactive"),
    }


def build_persona_prompt_addendum(mode: str = "default") -> str:
    profile = load_persona_profile()
    labels = persona_style_labels(profile)
    lines = [
        "Nova persona contract:",
        f"- Assistant name: {profile.get('assistant_name','Nova')}",
        f"- Identity: {profile.get('identity','')}",
        f"- Self-model: {profile.get('self_model','')}",
        f"- Response contract: {profile.get('response_contract','')}",
        f"- Current mode: {mode}; mode guidance: {(profile.get('modes') or {}).get(mode) or (profile.get('modes') or {}).get('default','')}",
        "- Style sliders: " + ", ".join(f"{k}={v}" for k, v in labels.items()),
        "- Core traits: " + ", ".join(profile.get("core_traits", [])),
        "- Operating beliefs: " + "; ".join(profile.get("beliefs", [])[:6]),
        "- Avoid: " + "; ".join(profile.get("avoid", [])[:6]),
    ]
    note = str(profile.get("custom_system_note") or "").strip()
    if note:
        lines.append("- User custom system note: " + note[:1200])
    return "\n".join(lines).strip()


def build_custom_chat_window_spec() -> dict[str, Any]:
    profile = load_persona_profile()
    return {
        "ok": True,
        "title": "Custom Chat / Persona Window",
        "persona": profile,
        "sliders": [
            {"key": "formality", "left": "casual", "right": "formal", "value": profile["sliders"].get("formality", 0.35)},
            {"key": "creativity", "left": "literal", "right": "creative", "value": profile["sliders"].get("creativity", 0.55)},
            {"key": "humor", "left": "dry", "right": "witty", "value": profile["sliders"].get("humor", 0.25)},
            {"key": "empathy", "left": "neutral", "right": "warm", "value": profile["sliders"].get("empathy", 0.70)},
            {"key": "verbosity", "left": "concise", "right": "detailed", "value": profile["sliders"].get("verbosity", 0.45)},
            {"key": "technical_depth", "left": "plain", "right": "deep technical", "value": profile["sliders"].get("technical_depth", 0.70)},
            {"key": "proactivity", "left": "reactive", "right": "proactive", "value": profile["sliders"].get("proactivity", 0.55)},
        ],
        "prompt_addendum": build_persona_prompt_addendum(),
        "voice_integration": "Voice replies use conversational summaries plus the same persona style, with risky actions routed through approvals/receipts.",
        "idle_autonomous_integration": "Idle/autonomous mode receives persona + response contract but must still prioritize validation, receipts and preservation rules over style.",
    }


def render_persona_profile(profile: dict[str, Any] | None = None) -> str:
    profile = profile or load_persona_profile()
    labels = persona_style_labels(profile)
    lines = ["# Nova Persona Profile", "", f"Assistant: **{profile.get('assistant_name','Nova')}**", "", "## Identity", profile.get("identity", ""), "", "## Response contract", profile.get("response_contract", ""), "", "## Sliders"]
    for key, val in (profile.get("sliders") or {}).items():
        lines.append(f"- **{key}**: {val:.2f} ({labels.get(key, 'balanced')})")
    lines.extend(["", "## Core traits", "- " + "\n- ".join(profile.get("core_traits", [])), "", "## Beliefs", "- " + "\n- ".join(profile.get("beliefs", [])), "", "## Prompt addendum preview", "```text", build_persona_prompt_addendum(), "```", "", "Use `/persona-set formality=0.8 verbosity=0.3 humor=0.1` or `/persona-json { ... }` to update it."])
    return "\n".join(lines).strip() + "\n"


def append_voice_audit(transcript: str, action: str = "", status: str = "observed", source: str = "voice") -> dict[str, Any]:
    entry = {
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source": source,
        "transcript": transcript,
        "action": action,
        "status": status,
    }
    append_jsonl(VOICE_AUDIT_PATH, entry, ensure_ascii=False)
    return entry


def build_voice_audit(limit: int = 20) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    try:
        if VOICE_AUDIT_PATH.exists():
            lines = VOICE_AUDIT_PATH.read_text(encoding="utf-8", errors="replace").splitlines()[-int(limit or 20):]
            for line in lines:
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict):
                        items.append(obj)
                except Exception:
                    continue
    except Exception:
        LOGGER.debug("Failed to read voice audit entries from %s", VOICE_AUDIT_PATH, exc_info=True)
    return {"ok": True, "path": str(VOICE_AUDIT_PATH), "count": len(items), "items": items, "summary": f"{len(items)} voice audit entr{'y' if len(items)==1 else 'ies'}"}


def render_voice_audit(payload: dict[str, Any]) -> str:
    lines = ["# Voice Command Audit", "", payload.get("summary", ""), "", f"Path: `{payload.get('path','')}`", "", "## Recent voice commands"]
    if not payload.get("items"):
        lines.append("- No voice commands recorded yet.")
    for item in payload.get("items", []):
        lines.append(f"- {item.get('time','')} — **{item.get('status','')}** — {item.get('transcript','')} → `{item.get('action','')}`")
    return "\n".join(lines).strip() + "\n"
