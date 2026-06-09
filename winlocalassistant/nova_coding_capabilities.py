from __future__ import annotations

"""Nova coding capability planning and local-model tuning helpers.

The helpers in this module are deterministic and read-only. They make Nova's
coding path less HTML-biased by selecting the cheapest suitable artifact type,
entrypoint, run command, and verifier before the local model writes files.
"""

import os
import platform
import re
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class CodingExecutionPlan:
    goal: str
    artifact_type: str
    language: str
    why: str
    expected_files: list[str] = field(default_factory=list)
    main_file: str = "README.md"
    run_command: str = ""
    verify_command: str = ""
    optional_verify_commands: list[str] = field(default_factory=list)
    dependency_policy: str = "dependency-free unless explicitly requested"
    prompt_rules: list[str] = field(default_factory=list)
    safety_notes: list[str] = field(default_factory=list)
    efficiency_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def plan_coding_execution(goal: str) -> dict[str, Any]:
    """Return the most efficient local project shape for a coding request."""
    text = (goal or "").strip()
    low = text.lower()

    def has_any(*tokens: str) -> bool:
        return any(token in low for token in tokens)

    one_file_requested = has_any("one file", "single file", "just one file", "only one file") or bool(re.search(r"\bone\s+[a-z0-9_ -]{0,40}\s*file\b", low))

    if one_file_requested and has_any("python", ".py", "script") and not has_any("website", "browser", "html", "game"):
        plan = CodingExecutionPlan(
            goal=text,
            artifact_type="python_cli_script",
            language="Python",
            why="The prompt explicitly asks for one Python file, so Nova must not create a scaffold or HTML template.",
            expected_files=["script.py"],
            main_file="script.py",
            run_command="py -3 .\\script.py",
            verify_command="py -3 -m py_compile script.py",
            optional_verify_commands=[],
            dependency_policy="Use the Python standard library unless the user explicitly asks for packages.",
            prompt_rules=[
                "Create exactly one Python source file named script.py.",
                "Do not add README.md, tests, HTML, CSS, or JS for this one-file request.",
                "Keep the script directly runnable and include helpful argparse/help text only if useful.",
            ],
        )
    elif has_any("typescript", "ts-node", "tsx", "ts cli", "typescript cli"):
        plan = CodingExecutionPlan(
            goal=text,
            artifact_type="typescript_cli_tool",
            language="TypeScript/Node.js",
            why="The prompt explicitly asks for TypeScript, so Nova should create TypeScript sources and supporting Node project metadata instead of plain browser files.",
            expected_files=["package.json", "tsconfig.json", "src/index.ts", "README.md"],
            main_file="src/index.ts",
            run_command="npm run build && node dist/index.js",
            verify_command="node -e \"const fs=require('fs'); for (const p of ['package.json','tsconfig.json','src/index.ts']) if (!fs.existsSync(p)) throw new Error('missing '+p); console.log('typescript project files ok')\"",
            optional_verify_commands=["npm install", "npm run typecheck", "npm test"],
            dependency_policy="Do not run npm install automatically; TypeScript tooling should be installed only with explicit user approval.",
            prompt_rules=[
                "Create TypeScript source under src/ with explicit types for inputs and outputs.",
                "Keep package.json scripts accurate for build, typecheck and start.",
                "Avoid browser DOM code unless the user requested a browser UI.",
            ],
            safety_notes=["Treat npm install as an explicit package-install action requiring user approval."],
        )
    elif has_any("batch file", "windows batch", ".bat", "cmd script", "batch script"):
        plan = CodingExecutionPlan(
            goal=text,
            artifact_type="batch_script",
            language="Windows batch",
            why="The prompt asks for a Windows batch/cmd surface, so a .bat file is the most direct local artifact.",
            expected_files=["script.bat", "README.md"],
            main_file="script.bat",
            run_command="cmd /c script.bat",
            verify_command="powershell -NoProfile -Command \"$p=Get-Content .\\script.bat -Raw; if($p -match '@echo off'){'batch script present'}else{throw 'missing @echo off'}\"",
            optional_verify_commands=["cmd /c script.bat --help"],
            dependency_policy="Use built-in cmd.exe commands only unless the user explicitly requests external tools.",
            prompt_rules=[
                "Start with @echo off and use setlocal for predictable environment handling.",
                "Quote paths and show safe usage/help output.",
                "Use dry-run prompts before file-changing actions.",
            ],
            safety_notes=["Never test destructive batch actions on real user files; use temp fixtures and dry-run mode."],
        )
    elif has_any("markdown", "readme", "documentation", "docs") and not has_any("website", "browser", "html", "web app"):
        plan = CodingExecutionPlan(
            goal=text,
            artifact_type="markdown_document",
            language="Markdown",
            why="The request is documentation-shaped, so Nova should produce a clear Markdown document instead of inventing an app.",
            expected_files=["README.md"],
            main_file="README.md",
            run_command="",
            verify_command="py -3 -c \"from pathlib import Path; text=Path('README.md').read_text(encoding='utf-8'); assert text.strip(); print('markdown ok')\"",
            optional_verify_commands=[],
            dependency_policy="No dependencies required for Markdown output.",
            prompt_rules=[
                "Write the requested document directly in Markdown.",
                "Use headings, concise steps, examples and verification notes where useful.",
                "Do not claim runnable code exists unless code files are also produced.",
            ],
        )
    elif has_any("json config", "json schema", "config file", "configuration file", "settings file", "settings json") or (has_any("json") and not has_any("parse", "parser", "python", "script", "api", "browser", "website", "game")):
        plan = CodingExecutionPlan(
            goal=text,
            artifact_type="json_config",
            language="JSON/config",
            why="The request is for structured configuration/data, so Nova should emit valid JSON plus usage notes rather than a runnable app.",
            expected_files=["config.json", "README.md"],
            main_file="config.json",
            run_command="",
            verify_command="py -3 -c \"import json; from pathlib import Path; json.loads(Path('config.json').read_text(encoding='utf-8')); print('json ok')\"",
            optional_verify_commands=[],
            dependency_policy="No package installs required for JSON/config files.",
            prompt_rules=[
                "Keep JSON strictly valid with double-quoted keys and no comments.",
                "Document each setting and safe defaults in README.md.",
                "Use placeholder values for secrets and mark them clearly.",
            ],
            safety_notes=["Never include real secrets, keys or tokens in generated config files."],
        )
    elif has_any("java", "javac", "swing"):
        plan = CodingExecutionPlan(
            goal=text,
            artifact_type="java_cli_or_desktop_app",
            language="Java",
            why="The prompt explicitly asks for Java or Java runtime concepts, so Nova should not convert it into browser files.",
            expected_files=["Main.java", "README.md"],
            main_file="Main.java",
            run_command="javac Main.java && java Main",
            verify_command="javac Main.java",
            optional_verify_commands=["java Main"],
            dependency_policy="Use only the Java standard library unless the user explicitly requests a dependency or framework.",
            prompt_rules=[
                "Return complete Java source with a public class matching the file name.",
                "Use console I/O for CLI tasks or Swing only when a desktop GUI is explicitly requested.",
                "Document exact javac/java commands in README.md.",
            ],
            efficiency_notes=["A single-file Java program is fastest to compile, inspect and run for small tasks."],
        )
    elif has_any("fastapi", "rest api", "api server", "backend", "endpoint", "uvicorn"):
        plan = CodingExecutionPlan(
            goal=text,
            artifact_type="python_fastapi_service",
            language="Python",
            why="The request is server/API shaped, so a small FastAPI project is more appropriate than static HTML.",
            expected_files=["main.py", "requirements.txt", "README.md"],
            main_file="main.py",
            run_command="py -3 -m uvicorn main:app --reload",
            verify_command="py -3 -m py_compile main.py",
            optional_verify_commands=["py -3 -m pip install -r requirements.txt", "py -3 -m uvicorn main:app --reload"],
            dependency_policy="Requires explicit dependency install approval for FastAPI/uvicorn if not already installed.",
            prompt_rules=[
                "Create a minimal FastAPI app with typed routes and clear sample responses.",
                "Keep external services mocked unless API credentials were supplied.",
                "README.md must separate install, run and smoke-test steps.",
            ],
            safety_notes=["Do not silently expose network services beyond localhost."],
            efficiency_notes=["Use py_compile first; only start the server when the user explicitly asks to run it."],
        )
    elif has_any("powershell", "ps1"):
        plan = CodingExecutionPlan(
            goal=text,
            artifact_type="powershell_automation_script",
            language="PowerShell",
            why="The prompt asks for a Windows/PowerShell automation surface, so a .ps1 script is the direct fit.",
            expected_files=["script.ps1", "README.md"],
            main_file="script.ps1",
            run_command="powershell -ExecutionPolicy Bypass -File .\\script.ps1",
            verify_command="powershell -NoProfile -Command \"$null = [scriptblock]::Create((Get-Content .\\script.ps1 -Raw)); 'syntax ok'\"",
            optional_verify_commands=["powershell -ExecutionPolicy Bypass -File .\\script.ps1 -WhatIf"],
            dependency_policy="Use built-in PowerShell cmdlets and include -WhatIf/dry-run behaviour for file changes.",
            prompt_rules=[
                "Include CmdletBinding/Switch parameters where useful.",
                "Dangerous file operations must support -WhatIf or dry-run first.",
                "README.md must show a safe example command.",
            ],
            safety_notes=["Never test on real user files; create temporary fixtures for verification."],
        )
    elif has_any("node", "npm", "javascript cli", "js cli", "command line tool") and not has_any("website", "html", "browser"):
        plan = CodingExecutionPlan(
            goal=text,
            artifact_type="node_cli_tool",
            language="JavaScript/Node.js",
            why="The request is CLI/tool shaped and mentions Node/JavaScript, so a Node entrypoint is more efficient than a web page.",
            expected_files=["index.js", "package.json", "README.md"],
            main_file="index.js",
            run_command="node index.js",
            verify_command="node --check index.js",
            optional_verify_commands=["npm test"],
            dependency_policy="No npm packages unless the prompt explicitly needs them.",
            prompt_rules=[
                "Use process.argv or readline for inputs.",
                "Keep package.json scripts accurate.",
                "Avoid browser DOM code unless the user requested a browser UI.",
            ],
        )
    elif has_any("python", "pyqt", "tkinter", "script", "automation", "csv", "json file", "file organiser", "file organizer", "rename files", "parse", "scrape local", "convert files"):
        desktop = has_any("tkinter", "desktop app", "gui app", "pyqt")
        main_file = "app.py" if desktop else "main.py"
        plan = CodingExecutionPlan(
            goal=text,
            artifact_type="python_desktop_app" if desktop else "python_cli_script",
            language="Python",
            why="The request is script/automation/data-processing shaped, where Python is the simplest local runnable format.",
            expected_files=[main_file, "README.md"] + (["tests/test_main.py"] if not desktop else []),
            main_file=main_file,
            run_command=f"py -3 .\\{main_file}",
            verify_command=f"py -3 -m py_compile {main_file}",
            optional_verify_commands=["py -3 -m pytest -q"] if not desktop else [],
            dependency_policy="Use the Python standard library first; require approval before pip installs.",
            prompt_rules=[
                "Provide argparse or clear function boundaries for CLI tools.",
                "Use deterministic sample inputs or temp fixtures for verification.",
                "Handle file/path errors clearly and safely.",
            ],
            safety_notes=["For file automation, default to dry-run and temporary fixtures during tests."],
            efficiency_notes=["Python scripts compile quickly and are better than HTML for file, data and automation tasks."],
        )
    elif has_any("game", "website", "html", "browser", "dashboard", "visual", "canvas", "calculator", "todo", "localstorage", "chart", "ui"):
        kind = "html_css_js_game" if has_any("game", "canvas", "snake", "pong", "platformer") else "html_css_js_app"
        plan = CodingExecutionPlan(
            goal=text,
            artifact_type=kind,
            language="HTML/CSS/JavaScript",
            why="The request asks for a visual/browser UI, so static browser files remain the most efficient no-install format.",
            expected_files=["index.html", "style.css", "app.js", "README.md"],
            main_file="index.html",
            run_command="start .\\index.html",
            verify_command="node --check app.js",
            optional_verify_commands=["open index.html and test the primary workflow manually"],
            dependency_policy="Dependency-free browser app unless the user explicitly requests a framework.",
            prompt_rules=[
                "Wire real DOM/event behaviour, not a static mock-up.",
                "Keep CSS/JS references local and matching actual file names.",
                "Document manual browser smoke steps in README.md.",
            ],
        )
    else:
        plan = CodingExecutionPlan(
            goal=text,
            artifact_type="python_cli_script",
            language="Python",
            why="The prompt does not require a visual browser UI; defaulting to a small Python CLI keeps output runnable, testable and efficient.",
            expected_files=["main.py", "README.md"],
            main_file="main.py",
            run_command="py -3 .\\main.py",
            verify_command="py -3 -m py_compile main.py",
            optional_verify_commands=["py -3 -m pytest -q if tests are generated"],
            dependency_policy="Dependency-free Python unless the user asks for UI/web/API packages.",
            prompt_rules=[
                "Ask the model for the smallest runnable source layout that satisfies the prompt.",
                "Do not create HTML files unless a visual/browser interface is useful or requested.",
                "README.md must include exact run and verify commands.",
            ],
        )

    return plan.to_dict()


def render_coding_execution_plan(plan: dict[str, Any]) -> str:
    lines = [
        "# Nova Coding Execution Plan",
        "",
        f"Goal: {plan.get('goal','')}",
        f"Artifact type: `{plan.get('artifact_type','')}`",
        f"Language/runtime: **{plan.get('language','')}**",
        f"Why: {plan.get('why','')}",
        "",
        "## Files",
    ]
    lines.extend(f"- `{f}`" for f in plan.get("expected_files", []) or [])
    lines.extend([
        "",
        "## Commands",
        f"- Main file: `{plan.get('main_file','')}`",
        f"- Run: `{plan.get('run_command','')}`",
        f"- Verify: `{plan.get('verify_command','')}`",
    ])
    optional = plan.get("optional_verify_commands") or []
    if optional:
        lines.extend(["", "## Optional checks"])
        lines.extend(f"- `{cmd}`" for cmd in optional)
    lines.extend(["", "## Prompt rules"])
    lines.extend(f"- {item}" for item in plan.get("prompt_rules", []) or [])
    notes = list(plan.get("safety_notes", []) or []) + list(plan.get("efficiency_notes", []) or [])
    if notes:
        lines.extend(["", "## Notes"])
        lines.extend(f"- {item}" for item in notes)
    return "\n".join(lines) + "\n"


def build_coding_capability_audit(repo_root: Path | str = ".") -> dict[str, Any]:
    root = Path(repo_root)
    files = {
        "project_brief": root / "winlocalassistant" / "project_brief.py",
        "tools": root / "winlocalassistant" / "tools.py",
        "runtime_probe": root / "winlocalassistant" / "project_runtime_probe.py",
        "project_types": root / "winlocalassistant" / "project_type_registry.py",
    }
    contents = {name: _read(path) for name, path in files.items()}
    checks = [
        _check("coding_plan_module", (root / "winlocalassistant" / "nova_coding_capabilities.py").exists(), "Deterministic multi-language coding planner exists."),
        _check("dynamic_project_brief", "plan_coding_execution" in contents["project_brief"], "Project brief uses the coding planner instead of always suggesting browser files."),
        _check("prompt_not_html_only", "Do not force everything into HTML" in contents["tools"] and "CODING EXECUTION PLAN" in contents["tools"], "Local-model prompt includes an explicit multi-language coding plan."),
        _check("python_verify", "py_compile" in contents["tools"], "Verifier can check Python syntax."),
        _check("node_verify", "node --check" in contents["tools"] or "node_syntax" in contents["tools"], "Verifier can check JavaScript syntax."),
        _check("java_verify", "javac" in contents["tools"], "Verifier can check Java when javac exists."),
        _check("powershell_verify", "scriptblock" in contents["tools"].lower() or "powershell" in contents["tools"].lower(), "Verifier can sanity-check PowerShell scripts."),
        _check("runtime_probe_generic", "has_entrypoint" in contents["runtime_probe"], "Runtime probe has non-browser generic entrypoint checks."),
        _check("project_types_multi_language", "java_cli" in contents["project_types"] and "powershell" in contents["project_types"], "Project type registry recognises non-browser project types."),
    ]
    concerns = []
    if '"main_file": "index.html"' in contents["tools"]:
        concerns.append("Some schema examples still mention index.html for readability, but the coding execution plan now supplies the actual expected files and commands.")
    if not any(c["name"] == "java_verify" and c["ok"] for c in checks):
        concerns.append("Java outputs may compile only when javac is installed on the user machine.")
    return {
        "ok": all(c["ok"] for c in checks),
        "checks": checks,
        "concerns": concerns,
        "recommendations": [
            "Use /coding-plan GOAL before generation when the task could be CLI, Java, Python, API or browser.",
            "Keep verification command in PROJECT_MANIFEST.json aligned with the selected runtime.",
            "Prefer deterministic syntax checks before asking the local model for another repair pass.",
        ],
    }


def render_coding_capability_audit(payload: dict[str, Any]) -> str:
    lines = ["# Nova Coding Capability Audit", "", f"Overall: **{'PASS' if payload.get('ok') else 'REVIEW'}**", "", "## Checks"]
    for check in payload.get("checks", []):
        mark = "✅" if check.get("ok") else "⚠️"
        lines.append(f"- {mark} **{check.get('name','')}** — {check.get('detail','')}")
    concerns = payload.get("concerns") or []
    lines.extend(["", "## Areas of concern"])
    lines.extend(f"- {item}" for item in concerns) if concerns else lines.append("- none")
    lines.extend(["", "## Recommended usage"])
    lines.extend(f"- {item}" for item in payload.get("recommendations", []) or [])
    return "\n".join(lines) + "\n"


def build_local_model_performance_plan(goal: str = "", hardware_hint: str = "") -> dict[str, Any]:
    """Build a practical local-model strategy for common Nova situations."""
    low = (goal or "").lower()
    hint = (hardware_hint or "").strip()
    task = _task_kind(low)
    has_gpu_hint = bool(re.search(r"\b(rtx|gtx|nvidia|amd|cuda|gpu|vram|gb)\b", hint.lower()))
    likely_small_vram = bool(re.search(r"\b(4gb|4 gb|6gb|6 gb|gtx 1650)\b", hint.lower()))
    profile = {
        "chat": {"model_role": "small general instruct", "num_ctx": 2048, "temperature": 0.5, "num_predict": 512},
        "coding": {"model_role": "coder model", "num_ctx": 4096, "temperature": 0.15, "num_predict": 1400},
        "long_context": {"model_role": "context-aware model with retrieval trimming", "num_ctx": 8192, "temperature": 0.25, "num_predict": 900},
        "vision": {"model_role": "vision-capable model", "num_ctx": 2048, "temperature": 0.2, "num_predict": 700},
        "tooling": {"model_role": "small planner + deterministic tools", "num_ctx": 3072, "temperature": 0.2, "num_predict": 700},
    }[task]
    if likely_small_vram:
        profile = {**profile, "num_ctx": min(int(profile["num_ctx"]), 4096), "quantization": "Q4/Q5 small coder or instruct model", "gpu_strategy": "fit model plus KV cache in VRAM; reduce context before increasing model size"}
    elif has_gpu_hint:
        profile = {**profile, "quantization": "Q5/Q6 for quality if VRAM allows, Q4 for speed", "gpu_strategy": "offload as many layers as fit, then benchmark tokens/sec and failures"}
    else:
        profile = {**profile, "quantization": "Q4/Q5 for CPU-friendly local use", "gpu_strategy": "assume CPU or unknown GPU; use smaller model and tighter context"}

    strategies = [
        "Route coding tasks to coder models and keep chat/summary tasks on smaller faster instruct models.",
        "Trim context with project/file packs instead of pasting the whole repo into every prompt.",
        "Use a generate -> deterministic verify -> targeted repair loop rather than regenerating the whole project after each error.",
        "Keep stable system prompts and reusable project briefs compact so local runtimes can benefit from prompt/KV reuse where supported.",
        "Use lower temperature for code and validation, higher only for brainstorming.",
        "Record model, context, timeout, tokens/sec and validation failures so Nova can choose the fastest model that still passes tests.",
    ]
    settings = {
        "suggested_ollama_options": {
            "num_ctx": profile["num_ctx"],
            "temperature": profile["temperature"],
            "num_predict": profile["num_predict"],
            "keep_alive": "10m for repeated project work; shorter for memory pressure",
        },
        "task_kind": task,
        "model_role": profile["model_role"],
        "quantization": profile["quantization"],
        "gpu_strategy": profile["gpu_strategy"],
    }
    return {"goal": goal, "hardware_hint": hint, "profile": settings, "strategies": strategies, "sanity_checks": [
        "Measure time-to-first-token and tokens/sec before and after changing model/context.",
        "Confirm generated files pass syntax checks before asking the model to self-review.",
        "If output quality drops, reduce context noise before increasing temperature or switching to a larger model.",
    ]}


def render_local_model_performance_plan(payload: dict[str, Any]) -> str:
    profile = payload.get("profile", {})
    options = profile.get("suggested_ollama_options", {}) if isinstance(profile, dict) else {}
    lines = [
        "# Nova Local Model Performance Plan",
        "",
        f"Goal/task: {payload.get('goal') or 'general Nova use'}",
        f"Task kind: `{profile.get('task_kind','')}`",
        f"Model role: **{profile.get('model_role','')}**",
        f"Quantization: {profile.get('quantization','')}",
        f"GPU/context strategy: {profile.get('gpu_strategy','')}",
        "",
        "## Suggested runtime options",
    ]
    for key, value in options.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Strategies"])
    lines.extend(f"- {item}" for item in payload.get("strategies", []) or [])
    lines.extend(["", "## Sanity checks"])
    lines.extend(f"- {item}" for item in payload.get("sanity_checks", []) or [])
    return "\n".join(lines) + "\n"


def verifier_for_file(path: str) -> str:
    suffix = Path(path).suffix.lower()
    name = Path(path).name
    if suffix == ".py":
        return f"py -3 -m py_compile {name}"
    if suffix == ".js":
        return f"node --check {name}"
    if suffix == ".java":
        return f"javac {name}"
    if suffix == ".ts":
        return "node -e \"const fs=require('fs'); if(!fs.existsSync('tsconfig.json')) throw new Error('missing tsconfig.json'); console.log('typescript file present')\""
    if suffix == ".ps1":
        return f"powershell -NoProfile -Command \"$null = [scriptblock]::Create((Get-Content .\\{name} -Raw)); 'syntax ok'\""
    if suffix == ".bat":
        return f"powershell -NoProfile -Command \"$p=Get-Content .\\{name} -Raw; if($p -match '@echo off'){{'batch script present'}}else{{throw 'missing @echo off'}}\""
    if suffix == ".json":
        return f"py -3 -c \"import json; from pathlib import Path; json.loads(Path('{name}').read_text(encoding='utf-8')); print('json ok')\""
    if suffix in {".md", ".markdown"}:
        return f"py -3 -c \"from pathlib import Path; assert Path('{name}').read_text(encoding='utf-8').strip(); print('markdown ok')\""
    return ""


def _task_kind(low: str) -> str:
    if any(t in low for t in ["image", "photo", "vision", "screenshot"]):
        return "vision"
    coding_terms = [
        "code", "coding", "python", "java", "javascript", "typescript",
        "node", "npm", "powershell", "batch", "cmd", "script", "cli",
        "command-line", "command line", "bug", "program", "json config",
        "json schema", "config file", "configuration file", "settings file",
        "tsconfig",
    ]
    if any(t in low for t in coding_terms):
        return "coding"
    if any(t in low for t in ["long", "document", "documentation", "docs", "markdown", "readme", "repo", "summarise", "summarize", "many files"]):
        return "long_context"
    if any(t in low for t in ["project", "app"]):
        return "coding"
    if any(t in low for t in ["tool", "agent", "workflow", "autonomous", "command"]):
        return "tooling"
    return "chat"


def _check(name: str, ok: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "detail": detail}


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""
