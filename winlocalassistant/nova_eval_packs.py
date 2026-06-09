from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable


@dataclass(frozen=True)
class NovaEvalCase:
    name: str
    command: str
    purpose: str
    expected_markers: tuple[str, ...]
    capability: str
    risk: str = "read_only"


@dataclass
class NovaEvalResult:
    name: str
    command: str
    purpose: str
    capability: str
    risk: str
    ok: bool
    missing_markers: list[str]
    output_preview: str
    error: str = ""


def nova_eval_packs() -> dict[str, list[NovaEvalCase]]:
    """Deterministic eval packs for proving Nova behaviour after upgrades.

    The packs intentionally use read-only or profile-report commands only. They
    are small enough to run during refactors, but broad enough to catch broken
    routing, overclaiming, local-model context loss and release-surface drift.
    """
    return {
        "core": [
            NovaEvalCase("version_alignment", "/version", "Version and product identity stay aligned", ("Nova", "Version"), "identity"),
            NovaEvalCase("status_available", "/status", "Runtime status remains available", ("workspace",), "runtime"),
            NovaEvalCase("help_surface", "/help", "Main command help renders", ("Commands", "/nova-eval-packs"), "routing"),
        ],
        "release": [
            NovaEvalCase("brand_audit", "/nova-brand-audit", "Visible release text stays Nova branded", ("Nova Brand Audit", "Legacy visible mentions"), "release_hygiene"),
            NovaEvalCase("command_contracts", "/command-verify", "Read-only command contracts still pass", ("Nova Command Verification", "Passed:"), "regression"),
            NovaEvalCase("mcp_manifest", "/mcp-export-manifest", "MCP-style export still exposes safe surfaces", ("Nova MCP-style", "Security"), "integration"),
        ],
        "agent": [
            NovaEvalCase("trace_observability", "/trace-observability improve Nova safely", "Trace-first debugging plan remains routed", ("Trace", "Observability"), "observability"),
            NovaEvalCase("guardrail_memory", "/guardrail-memory improve Nova => command execution", "Guardrail memory planning remains routed", ("Guardrail", "Memory"), "guardrails"),
            NovaEvalCase("context_router", "/context-router-policy improve coding reliability", "Context routing policy remains available", ("Context", "Router"), "context"),
        ],
        "coding": [
            NovaEvalCase("coding_audit", "/coding-audit build a python cli", "Coding capability audit remains request-aware", ("Coding", "Audit"), "coding"),
            NovaEvalCase("verifier_ladder", "/verifier-ladder build a python cli => python", "Verifier ladder generation remains routed", ("Verifier", "Ladder"), "validation"),
            NovaEvalCase("patch_impact", "/patch-impact-plan winlocalassistant/core.py", "Patch impact planning maps changed files to checks", ("Patch", "Impact"), "regression"),
        ],
        "voice": [
            NovaEvalCase("voice_pipeline", "/voice-pipeline-review Hey Nova wake pipeline", "Voice pipeline review remains available", ("Voice", "Pipeline"), "voice"),
            NovaEvalCase("voice_audit", "/voice-audit", "Voice audit command remains available", ("Voice", "Audit"), "voice"),
        ],
        "odysseus": [
            NovaEvalCase("odysseus_suite", "/nova-odysseus-suite", "Odysseus feature-port coverage remains routed", ("Odysseus Feature Suite", "Coverage"), "integration"),
            NovaEvalCase("tool_permissions", "/nova-tool-permissions check write file", "Privileged tool gate classifier remains available", ("Tool Permissions", "Decision"), "security"),
            NovaEvalCase("cookbook", "/nova-cookbook whatif ram=32 vram=16 => coding", "Hardware-aware model recommendations remain available", ("Model Cookbook", "Recommended local models"), "models"),
            NovaEvalCase("compare", "/nova-compare plan Improve Nova => qwen2.5-coder:7b, qwen2.5:14b", "Blind model comparison receipts remain available", ("Blind Model Compare", "Comparison ID"), "models"),
            NovaEvalCase("docs", "/nova-docs list", "Document vault command remains available", ("Nova Documents",), "documents"),
            NovaEvalCase("integration_gates", "/nova-integration-gates", "Integration gate status remains available", ("Integration Gates", "High-risk surfaces"), "security"),
            NovaEvalCase("fastapi_plan", "/nova-fastapi-plan", "FastAPI migration plan remains available", ("FastAPI Architecture Plan", "hybrid"), "architecture"),
            NovaEvalCase("api_status", "/nova-api-status", "Actual optional FastAPI bridge status remains routed", ("FastAPI Bridge Status", "Routes"), "architecture"),
            NovaEvalCase("gui_workbench", "/nova-gui-workbench-plan", "Odysseus-style GUI workbench plan remains available", ("GUI Workbench Plan", "Rail"), "ux"),
        ],
    }


def _preview(text: str, limit: int = 700) -> str:
    compact = "\n".join(str(text or "").splitlines()[:18])
    if len(compact) > limit:
        return compact[: limit - 3] + "..."
    return compact


def select_eval_cases(pack: str = "core") -> tuple[str, list[NovaEvalCase], list[str]]:
    packs = nova_eval_packs()
    requested = (pack or "core").strip().lower()
    aliases = {"all": "all", "default": "core", "safe": "core", "regression": "release"}
    requested = aliases.get(requested, requested)
    if requested == "all":
        cases: list[NovaEvalCase] = []
        for name in ("core", "release", "agent", "coding", "voice", "odysseus"):
            cases.extend(packs[name])
        return "all", cases, list(packs)
    if requested not in packs:
        return requested, [], list(packs)
    return requested, packs[requested], list(packs)


def build_nova_eval_plan(pack: str = "core") -> dict:
    selected, cases, available = select_eval_cases(pack)
    return {
        "ok": bool(cases),
        "mode": "plan",
        "pack": selected,
        "available_packs": available,
        "total_cases": len(cases),
        "cases": [asdict(case) for case in cases],
        "validation_hint": "/nova-eval-packs run all",
    }


def run_nova_eval_pack(run_command: Callable[[str], str], pack: str = "core") -> dict:
    selected, cases, available = select_eval_cases(pack)
    if not cases:
        return {
            "ok": False,
            "mode": "run",
            "pack": selected,
            "available_packs": available,
            "total_cases": 0,
            "passed": 0,
            "failed": 0,
            "results": [],
            "error": f"Unknown eval pack '{selected}'.",
        }
    results: list[NovaEvalResult] = []
    for case in cases:
        try:
            output = str(run_command(case.command) or "")
            lower = output.lower()
            missing = [marker for marker in case.expected_markers if marker.lower() not in lower]
            forbidden = any(marker in lower for marker in ("unknown command", "command error:"))
            ok = bool(output.strip()) and not missing and not forbidden
            if forbidden and not missing:
                missing = ["no Unknown command/Command error"]
            results.append(
                NovaEvalResult(
                    name=case.name,
                    command=case.command,
                    purpose=case.purpose,
                    capability=case.capability,
                    risk=case.risk,
                    ok=ok,
                    missing_markers=missing,
                    output_preview=_preview(output),
                )
            )
        except Exception as exc:
            results.append(
                NovaEvalResult(
                    name=case.name,
                    command=case.command,
                    purpose=case.purpose,
                    capability=case.capability,
                    risk=case.risk,
                    ok=False,
                    missing_markers=list(case.expected_markers),
                    output_preview="",
                    error=str(exc),
                )
            )
    passed = sum(1 for item in results if item.ok)
    failed = len(results) - passed
    return {
        "ok": failed == 0,
        "mode": "run",
        "pack": selected,
        "available_packs": available,
        "total_cases": len(results),
        "passed": passed,
        "failed": failed,
        "results": [asdict(item) for item in results],
    }


def render_nova_eval_packs(payload: dict) -> str:
    pack = payload.get("pack", "core")
    mode = payload.get("mode", "plan")
    lines = ["# Nova Eval Packs", "", f"Mode: **{mode}**", f"Pack: **{pack}**"]
    if payload.get("error"):
        lines += ["", f"Error: {payload.get('error')}", "", "Available packs: " + ", ".join(payload.get("available_packs", []))]
        return "\n".join(lines)
    if mode == "run":
        lines += [f"Result: **{'PASS' if payload.get('ok') else 'FAIL'}**", f"Passed: {payload.get('passed', 0)}/{payload.get('total_cases', 0)}", "", "## Results"]
        for item in payload.get("results", []):
            status = "PASS" if item.get("ok") else "FAIL"
            lines.append(f"- **{status}** `{item.get('command')}` — {item.get('purpose')} [{item.get('capability')}]")
            if item.get("missing_markers"):
                lines.append("  - Missing/failed markers: " + ", ".join(map(str, item.get("missing_markers", []))))
            if item.get("error"):
                lines.append("  - Error: " + str(item.get("error")))
        return "\n".join(lines)
    lines += [f"Cases: **{payload.get('total_cases', 0)}**", "", "## Planned checks"]
    for case in payload.get("cases", []):
        lines.append(f"- `{case.get('command')}` — {case.get('purpose')} [{case.get('capability')}, {case.get('risk')}]")
    lines += ["", "Run a pack with `/nova-eval-packs run core`, `/nova-eval-packs run release`, or `/nova-eval-packs run all`."]
    return "\n".join(lines)
