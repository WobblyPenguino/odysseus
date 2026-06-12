from __future__ import annotations

import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MEMORY = ROOT / "local_ai_cycles" / "memory"


def read_text(path: Path) -> str:
    try:
        if path.exists() and path.is_file():
            return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    return ""


def git_status_short() -> str:
    try:
        return subprocess.check_output(
            ["git", "status", "--short"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.STDOUT,
        ).strip()
    except Exception as exc:
        return f"<git status failed: {exc}>"


@dataclass
class FailureTriage:
    latest_result: str
    latest_task: str
    outcome_category: str
    missing_required_files: list[str]
    changed_files: list[str]
    denied_noneditable_files: list[str]
    validation_command_failed: str
    git_clean: bool
    recommended_action: str


def find_first(pattern: str, text: str) -> str:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else ""


def split_files(value: str) -> list[str]:
    if not value:
        return []
    parts = re.split(r"[,;]", value)
    return [part.strip().strip(".") for part in parts if part.strip()]


def triage() -> FailureTriage:
    summary = read_text(MEMORY / "NOVA_TASK_LOOP_SUMMARY_LATEST.md")
    batch = read_text(MEMORY / "NOVA_SUPERVISED_AUTONOMY_BATCH_LATEST.md")
    failure = read_text(MEMORY / "NOVA_TASK_FAILURE_REVIEW_LATEST.md")
    combined = "\n".join([summary, batch, failure])

    latest_result = find_first(r"^Result:\s*(.+)$", summary) or find_first(r"Final Status:\s*(.+)$", batch)
    latest_task = find_first(r"^Task:\s*(.+)$", summary) or find_first(r"Selected task:\s*(.+)$", summary)
    outcome_category = find_first(r"^Outcome category:\s*(.+)$", summary)

    missing_required_files = split_files(
        find_first(r"missing required changed file\(s\):\s*([^\n]+?)\.\s*Changed file", combined)
    )
    changed_files = split_files(find_first(r"Changed file\(s\):\s*([^\n]+)", combined))
    denied_noneditable_files = split_files(find_first(r"Aider add-file prompts denied for non-editable file\(s\):\s*([^\n]+)", combined))
    validation_command_failed = find_first(r"Command failed:\s*([^\n]+)", combined)

    status = git_status_short()
    git_clean = not bool(status.strip())

    if missing_required_files:
        recommended_action = (
            "Repair the task manually or improve the generated task prompt so Aider must edit every "
            "RequiredChangedFiles entry. Do not run another live cycle until this task has source+test evidence."
        )
    elif denied_noneditable_files:
        recommended_action = (
            "Generated task attempted to add a non-editable file. Tighten candidate Editable/RequiredChangedFiles "
            "or add prompt instructions to refuse unrelated files."
        )
    elif validation_command_failed:
        recommended_action = "Fix the failing validation command locally, then rerun Check and Preflight."
    elif outcome_category == "task-pool-exhausted":
        recommended_action = "Run Preflight after refreshing candidate discovery evidence; do not run live."
    elif not git_clean:
        recommended_action = "Clean generated noise or inspect dirty source files before any next run."
    else:
        recommended_action = "No specific failure pattern detected. Inspect latest task summary and batch log."

    return FailureTriage(
        latest_result=latest_result or "unknown",
        latest_task=latest_task or "unknown",
        outcome_category=outcome_category or "unknown",
        missing_required_files=missing_required_files,
        changed_files=changed_files,
        denied_noneditable_files=denied_noneditable_files,
        validation_command_failed=validation_command_failed,
        git_clean=git_clean,
        recommended_action=recommended_action,
    )


def write_report(result: FailureTriage) -> None:
    MEMORY.mkdir(parents=True, exist_ok=True)
    json_path = MEMORY / "NOVA_FAILURE_TRIAGE_LATEST.json"
    md_path = MEMORY / "NOVA_FAILURE_TRIAGE_LATEST.md"

    json_path.write_text(json.dumps(asdict(result), indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Nova Failure Triage Latest",
        "",
        f"Latest result: {result.latest_result}",
        f"Latest task: {result.latest_task}",
        f"Outcome category: {result.outcome_category}",
        f"Git clean: {result.git_clean}",
        "",
        "## Detected failure evidence",
        "",
        f"Missing required files: {', '.join(result.missing_required_files) if result.missing_required_files else 'none'}",
        f"Changed files: {', '.join(result.changed_files) if result.changed_files else 'none'}",
        f"Denied non-editable files: {', '.join(result.denied_noneditable_files) if result.denied_noneditable_files else 'none'}",
        f"Validation command failed: {result.validation_command_failed or 'none'}",
        "",
        "## Recommended next action",
        "",
        result.recommended_action,
        "",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")

    print(md_path)
    print(json_path)
    print(result.recommended_action)


def main() -> int:
    write_report(triage())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
