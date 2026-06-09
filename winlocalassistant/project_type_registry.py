from __future__ import annotations

from typing import Any

PROJECT_TYPES: dict[str, dict[str, Any]] = {
    "html_css_js_game": {"markers": ["game", "score", "controls", "collision", "restart"], "files": ["index.html", "style.css", "app.js", "README.md"]},
    "html_css_js_app": {"markers": ["form", "state", "localStorage", "export"], "files": ["index.html", "style.css", "app.js", "README.md"]},
    "python_cli_script": {"markers": ["argparse", "main", "README"], "files": ["main.py", "README.md"]},
    "python_gui_app": {"markers": ["tkinter", "mainloop"], "files": ["app.py", "README.md"]},
    "fastapi_app": {"markers": ["FastAPI", "uvicorn", "route"], "files": ["main.py", "requirements.txt", "README.md"]},
    "node_cli_tool": {"markers": ["node", "process.argv", "package.json"], "files": ["index.js", "package.json", "README.md"]},
    "typescript_cli_tool": {"markers": ["typescript", "tsconfig", "src/index.ts"], "files": ["package.json", "tsconfig.json", "src/index.ts", "README.md"]},
    "java_cli_app": {"markers": ["javac", "public static void main", "class Main"], "files": ["Main.java", "README.md"]},
    "powershell_script": {"markers": ["PowerShell", "param", "WhatIf"], "files": ["script.ps1", "README.md"]},
    "batch_script": {"markers": ["@echo off", "setlocal", "cmd"], "files": ["script.bat", "README.md"]},
    "markdown_document": {"markers": ["markdown", "headings", "README"], "files": ["README.md"]},
    "json_config": {"markers": ["valid JSON", "settings", "schema"], "files": ["config.json", "README.md"]},
    "mcp_server": {"markers": ["mcp", "tools", "server"], "files": ["server.py", "README.md"]},
    "data_dashboard": {"markers": ["chart", "filter", "table"], "files": ["index.html", "style.css", "app.js", "README.md"]},
    "automation_script": {"markers": ["dry run", "input", "output", "log"], "files": ["main.py", "README.md"]},
}


def infer_project_type(goal: str) -> str:
    low = (goal or "").lower()
    if any(term in low for term in ["typescript", "ts-node", "tsx", "ts cli", "typescript cli"]):
        return "typescript_cli_tool"
    if any(term in low for term in ["java", "javac", "swing"]):
        return "java_cli_app"
    if any(term in low for term in ["powershell", "ps1"]):
        return "powershell_script"
    if any(term in low for term in ["batch file", "windows batch", ".bat", "cmd script", "batch script"]):
        return "batch_script"
    if any(term in low for term in ["markdown", "readme", "documentation", "docs"]) and not any(term in low for term in ["website", "browser", "html", "web app"]):
        return "markdown_document"
    if any(term in low for term in ["json config", "json schema", "config file", "configuration file", "settings file", "settings json"]) or ("json" in low and not any(term in low for term in ["parse", "parser", "python", "script", "api", "browser", "website", "game"])):
        return "json_config"
    if "game" in low:
        return "html_css_js_game"
    if "fastapi" in low or "api" in low or "endpoint" in low:
        return "fastapi_app"
    if "mcp" in low:
        return "mcp_server"
    if any(term in low for term in ["node", "npm", "javascript cli", "command line tool"]):
        return "node_cli_tool"
    if any(term in low for term in ["python", "script", "automation", "csv", "parse", "file organiser", "file organizer"]):
        return "python_cli_script"
    if "dashboard" in low or "chart" in low:
        return "data_dashboard"
    if any(term in low for term in ["website", "html", "browser", "ui", "calculator", "todo"]):
        return "html_css_js_app"
    return "python_cli_script"


def project_type_contract(goal: str) -> dict[str, Any]:
    kind = infer_project_type(goal)
    return {"kind": kind, **PROJECT_TYPES[kind]}
