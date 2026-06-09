from __future__ import annotations

"""Legacy capability continuity guard for Nova.

This module is intentionally deterministic: it does not need old zips to be
present, but it records the historically important capability anchors that were
added in earlier local-assistant versions and checks whether the current tree
still exposes their files/commands/markers.  When older release zips are placed
beside the current Nova folder, the report also lists them for manual diffing.
"""

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import json
import zipfile


@dataclass(frozen=True)
class LegacyAnchor:
    id: str
    introduced: str
    name: str
    why: str
    required_files: tuple[str, ...]
    required_text: tuple[tuple[str, str], ...]
    commands: tuple[str, ...]
    test_suggestions: tuple[str, ...]


LEGACY_ANCHORS: tuple[LegacyAnchor, ...] = (
    LegacyAnchor(
        id="odysseus_voyage_deck",
        introduced="v55.3.139",
        name="Odysseus-style voyage/workbench surfaces",
        why="Earlier versions exposed Chat/Agents, Cookbook, Deep Research, Compare, Documents, Notes/Tasks, Memory and Themes without digging through raw panels.",
        required_files=("winlocalassistant/webui.py", "winlocalassistant/nova_odysseus_suite.py"),
        required_text=(("winlocalassistant/core.py", "/nova-odysseus-suite"), ("winlocalassistant/core.py", "/nova-notes"), ("winlocalassistant/core.py", "/nova-tasks"), ("winlocalassistant/core.py", "/nova-docs")),
        commands=("/nova-odysseus-suite", "/nova-notes", "/nova-tasks", "/nova-docs", "/nova-skills", "/nova-presets"),
        test_suggestions=("tests_nova_odysseus_suite_v55_3_136.py", "tests_nova_eval_packs_v55_3_134.py"),
    ),
    LegacyAnchor(
        id="voice_wake_reliability",
        introduced="v55.3.141",
        name="Hey Nova voice/wake reliability and listener pause semantics",
        why="Voice/wake should not show listening while Nova is still thinking, and wake/listener diagnostics must remain available.",
        required_files=("start_nova_desktop_voice_listener.bat", "start_nova_desktop_voice_listener.ps1"),
        required_text=(("winlocalassistant/core.py", "/voice-troubleshoot"), ("winlocalassistant/core.py", "/voice-mode"), ("winlocalassistant/core.py", "/voice-audit")),
        commands=("/voice-mode", "/voice-troubleshoot", "/voice-audit", "/speak"),
        test_suggestions=("tests_v55_3_113_voice_wake_chat_mute.py", "tests_v55_3_118_unified_voice_ux.py", "tests_v55_3_120_voice_reliability_security.py"),
    ),
    LegacyAnchor(
        id="resize_activity_scroll",
        introduced="v55.3.141",
        name="Resizable panels and Live Activity scroll preservation",
        why="Live Activity and centre panels were previously hardened so polling/refreshes do not jump or cover the composer.",
        required_files=("winlocalassistant/webui.py",),
        required_text=(("winlocalassistant/webui.py", "liveActivity"), ("winlocalassistant/webui.py", "composer"), ("winlocalassistant/webui_emergency_stability.py", "NovaEmergencyStability")),
        commands=("/activity", "/live-timeline", "/gui-layout-status"),
        test_suggestions=("tests_v55_3_141_voice_resize_coding_flow.py", "tests_gui_interaction_overhaul.py", "tests_emergency_stability.py"),
    ),
    LegacyAnchor(
        id="pipeline_observability",
        introduced="v55.3.146",
        name="Pipeline routing, browser smoke and live timeline observability",
        why="Broad review/QA prompts should route to audits and evidence traces instead of unrelated project generation.",
        required_files=("winlocalassistant/pipeline_router.py",),
        required_text=(("winlocalassistant/core.py", "/pipeline-route"), ("winlocalassistant/core.py", "/browser-smoke"), ("winlocalassistant/core.py", "/live-timeline"), ("winlocalassistant/tools.py", "live_timeline")),
        commands=("/pipeline-route", "/browser-smoke", "/live-timeline", "/project-patterns"),
        test_suggestions=("tests_v55_3_146_pipeline_observability.py", "tests_v55_3_148_tool_awareness_orchestration.py"),
    ),
    LegacyAnchor(
        id="repo_session_memory",
        introduced="v55.3.147-v55.3.150",
        name="Repo/session memory, command verification and repo upgrade assurance",
        why="Nova should keep command-contract verification, repo-upgrade assurance, session evidence and codebase sanity routes.",
        required_files=("winlocalassistant/command_verifier.py", "winlocalassistant/regression_sweep.py"),
        required_text=(("winlocalassistant/core.py", "/command-verify"), ("winlocalassistant/core.py", "/repo-upgrade-assurance"), ("winlocalassistant/core.py", "/codebase-sanity-audit"), ("winlocalassistant/core.py", "/session-evidence")),
        commands=("/command-verify", "/repo-upgrade-assurance", "/codebase-sanity-audit", "/session-evidence", "/regression-sweep"),
        test_suggestions=("tests_command_verifier.py", "tests_v55_3_150_repo_research_codebase_audit.py", "tests_codebase_integrity_audit.py"),
    ),
    LegacyAnchor(
        id="provider_runtime",
        introduced="v55.3.163",
        name="Provider runtime lanes and local/remote routing gates",
        why="Modern Nova must preserve local-first Ollama plus optional guarded remote provider lanes and queue receipts.",
        required_files=("winlocalassistant/provider_runtime.py",),
        required_text=(("winlocalassistant/core.py", "/providers"), ("winlocalassistant/core.py", "/provider-route"), ("winlocalassistant/core.py", "/queue-status"), ("winlocalassistant/core.py", "/allow-internet")),
        commands=("/providers", "/provider-route", "/queue-status", "/allow-internet"),
        test_suggestions=("tests_nova_provider_runtime_v55_3_163.py",),
    ),
    LegacyAnchor(
        id="remote_scheduler_validation",
        introduced="v55.3.164",
        name="Scheduler, validation, remote access and Wake-on-LAN controls",
        why="Recent remote/profile/scheduler/validation work must stay guarded and testable.",
        required_files=("winlocalassistant/remote_access.py", "winlocalassistant/validate.py"),
        required_text=(("winlocalassistant/core.py", "/remote-access-test"), ("winlocalassistant/core.py", "/remote-profile"), ("winlocalassistant/core.py", "/remote-wake"), ("winlocalassistant/core.py", "/validation-status")),
        commands=("/remote-access-test", "/remote-profile", "/remote-wake", "/validation-status"),
        test_suggestions=("tests_nova_remote_access_v55_3_164.py", "tests_nova_scheduler_v55_3_164.py", "tests_validation_status_command.py"),
    ),
    LegacyAnchor(
        id="emergency_chat_help_layout",
        introduced="v55.3.164 emergency",
        name="Emergency chat/help/layout stability path",
        why="Normal chat must answer small prompts even when the local model is slow, and help must be concise by default.",
        required_files=("winlocalassistant/webui_emergency_stability.py", "winlocalassistant/command_help.py"),
        required_text=(("winlocalassistant/core.py", "render_concise_help"), ("winlocalassistant/core.py", "local_fallback"), ("winlocalassistant/webui_emergency_stability.py", "NovaEmergencyStability")),
        commands=("/help", "/help-full", "/command-help", "/llm-status"),
        test_suggestions=("tests_emergency_stability.py", "tests_smoke.py"),
    ),
)


def _read(root: Path, rel: str) -> str:
    p = root / rel
    if not p.exists() or not p.is_file():
        return ""
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _candidate_archives(root: Path) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    search_roots = [root, root.parent, root.parent.parent]
    seen: set[Path] = set()
    for base in search_roots:
        if not base.exists():
            continue
        for p in base.glob("*.zip"):
            if p in seen:
                continue
            seen.add(p)
            name = p.name.lower()
            if not any(k in name for k in ["nova", "winlocalassistant", "localassistant", "wla"]):
                continue
            info: dict[str, Any] = {"path": str(p), "name": p.name, "size_bytes": p.stat().st_size}
            try:
                with zipfile.ZipFile(p) as zf:
                    names = zf.namelist()
                    info["file_count"] = len(names)
                    info["has_core"] = any(n.endswith("winlocalassistant/core.py") for n in names)
                    info["has_webui"] = any(n.endswith("winlocalassistant/webui.py") for n in names)
                    info["has_tests"] = any(Path(n).name.startswith("tests_") and n.endswith(".py") for n in names)
            except Exception as exc:
                info["error"] = str(exc)
            candidates.append(info)
    candidates.sort(key=lambda x: x.get("name", ""))
    return candidates[:50]


def build_legacy_continuity_audit(root: str | Path = ".") -> dict[str, Any]:
    root = Path(root).expanduser().resolve()
    anchor_results: list[dict[str, Any]] = []
    for anchor in LEGACY_ANCHORS:
        missing_files = [rel for rel in anchor.required_files if not (root / rel).exists()]
        missing_text: list[dict[str, str]] = []
        for rel, needle in anchor.required_text:
            if needle not in _read(root, rel):
                missing_text.append({"file": rel, "needle": needle})
        ok = not missing_files and not missing_text
        status = "pass" if ok else "review"
        anchor_results.append({
            **asdict(anchor),
            "status": status,
            "ok": ok,
            "missing_files": missing_files,
            "missing_text": missing_text,
        })
    failed = [a for a in anchor_results if not a["ok"]]
    archives = _candidate_archives(root)
    payload = {
        "ok": not failed,
        "root": str(root),
        "anchor_count": len(anchor_results),
        "failed_count": len(failed),
        "anchors": anchor_results,
        "candidate_archives": archives,
        "limitations": [
            "This deterministic check covers known uploaded/diffed historical anchors and local zip candidates visible to this runtime.",
            "It cannot prove account-wide absence of a regression unless every historical zip/source tree is supplied or discoverable.",
            "Unknown old features should be added as new anchors once found.",
        ],
        "recommended_tests": sorted({t for a in LEGACY_ANCHORS for t in a.test_suggestions}),
    }
    return payload


def write_legacy_contract(root: str | Path = ".") -> Path:
    root = Path(root).expanduser().resolve()
    payload = build_legacy_continuity_audit(root)
    out = root / "docs" / "NOVA_LEGACY_CONTINUITY_CONTRACT.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out


def render_legacy_continuity_audit(payload: dict[str, Any]) -> str:
    lines = [
        "# Nova Legacy Continuity Audit",
        "",
        f"Status: **{'PASS' if payload.get('ok') else 'REVIEW'}**",
        f"Root: `{payload.get('root')}`",
        f"Anchors checked: `{payload.get('anchor_count')}`",
        f"Anchors needing review: `{payload.get('failed_count')}`",
        "",
        "## Historical capability anchors",
    ]
    for a in payload.get("anchors", []):
        status = "PASS" if a.get("ok") else "REVIEW"
        lines += [
            "",
            f"### {status}: {a.get('name')}",
            f"- Introduced: `{a.get('introduced')}`",
            f"- Why preserve it: {a.get('why')}",
            f"- Commands: {', '.join('`' + c + '`' for c in a.get('commands', []))}",
        ]
        if a.get("missing_files"):
            lines.append("- Missing files: " + ", ".join(f"`{x}`" for x in a.get("missing_files", [])))
        if a.get("missing_text"):
            lines.append("- Missing markers: " + ", ".join(f"`{m.get('needle')}` in `{m.get('file')}`" for m in a.get("missing_text", [])))
        if a.get("test_suggestions"):
            lines.append("- Tests: " + ", ".join(f"`{t}`" for t in a.get("test_suggestions", [])))
    archives = payload.get("candidate_archives", [])
    lines += ["", "## Local candidate archives discovered"]
    if not archives:
        lines.append("- None found beside this workspace. Put older Nova release zips next to the folder and rerun `/legacy-continuity-audit` for visibility.")
    else:
        for z in archives[:12]:
            suffix = []
            if z.get("has_core"):
                suffix.append("core")
            if z.get("has_webui"):
                suffix.append("webui")
            if z.get("has_tests"):
                suffix.append("tests")
            lines.append(f"- `{z.get('name')}` — {z.get('file_count', '?')} files" + (f" ({', '.join(suffix)})" if suffix else ""))
    lines += [
        "",
        "## Regression lock instructions",
        "- Add every newly recovered valuable feature as an anchor in `winlocalassistant/legacy_continuity.py`.",
        "- Run `/legacy-continuity-audit` before packaging any GUI/core/autonomous patch.",
        "- Run the suggested tests for changed areas; do not delete old anchors just because they are inconvenient.",
        "",
        "## Limitations",
    ]
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    return "\n".join(lines)
