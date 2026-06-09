from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Callable, Iterable


@dataclass(frozen=True)
class CommandContract:
    command: str
    purpose: str
    expected_markers: tuple[str, ...]
    forbidden_markers: tuple[str, ...] = ("Command error:", "Unknown command")
    category: str = "read_only"
    profile_write_only: bool = False


@dataclass
class CommandContractResult:
    command: str
    purpose: str
    ok: bool
    category: str
    expected_markers: list[str]
    missing_markers: list[str]
    forbidden_hits: list[str]
    output_preview: str
    error: str = ""


def default_command_contracts() -> list[CommandContract]:
    """Safe command contracts used to verify existing Nova commands behave as intended.

    These intentionally avoid destructive commands and commands that require a live local model,
    shell mutation, internet access, package installation, or project file writes. Some commands may
    write reports to Nova's profile directory; those are marked profile_write_only.
    """
    return [
        CommandContract("/version", "Show version and consistency checks", ("Nova", "Version")),
        CommandContract("/help", "Show command help", ("Commands", "/status", "/help")),
        CommandContract("/status", "Show runtime status", ("workspace",)),
        CommandContract("/idle status", "Show idle state", ("Idle",)),
        CommandContract("/autonomous status", "Show autonomous state", ("Autonomous",)),
        CommandContract("/autonomous-memory", "Show autonomous failure memory", ("Autonomous", "memory")),
        CommandContract("/autonomous-plan verify current project", "Preview autonomous sequence", ("Autonomous", "Sequence")),
        CommandContract("/autonomous-explain verify current project", "Explain autonomous state/plan", ("Autonomous", "What")),
        CommandContract("/planning-dashboard make a calculator and verify it", "Show planning dashboard", ("Planning", "Dashboard")),
        CommandContract("/tool-catalog", "Show command/tool catalogue", ("Tool", "catalog")),
        CommandContract("/interaction-lessons", "Show interaction learning state", ("Interaction", "lesson")),
        CommandContract("/avatar", "Show avatar state", ("Updated",)),
        CommandContract("/quality-dashboard verify current project", "Write/read quality dashboard report", ("Quality", "Dashboard"), profile_write_only=True),
        CommandContract("/architecture-audit", "Write/read architecture continuity audit", ("Architecture", "Audit"), profile_write_only=True),
        CommandContract("/autonomous-journal", "Show latest autonomous journal", ("Autonomous", "Journal"), profile_write_only=True),
        CommandContract("/model-health", "Show degraded-mode model dependency health", ("Model", "Health")),
        CommandContract("/command-timeout status", "Show shell command timeout", ("Shell", "timeout")),
        CommandContract("/model-context", "Preview local model Nova context pack", ("Local", "Context", "Nova")),
        CommandContract("/self-awareness", "Write/read capability audit", ("Self", "awareness"), profile_write_only=True),
    ]


def _preview(text: str, limit: int = 800) -> str:
    compact = "\n".join(str(text or "").splitlines()[:24])
    if len(compact) > limit:
        return compact[: limit - 3] + "..."
    return compact


def verify_command_contracts(
    run_command: Callable[[str], str],
    contracts: Iterable[CommandContract] | None = None,
) -> dict:
    """Run non-destructive command contracts and return detailed pass/fail evidence."""
    selected = list(contracts or default_command_contracts())
    results: list[CommandContractResult] = []
    for contract in selected:
        try:
            output = run_command(contract.command)
            output_text = str(output or "")
            lower = output_text.lower()
            missing = [m for m in contract.expected_markers if m.lower() not in lower]
            forbidden = [m for m in contract.forbidden_markers if m.lower() in lower]
            ok = not missing and not forbidden and bool(output_text.strip())
            results.append(
                CommandContractResult(
                    command=contract.command,
                    purpose=contract.purpose,
                    ok=ok,
                    category=contract.category,
                    expected_markers=list(contract.expected_markers),
                    missing_markers=missing,
                    forbidden_hits=forbidden,
                    output_preview=_preview(output_text),
                )
            )
        except Exception as exc:
            results.append(
                CommandContractResult(
                    command=contract.command,
                    purpose=contract.purpose,
                    ok=False,
                    category=contract.category,
                    expected_markers=list(contract.expected_markers),
                    missing_markers=list(contract.expected_markers),
                    forbidden_hits=[],
                    output_preview="",
                    error=str(exc),
                )
            )
    passed = sum(1 for result in results if result.ok)
    failed = len(results) - passed
    return {
        "ok": failed == 0,
        "passed": passed,
        "failed": failed,
        "total": len(results),
        "results": [asdict(result) for result in results],
    }


def render_command_verification_markdown(report: dict) -> str:
    lines = [
        "# Nova Command Verification",
        "",
        f"Result: **{'PASS' if report.get('ok') else 'FAIL'}**",
        f"Passed: {report.get('passed', 0)}/{report.get('total', 0)}",
        "",
        "## Checked commands",
    ]
    for item in report.get("results", []):
        status = "PASS" if item.get("ok") else "FAIL"
        lines.append(f"- **{status}** `{item.get('command')}` — {item.get('purpose','')}")
        if item.get("missing_markers"):
            lines.append("  - Missing expected markers: " + ", ".join(map(str, item.get("missing_markers", []))))
        if item.get("forbidden_hits"):
            lines.append("  - Forbidden output markers: " + ", ".join(map(str, item.get("forbidden_hits", []))))
        if item.get("error"):
            lines.append("  - Error: " + str(item.get("error")))
    if not report.get("ok"):
        lines.extend([
            "",
            "## Recommended next step",
            "Investigate the failing command output preview and add a narrow regression test before changing behaviour.",
        ])
    return "\n".join(lines)
