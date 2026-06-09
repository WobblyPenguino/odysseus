from __future__ import annotations

import argparse
import ast
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .release_packager import collect_release_files

CODEBASE_ADVISOR_SCHEMA_VERSION = 1


@dataclass
class AdvisorFinding:
    id: str
    title: str
    status: str
    priority: str
    evidence: str
    recommendation: str
    implemented_now: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _read(path: Path, limit: int = 300_000) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        return text[:limit]
    except Exception:
        return ""


def _count_lines(path: Path) -> int:
    try:
        return len(path.read_text(encoding="utf-8", errors="replace").splitlines())
    except Exception:
        return 0


def _count_broad_silent_excepts(root: Path) -> int:
    count = 0
    for path in (root / "winlocalassistant").glob("*.py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is not None:
                if isinstance(node.type, ast.Name) and node.type.id == "Exception":
                    if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                        count += 1
    return count


def _rendered_webui_text_for_root(root: Path, fallback: str) -> str:
    """Return served GUI HTML for the active checkout when it is cheap to import."""
    try:
        package_root = Path(__file__).resolve().parents[1]
        if root == package_root:
            from .webui import HTML

            return str(HTML)
    except Exception:
        return fallback
    return fallback


def build_codebase_advisor(root: str | Path = ".") -> dict[str, Any]:
    root = Path(root).expanduser().resolve()
    webui = root / "winlocalassistant" / "webui.py"
    core = root / "winlocalassistant" / "core.py"
    tools = root / "winlocalassistant" / "tools.py"
    init_text = _read(root / "winlocalassistant" / "__init__.py", 20_000)
    webui_text = _read(webui)
    rendered_webui_text = _rendered_webui_text_for_root(root, webui_text)
    core_text = _read(core)
    tools_text = _read(tools)
    version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', init_text)
    version = version_match.group(1) if version_match else "unknown"
    release_set = collect_release_files(root)
    findings: list[AdvisorFinding] = []

    findings.append(AdvisorFinding(
        id="clean_release_packaging",
        title="Create clean release packages instead of zipping caches/reports by hand",
        status="implemented",
        priority="high",
        evidence=f"Release collector found {len(release_set.get('files') or [])} shippable files and {len(release_set.get('skipped') or [])} generated/cache files that should be excluded.",
        recommendation="Use /release-package before sharing Nova builds; it writes a manifest, excludes cache/report bloat, and gives validation commands.",
        implemented_now=True,
    ))

    findings.append(AdvisorFinding(
        id="codebase_advisor",
        title="Add a deterministic improvement advisor so future work is ranked, not random",
        status="implemented",
        priority="high",
        evidence="The advisor inspects webui/core/tool size, version markers, release packaging readiness, and regression-test coverage.",
        recommendation="Use /codebase-advisor after each patch to decide what should be improved next and what should remain protected.",
        implemented_now=True,
    ))

    webui_lines = _count_lines(webui)
    if webui_lines > 900:
        findings.append(AdvisorFinding(
            id="split_webui_assets",
            title="Split the very large web UI into separate CSS/JS asset builders",
            status="proposed",
            priority="high",
            evidence=f"webui.py is about {webui_lines} lines and contains HTML, CSS, JS, API routing, and rendering logic together.",
            recommendation="Next: move browser JS helpers into a versioned web asset module or template fragments, then test with node --check and existing GUI regression tests.",
        ))

    core_lines = _count_lines(core)
    if core_lines > 4000:
        findings.append(AdvisorFinding(
            id="split_command_router",
            title="Split the giant command router into command groups",
            status="proposed",
            priority="high",
            evidence=f"core.py is about {core_lines} lines, making command changes risky and harder to regression-test locally.",
            recommendation="Next: extract persona/voice/autonomous/release command handlers into modules while keeping public slash commands unchanged.",
        ))

    if version != "unknown" and (f"v{version}" in webui_text or f"v{version}" in rendered_webui_text):
        findings.append(AdvisorFinding(
            id="visible_version_consistency",
            title="Current version is visible in the package and GUI",
            status="protected",
            priority="medium",
            evidence=f"v{version} appears in the served GUI HTML and __init__.py.",
            recommendation="Keep this continuity check in feature-continuity and release tests to catch stale UI banners.",
        ))
    else:
        findings.append(AdvisorFinding(
            id="visible_version_consistency",
            title="Version marker drift risk",
            status="needs_fix",
            priority="high",
            evidence=f"Package version is {version}, but the GUI banner may not expose that exact version.",
            recommendation="Update the web UI banner and version continuity tests before release.",
        ))

    def _version_key(name: str) -> int:
        match = re.search(r"tests_v55_3_(\d+)", name)
        return int(match.group(1)) if match else -1
    version_tail = version.split(".")[-1] if version != "unknown" else ""
    latest_tests = sorted((p.name for p in root.glob("tests_v55_3_*.py")), key=_version_key)[-8:]
    current_test_present = any(f"tests_v55_3_{version_tail}_" in name for name in latest_tests) if version_tail else False
    findings.append(AdvisorFinding(
        id="latest_regression_chain",
        title="Recent patch regression chain is present",
        status="protected" if current_test_present else "needs_review",
        priority="medium",
        evidence="Latest visible v55.3 test files: " + ", ".join(latest_tests),
        recommendation="Keep each new feature paired with a versioned regression test and include it in completion/nova validation paths.",
    ))

    silent_excepts = _count_broad_silent_excepts(root)
    findings.append(AdvisorFinding(
        id="silent_exception_debt",
        title="Reduce silent broad exception blocks over time",
        status="proposed" if silent_excepts else "protected",
        priority="medium",
        evidence=f"Static AST scan found {silent_excepts} direct `except Exception: pass` block(s) in package modules.",
        recommendation="Replace silent catches with structured debug logging or narrow expected exception types, starting with UI/status refresh paths.",
    ))

    if "release_package" in tools_text and "/release-package" in core_text:
        findings.append(AdvisorFinding(
            id="release_command_wired",
            title="Release packaging command is wired end-to-end",
            status="implemented",
            priority="high",
            evidence="Tool registry and slash-command routing include release packaging markers.",
            recommendation="Expose /release-package in the left command centre and keep the command read-only except for writing the output zip.",
            implemented_now=True,
        ))

    priority_order = {"high": 0, "medium": 1, "low": 2}
    status_order = {"needs_fix": 0, "proposed": 1, "implemented": 2, "protected": 3}
    ranked = sorted([item.to_dict() for item in findings], key=lambda x: (priority_order.get(x.get("priority", "low"), 9), status_order.get(x.get("status", "proposed"), 9), x.get("id", "")))
    implemented = [item for item in ranked if item.get("implemented_now")]
    proposed = [item for item in ranked if item.get("status") == "proposed"]
    ok = not any(item.get("status") == "needs_fix" for item in ranked)
    return {
        "schema_version": CODEBASE_ADVISOR_SCHEMA_VERSION,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "root": str(root),
        "version": version,
        "ok": ok,
        "summary": "codebase advisor completed" if ok else "codebase advisor found release blockers",
        "implemented_now": implemented,
        "next_proposals": proposed,
        "findings": ranked,
        "metrics": {
            "webui_lines": webui_lines,
            "core_lines": core_lines,
            "tools_lines": _count_lines(tools),
            "release_file_count": len(release_set.get("files") or []),
            "release_skipped_count": len(release_set.get("skipped") or []),
            "silent_exception_pass_count": silent_excepts,
        },
    }


def render_codebase_advisor(payload: dict[str, Any]) -> str:
    lines = [
        "# Codebase Improvement Advisor",
        "",
        f"Summary: {payload.get('summary','')}",
        f"Root: `{payload.get('root','')}`",
        f"Version: `{payload.get('version','unknown')}`",
        "",
        "## Implemented in this pass",
    ]
    implemented = payload.get("implemented_now") or []
    if implemented:
        for item in implemented:
            lines.append(f"- **{item.get('title')}** — {item.get('recommendation')}")
    else:
        lines.append("- No implemented items were recorded.")
    lines.append("\n## Recommended next improvements")
    proposed = payload.get("next_proposals") or []
    if proposed:
        for item in proposed:
            lines.append(f"- **{item.get('priority','medium').upper()}** `{item.get('id')}`: {item.get('title')}")
            lines.append(f"  - Evidence: {item.get('evidence')}")
            lines.append(f"  - Next: {item.get('recommendation')}")
    else:
        lines.append("- No proposed items remain from the current scan.")
    lines.append("\n## All findings")
    for item in payload.get("findings") or []:
        lines.append(f"- {item.get('status')} / {item.get('priority')}: `{item.get('id')}` — {item.get('title')}")
    metrics = payload.get("metrics") or {}
    lines.append("\n## Metrics")
    for key, value in metrics.items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines).strip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect Nova and rank practical next codebase improvements.")
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    payload = build_codebase_advisor(args.root)
    print(render_codebase_advisor(payload))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
