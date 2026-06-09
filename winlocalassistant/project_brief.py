from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .project_acceptance import build_project_acceptance_contract
from .nova_coding_capabilities import plan_coding_execution
from .safe_io import atomic_write_json, atomic_write_text


@dataclass(frozen=True)
class ProjectBuildBrief:
    """Deterministic project brief used before autonomous/code generation.

    The local model can be weak or overly generic. This brief turns the user's
    request into concrete domain objects, workflows, edge cases and acceptance
    checks so project creation is less likely to drift into a generic demo.
    """

    goal: str
    artifact_type: str
    domain: str
    audience: str
    functional_requirements: list[str] = field(default_factory=list)
    data_model: list[str] = field(default_factory=list)
    ui_states: list[str] = field(default_factory=list)
    edge_cases: list[str] = field(default_factory=list)
    nonfunctional_requirements: list[str] = field(default_factory=list)
    suggested_files: list[str] = field(default_factory=list)
    acceptance_tests: list[str] = field(default_factory=list)
    verification_commands: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_prompt_text(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


def infer_project_build_brief(goal: str) -> ProjectBuildBrief:
    text = (goal or "").strip()
    low = text.lower()
    contract = build_project_acceptance_contract(text)
    coding_plan = plan_coding_execution(text)
    planned_type = str(coding_plan.get("artifact_type") or "")
    contract_type = str(contract.artifact_type or "")
    specific_browser_types = {"calculator", "todo_app", "snake_game", "browser_game"}
    if contract_type in specific_browser_types and planned_type in {"html_css_js_app", "html_css_js_game"}:
        artifact_type = contract_type
    else:
        artifact_type = planned_type or contract_type
    domain = _infer_domain(low, artifact_type)
    audience = _infer_audience(low)
    features = _feature_phrases(text)
    functional = _base_functional_requirements(low, artifact_type, domain)
    for feature in features:
        requirement = f"Implement requested capability: {feature}"
        if requirement not in functional:
            functional.append(requirement)
    data_model = _data_model_for(low, artifact_type, domain)
    ui_states = _ui_states_for(low, artifact_type, domain)
    edge_cases = _edge_cases_for(low, artifact_type, domain)
    suggested_files = list(coding_plan.get("expected_files") or _suggested_files_for(artifact_type, domain))
    nonfunctional = [
        "Runs locally on Windows without hidden cloud dependencies unless the user explicitly requested an API.",
        "Uses clear labels, empty states and error messages so a human can tell what to do next.",
        "Keeps README/run instructions accurate; do not claim features that are not implemented in code.",
    ]
    if any(token in low for token in ["save", "persist", "localstorage", "history"]):
        nonfunctional.append("Persist user data with localStorage or an explicit local file workflow, and handle missing/invalid saved data safely.")
    acceptance = list(contract.required_behaviours)
    acceptance.extend(_extra_acceptance_for(low, artifact_type, domain, features))
    verification = [cmd for cmd in [str(coding_plan.get("verify_command") or "")] + list(coding_plan.get("optional_verify_commands") or []) if cmd]
    if not verification:
        verification = _verification_commands_for(artifact_type, domain)
    assumptions = _dedupe(_assumptions_for(low, artifact_type, domain) + [str(coding_plan.get("why") or "")])
    return ProjectBuildBrief(
        goal=text,
        artifact_type=artifact_type,
        domain=domain,
        audience=audience,
        functional_requirements=_dedupe(functional)[:24],
        data_model=_dedupe(data_model)[:18],
        ui_states=_dedupe(ui_states)[:18],
        edge_cases=_dedupe(edge_cases)[:18],
        nonfunctional_requirements=_dedupe(nonfunctional)[:12],
        suggested_files=suggested_files,
        acceptance_tests=_dedupe(acceptance)[:28],
        verification_commands=verification,
        assumptions=assumptions,
    )


def render_project_build_brief_markdown(brief: ProjectBuildBrief) -> str:
    sections = [
        ("Functional requirements", brief.functional_requirements),
        ("Data model / state", brief.data_model),
        ("UI states / screens", brief.ui_states),
        ("Edge cases", brief.edge_cases),
        ("Non-functional requirements", brief.nonfunctional_requirements),
        ("Acceptance tests", brief.acceptance_tests),
        ("Verification commands", brief.verification_commands),
        ("Assumptions", brief.assumptions),
    ]
    lines = [
        "# Project Build Brief",
        "",
        f"Goal: {brief.goal}",
        f"Artifact type: {brief.artifact_type}",
        f"Domain: {brief.domain}",
        f"Audience: {brief.audience}",
        "",
        "Suggested files: " + ", ".join(brief.suggested_files),
    ]
    for title, items in sections:
        lines.extend(["", f"## {title}"])
        lines.extend([f"- {item}" for item in items] or ["- none inferred"])
    return "\n".join(lines) + "\n"


def write_project_build_brief(root: Path, brief: ProjectBuildBrief) -> tuple[Path, Path]:
    root.mkdir(parents=True, exist_ok=True)
    md_path = root / "PROJECT_BUILD_BRIEF.md"
    json_path = root / "PROJECT_BUILD_BRIEF.json"
    atomic_write_text(md_path, render_project_build_brief_markdown(brief))
    atomic_write_json(json_path, brief.to_dict(), ensure_ascii=False)
    return md_path, json_path


def _infer_domain(low: str, artifact_type: str) -> str:
    domains = [
        ("stock_trading", ["stock", "trading", "portfolio", "shares", "ticker", "buy", "sell"]),
        ("education", ["quiz", "flashcard", "study", "learn", "student", "lesson"]),
        ("science", ["science", "chemistry", "physics", "biology", "pfas", "lab", "experiment"]),
        ("math", ["math", "calculator", "equation", "graph", "geometry", "statistics"]),
        ("project_management", ["task", "todo", "kanban", "deadline", "priority", "planner"]),
        ("data_dashboard", ["dashboard", "chart", "analytics", "visualise", "visualize", "data"]),
        ("file_automation", ["file organiser", "file organizer", "organise files", "organize files", "rename files"]),
        ("game", ["game", "snake", "pong", "platformer", "rpg"]),
        ("communication", ["cover letter", "email", "resume", "cv", "rewrite"]),
        ("java", ["java", "javac", "swing"]),
        ("typescript", ["typescript", "ts-node", "tsx", "ts cli"]),
        ("python", ["python", "script", "automation", "csv", "parse"]),
        ("node_cli", ["node", "npm", "javascript cli", "command line tool"]),
        ("api_service", ["fastapi", "api server", "backend", "endpoint", "uvicorn"]),
        ("powershell", ["powershell", "ps1"]),
        ("batch", ["batch file", "windows batch", ".bat", "cmd script"]),
        ("documentation", ["markdown", "readme", "documentation", "docs"]),
        ("configuration", ["json config", "json schema", "config file", "configuration file", "settings file"]),
    ]
    for domain, tokens in domains:
        if any(t in low for t in tokens):
            return domain
    return artifact_type.replace("_app", "") if artifact_type != "generic_project" else "general_software"


def _infer_audience(low: str) -> str:
    match = re.search(r"\bfor\s+([a-z0-9 ,+\-/]{3,80})", low)
    if match:
        phrase = re.split(r"\bwith\b|\bthat\b|\band\b", match.group(1))[0].strip(" ,.-")
        if phrase:
            return phrase[:80]
    if "student" in low:
        return "students"
    if "developer" in low or "coding" in low:
        return "developers"
    return "general local user"


def _feature_phrases(text: str) -> list[str]:
    low = text.lower()
    chunks: list[str] = []
    for marker in ["with", "include", "including", "has", "have", "that can"]:
        idx = low.find(marker)
        if idx >= 0:
            chunks.append(text[idx + len(marker):])
    if not chunks:
        return []
    features: list[str] = []
    for chunk in chunks[:2]:
        for part in re.split(r",|;|\band\b|\bplus\b", chunk):
            words = re.findall(r"[A-Za-z0-9_+\-/]+", part)
            words = [w for w in words if w.lower() not in {"a", "an", "the", "to", "for", "it", "also", "please"}]
            if 1 <= len(words) <= 8:
                phrase = " ".join(words).strip()
                if len(phrase) >= 3:
                    features.append(phrase)
    return _dedupe(features)[:10]


def _base_functional_requirements(low: str, artifact_type: str, domain: str) -> list[str]:
    if artifact_type == "calculator":
        return ["Enter numbers by button and keyboard", "Perform add/subtract/multiply/divide", "Show live expression and final result", "Clear/reset and backspace", "Handle decimal points and divide-by-zero gracefully"]
    if artifact_type == "todo_app":
        return ["Create tasks", "Edit task text", "Mark tasks complete", "Delete tasks", "Filter tasks by status", "Persist task state locally"]
    if artifact_type in {"browser_game", "snake_game", "html_css_js_game"}:
        return ["Implement a real game loop", "Add player controls", "Show score/progress", "Implement collision or gameplay interactions", "Provide restart/end state", "Show instructions"]
    if artifact_type in {"python_cli_script", "python_desktop_app"}:
        return ["Implement the requested workflow in runnable Python", "Provide clear input/output handling", "Handle invalid inputs and file/path errors", "Include accurate README run and verification commands"]
    if artifact_type == "java_cli_or_desktop_app":
        return ["Implement runnable Java source", "Use a public class matching the filename", "Provide clear console or desktop interactions", "Document javac/java commands"]
    if artifact_type == "typescript_cli_tool":
        return ["Implement a TypeScript command-line entrypoint", "Use explicit types for inputs and outputs", "Keep package.json and tsconfig.json accurate", "Document build, typecheck and run steps"]
    if artifact_type == "node_cli_tool":
        return ["Implement a Node.js command-line entrypoint", "Parse command arguments or stdin clearly", "Handle invalid input", "Keep package.json scripts accurate"]
    if artifact_type == "powershell_automation_script":
        return ["Implement a runnable PowerShell script", "Default risky operations to dry-run or -WhatIf", "Validate input paths", "Document safe example commands"]
    if artifact_type == "batch_script":
        return ["Implement a runnable Windows batch file", "Use @echo off and setlocal", "Quote user paths", "Show safe usage/help output before risky actions"]
    if artifact_type == "markdown_document":
        return ["Write the requested Markdown document", "Use clear headings and examples", "Cover the user's requested sections", "Avoid claiming uncreated runnable code"]
    if artifact_type == "json_config":
        return ["Create valid JSON configuration", "Use clear setting names and safe defaults", "Use placeholders for secrets", "Document each setting in README.md"]
    if artifact_type == "python_fastapi_service":
        return ["Implement a FastAPI app object", "Provide typed routes", "Return sample JSON responses", "Document install and localhost run steps"]
    if domain == "stock_trading":
        return ["Manage a watchlist of ticker symbols", "Simulate buy and sell transactions", "Track cash balance, holdings and portfolio value", "Show profit/loss and transaction history", "Persist data locally", "Export portfolio data as JSON"]
    if domain == "data_dashboard":
        return ["Display summary cards", "Render charts or grouped data views", "Filter/search the data", "Provide seeded sample data", "Show empty/error states"]
    if domain == "file_automation":
        return ["Use safe dry-run mode first", "Explain file movement rules", "Operate only on a user-selected folder", "Provide logs of proposed actions", "Include verification with temporary fixture files"]
    return ["Implement the main workflow described by the user", "Provide meaningful sample data or starter content", "Include visible controls for the primary actions", "Show success/error/empty states", "Include accurate README and run instructions"]


def _data_model_for(low: str, artifact_type: str, domain: str) -> list[str]:
    if artifact_type == "calculator":
        return ["current expression", "display value", "last result", "operator/error state"]
    if artifact_type == "todo_app":
        return ["task id", "task title", "completed flag", "priority/status", "created/updated timestamp"]
    if artifact_type in {"browser_game", "snake_game", "html_css_js_game"}:
        return ["player position", "velocity/direction", "score", "level/game state", "obstacles or targets", "timer/restart state"]
    if artifact_type in {"python_cli_script", "node_cli_tool", "typescript_cli_tool", "java_cli_or_desktop_app", "powershell_automation_script", "batch_script"}:
        return ["command/options", "input values", "result/output", "error state", "log or summary"]
    if artifact_type == "markdown_document":
        return ["document title", "section headings", "examples", "verification notes"]
    if artifact_type == "json_config":
        return ["setting key", "default value", "description in README", "secret placeholder if needed"]
    if artifact_type == "python_desktop_app":
        return ["window state", "input fields", "result/output", "error state"]
    if artifact_type == "python_fastapi_service":
        return ["request path", "query/body input", "response payload", "validation error", "health state"]
    if domain == "stock_trading":
        return ["cash balance", "ticker symbol", "share quantity", "average cost", "current simulated price", "transaction record", "profit/loss"]
    if domain == "data_dashboard":
        return ["record id", "category", "value", "date/time", "filter state", "selected chart/view"]
    return ["domain item id", "title/name", "status", "notes/details", "created/updated timestamp"]


def _ui_states_for(low: str, artifact_type: str, domain: str) -> list[str]:
    base = ["initial loaded state", "empty state", "valid input state", "invalid input/error state", "saved/exported state"]
    if artifact_type in {"browser_game", "snake_game", "html_css_js_game"}:
        return ["start screen", "playing", "paused if supported", "game over", "restart"]
    if artifact_type in {"python_cli_script", "node_cli_tool", "typescript_cli_tool", "java_cli_or_desktop_app", "powershell_automation_script", "batch_script"}:
        return ["help/usage output", "valid run", "invalid input error", "success output"]
    if artifact_type == "markdown_document":
        return ["document opened", "requested sections present", "examples readable", "verification notes present"]
    if artifact_type == "json_config":
        return ["config file parses", "README explains settings", "secret placeholders are not real credentials"]
    if artifact_type == "python_fastapi_service":
        return ["health response", "valid endpoint response", "invalid request response", "README curl/browser example"]
    if artifact_type == "python_desktop_app":
        return ["window opened", "valid input state", "invalid input message", "completed action"]
    if domain == "stock_trading":
        return ["watchlist", "trade form", "portfolio summary", "transaction history", "export confirmation"]
    return base


def _edge_cases_for(low: str, artifact_type: str, domain: str) -> list[str]:
    edges = ["missing input", "invalid input", "empty data", "local saved data is absent or corrupt"]
    if artifact_type == "calculator":
        edges.extend(["divide by zero", "multiple decimals", "operator pressed twice"])
    if artifact_type in {"python_cli_script", "node_cli_tool", "typescript_cli_tool", "java_cli_or_desktop_app", "powershell_automation_script", "batch_script"}:
        edges.extend(["missing command argument", "invalid command argument", "file/path not found", "permission denied"] )
    if artifact_type == "markdown_document":
        edges.extend(["missing requested section", "unclear example", "claiming an implementation that was not produced"])
    if artifact_type == "json_config":
        edges.extend(["invalid JSON syntax", "missing required setting", "accidental real secret value"])
    if artifact_type == "python_fastapi_service":
        edges.extend(["unknown route", "invalid query/body", "server already running"] )
    if domain == "stock_trading":
        edges.extend(["insufficient cash", "selling more shares than owned", "unknown ticker", "zero/negative quantity"])
    if artifact_type in {"browser_game", "snake_game", "html_css_js_game"}:
        edges.extend(["collision at boundary", "restart after game over", "rapid key presses"])
    return _dedupe(edges)


def _suggested_files_for(artifact_type: str, domain: str) -> list[str]:
    if domain == "file_automation":
        return ["file_organiser.py", "README.md", "tests/test_file_organiser.py"]
    if artifact_type == "python_cli_script":
        return ["main.py", "README.md", "tests/test_main.py"]
    if artifact_type == "python_desktop_app":
        return ["app.py", "README.md"]
    if artifact_type == "python_fastapi_service":
        return ["main.py", "requirements.txt", "README.md"]
    if artifact_type == "java_cli_or_desktop_app":
        return ["Main.java", "README.md"]
    if artifact_type == "typescript_cli_tool":
        return ["package.json", "tsconfig.json", "src/index.ts", "README.md"]
    if artifact_type == "node_cli_tool":
        return ["index.js", "package.json", "README.md"]
    if artifact_type == "powershell_automation_script":
        return ["script.ps1", "README.md"]
    if artifact_type == "batch_script":
        return ["script.bat", "README.md"]
    if artifact_type == "markdown_document":
        return ["README.md"]
    if artifact_type == "json_config":
        return ["config.json", "README.md"]
    if artifact_type in {"calculator", "todo_app", "browser_game", "snake_game", "generic_project", "html_css_js_app", "html_css_js_game"}:
        return ["index.html", "style.css", "app.js", "README.md"]
    return ["main.py", "README.md"]


def _extra_acceptance_for(low: str, artifact_type: str, domain: str, features: list[str]) -> list[str]:
    checks = []
    for feature in features:
        checks.append(f"Requested feature is visible and functional in code/UI: {feature}")
    if domain == "stock_trading":
        checks.extend(["buy/sell changes portfolio state", "invalid trades are rejected", "profit/loss updates after simulated prices change", "transaction history and export work"])
    if domain == "data_dashboard":
        checks.extend(["filters change displayed data", "charts or grouped summaries are based on real data arrays", "empty search has a clear message"])
    return checks


def _verification_commands_for(artifact_type: str, domain: str) -> list[str]:
    if domain == "file_automation":
        return ["py -3 -m py_compile file_organiser.py", "py -3 -m pytest -q"]
    if artifact_type == "python_cli_script":
        return ["py -3 -m py_compile main.py"]
    if artifact_type == "python_desktop_app":
        return ["py -3 -m py_compile app.py"]
    if artifact_type == "python_fastapi_service":
        return ["py -3 -m py_compile main.py"]
    if artifact_type == "java_cli_or_desktop_app":
        return ["javac Main.java"]
    if artifact_type == "typescript_cli_tool":
        return ["node -e \"const fs=require('fs'); for (const p of ['package.json','tsconfig.json','src/index.ts']) if (!fs.existsSync(p)) throw new Error('missing '+p); console.log('typescript project files ok')\""]
    if artifact_type == "node_cli_tool":
        return ["node --check index.js"]
    if artifact_type == "powershell_automation_script":
        return ["powershell -NoProfile -Command \"$null = [scriptblock]::Create((Get-Content .\\script.ps1 -Raw)); 'syntax ok'\""]
    if artifact_type == "batch_script":
        return ["powershell -NoProfile -Command \"$p=Get-Content .\\script.bat -Raw; if($p -match '@echo off'){'batch script present'}else{throw 'missing @echo off'}\""]
    if artifact_type == "markdown_document":
        return ["py -3 -c \"from pathlib import Path; assert Path('README.md').read_text(encoding='utf-8').strip(); print('markdown ok')\""]
    if artifact_type == "json_config":
        return ["py -3 -c \"import json; from pathlib import Path; json.loads(Path('config.json').read_text(encoding='utf-8')); print('json ok')\""]
    return ["py -3 -c \"from pathlib import Path; assert Path('index.html').exists(); assert Path('app.js').exists(); print('basic files ok')\"", "open index.html and test the primary workflow manually"]


def _assumptions_for(low: str, artifact_type: str, domain: str) -> list[str]:
    assumptions = []
    if domain == "stock_trading":
        assumptions.append("Use simulated prices because no live market-data API was supplied.")
    if artifact_type in {"browser_game", "snake_game", "html_css_js_game"}:
        assumptions.append("Use a dependency-free browser game unless the user requested a framework.")
    if artifact_type in {"html_css_js_app", "html_css_js_game", "browser_game", "snake_game", "calculator", "todo_app"} and "api" not in low and "server" not in low:
        assumptions.append("Prefer a dependency-free local browser app for visual/UI tasks.")
    elif artifact_type not in {"html_css_js_app", "html_css_js_game", "browser_game", "snake_game", "calculator", "todo_app"}:
        assumptions.append("Prefer the selected non-browser runtime because it is more efficient for this prompt than HTML.")
    if artifact_type == "typescript_cli_tool":
        assumptions.append("TypeScript typechecking may require npm install after explicit package approval.")
    if artifact_type == "json_config":
        assumptions.append("Use example placeholders instead of real secrets or credentials.")
    return assumptions


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = re.sub(r"\s+", " ", str(item).strip().lower())
        if key and key not in seen:
            seen.add(key)
            out.append(str(item).strip())
    return out
