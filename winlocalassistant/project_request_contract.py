from __future__ import annotations

"""Strict request-contract helpers for Nova project generation.

The contract is deliberately deterministic and conservative.  It converts the
user's wording into the minimum file/runtime shape Nova is allowed to generate,
so one-file/script/PowerShell/Nova-edit prompts do not silently become generic
HTML scaffolds.
"""

import re
from typing import Any

from .creation_intent import analyze_creation_request
from .nova_coding_capabilities import plan_coding_execution


def _has_any(low: str, *needles: str) -> bool:
    return any(n in low for n in needles)


def _detect_language(low: str, coding_plan: dict[str, Any]) -> str:
    language = str(coding_plan.get("language") or "").strip()
    if _has_any(low, "powershell", ".ps1", "ps1"):
        return "PowerShell"
    if _has_any(low, "python", ".py", "py script"):
        return "Python"
    if _has_any(low, "html", "css", "javascript", "browser", "website", "web app", "game"):
        return "HTML/CSS/JavaScript"
    return language or "unspecified"


def build_request_contract(user_text: str) -> dict[str, Any]:
    """Return a strict generation contract from the user's original request."""
    text = (user_text or "").strip()
    low = text.lower()
    one_file = _has_any(low, "one file", "single file", "just one file", "only one file") or bool(re.search(r"\bone\s+[a-z0-9_ -]{0,40}\s*file\b", low))
    nova_edit = bool(re.search(r"\bnova\b", low)) and _has_any(low, "add", "fix", "patch", "edit", "modify", "feature", "implement", "improve")

    creation = analyze_creation_request(text)
    coding = plan_coding_execution(text)
    expected_files = list(coding.get("expected_files") or creation.get("likely_files") or [])
    verify_command = str(coding.get("verify_command") or "")
    language = _detect_language(low, coding)
    project_or_script = "project"
    must_not_create_scaffold = False
    target = "new_artifact"

    if nova_edit:
        target = "nova_source_edit"
        project_or_script = "nova_edit"
        must_not_create_scaffold = True
        expected_files = []
        verify_command = "python -m compileall -q winlocalassistant app.py"
    elif one_file:
        project_or_script = "script_or_single_file"
        must_not_create_scaffold = True
        if language == "PowerShell":
            expected_files = ["script.ps1"]
            verify_command = "powershell -NoProfile -Command \"$null = [scriptblock]::Create((Get-Content .\\script.ps1 -Raw)); 'syntax ok'\""
        elif language == "Python":
            expected_files = ["script.py"]
            verify_command = "python -m py_compile script.py"
        elif expected_files:
            expected_files = expected_files[:1]
    elif language == "PowerShell":
        project_or_script = "script"
        expected_files = ["script.ps1"] if "script.ps1" not in expected_files else expected_files
        verify_command = verify_command or "powershell -NoProfile -Command \"$null = [scriptblock]::Create((Get-Content .\\script.ps1 -Raw)); 'syntax ok'\""
    elif language == "Python" and str(coding.get("artifact_type", "")).endswith("script"):
        project_or_script = "script"
    elif language == "HTML/CSS/JavaScript":
        project_or_script = "project"
        if not expected_files:
            expected_files = ["index.html", "style.css", "app.js", "README.md"]

    return {
        "ok": True,
        "source_request": text,
        "user_asked_for_one_file": one_file,
        "language": language,
        "project_or_script": project_or_script,
        "must_not_create_scaffold": must_not_create_scaffold,
        "expected_output_files": expected_files,
        "verification_command": verify_command,
        "target": target,
        "creation_analysis": creation,
        "coding_execution_plan": coding,
    }
