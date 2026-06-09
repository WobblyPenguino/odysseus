from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .safe_io import atomic_write_text
from typing import Any


@dataclass(frozen=True)
class ToolCatalogEntry:
    name: str
    purpose: str
    risk: str
    requires_confirmation: bool
    verification: list[str]
    fallback: list[str]
    never_use_for: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


CATALOG: list[ToolCatalogEntry] = [
    ToolCatalogEntry("idle_once", "Read-only idle analysis and candidate scoring", "low", False, ["idle report written"], ["idle propose"], ["source editing"]),
    ToolCatalogEntry("idle_propose", "Dry-run improvement proposal", "low", False, ["proposal report written"], ["manual review"], ["applying patches"]),
    ToolCatalogEntry("project_spec", "Create a deterministic project brief from the user's exact specification", "low", False, ["PROJECT_BUILD_BRIEF.md", "acceptance tests"], ["ask clarifying question", "manual project plan"], ["mutation beyond report files"]),
    ToolCatalogEntry("ai_create_project", "Create the user-requested project/artifact", "medium", False, ["project quality", "runtime probe", "acceptance contract"], ["project repair plan"], ["editing Nova source"]),
    ToolCatalogEntry("improve_project", "Improve current project files", "medium", True, ["project tests", "quality score"], ["surgical repair", "backtrack"], ["unsafe Nova self-edit"]),
    ToolCatalogEntry("run_shell", "Run a workspace command", "medium", True, ["exit code", "stdout/stderr review"], ["diagnose command error"], ["package/network/delete without approval"]),
    ToolCatalogEntry("self_improve", "Manual guarded Nova source improvement", "high", True, ["backup", "diff", "py_compile", "smoke tests", "rollback"], ["rollback", "surgical fallback"], ["automatic idle/autonomous invocation"]),
    ToolCatalogEntry("quality_dashboard", "Summarise Nova/project health and next actions", "low", False, ["report written"], ["manual inspection"], ["mutation"]),
    ToolCatalogEntry("code_repair_audit", "Deterministic bug/repair audit for syntax, duplicate definitions, swallowed exceptions and release hygiene", "low", False, ["repair audit markdown/json written"], ["deep code review", "manual inspection"], ["mutation"]),
    ToolCatalogEntry("code_review_audit", "Deeper read-only reliability and maintainability review", "low", False, ["review markdown/json written"], ["repair audit", "manual inspection"], ["mutation"]),
    ToolCatalogEntry("code_quality_gate", "CodeRabbit-style local code verification gate with file/line comments and pass/warn/block decision", "low", False, ["quality-gate markdown/json written", "blocking/warning counts visible"], ["repair audit", "deep code review", "manual inspection"], ["external CodeRabbit SaaS calls", "mutation"]),
    ToolCatalogEntry("codebase_integrity_audit", "Whole-codebase integrity audit for syntax, imports, version markers, release hygiene and aggregated quality gates", "low", False, ["integrity markdown/json written", "decision and issue ledger visible"], ["code_quality_gate", "repair audit", "pytest"], ["mutation", "external services"]),
    ToolCatalogEntry("sandbox_status", "Inspect Docker/Podman runtime, sandbox policy and known Linux/Kali sandbox state", "low", False, ["runtime availability", "policy summary"], ["manual Docker/Podman check"], ["mutation", "running arbitrary commands"]),
    ToolCatalogEntry("sandbox_start", "Start a disposable Linux or Kali sandbox with bounded resources and safe defaults", "medium", True, ["container id", "state file", "audit log"], ["install Docker/Podman", "manual container run"], ["host privilege escalation", "unapproved external targets"]),
    ToolCatalogEntry("sandbox_exec", "Run a policy-checked command inside an existing disposable sandbox", "medium", True, ["stdout/stderr", "return code", "audit log"], ["sandbox_status", "manual terminal"], ["host-control commands", "unauthorised offensive security activity"]),
]


def get_tool_catalog() -> list[ToolCatalogEntry]:
    return list(CATALOG)


def find_tool_entry(name: str) -> ToolCatalogEntry | None:
    low = (name or "").lower().strip().replace("-", "_")
    for entry in CATALOG:
        if entry.name == low or entry.name.replace("_", "-") == low:
            return entry
    return None


def render_tool_catalog_markdown() -> str:
    lines = ["# Nova Tool Catalogue", "", "Tools are grouped by risk, verification and fallback expectations.", ""]
    for entry in CATALOG:
        lines += [
            f"## {entry.name}",
            f"- Purpose: {entry.purpose}",
            f"- Risk: {entry.risk}",
            f"- Requires confirmation: {entry.requires_confirmation}",
            f"- Verification: {', '.join(entry.verification)}",
            f"- Fallback: {', '.join(entry.fallback)}",
            f"- Never use for: {', '.join(entry.never_use_for)}",
            "",
        ]
    return "\n".join(lines)


def write_tool_catalog_docs(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(path, render_tool_catalog_markdown())
    return path


def catalog_as_json() -> str:
    return json.dumps([entry.to_dict() for entry in CATALOG], indent=2)
