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


def find_first(pattern: str, text: str) -> str:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else ""


def find_last(pattern: str, text: str) -> str:
    matches = list(re.finditer(pattern, text, flags=re.IGNORECASE | re.MULTILINE))
    return matches[-1].group(1).strip() if matches else ""


def latest_cycle_section(summary: str) -> str:
    marker = "\n## Cycle "
    index = summary.rfind(marker)
    if index == -1:
        return summary
    return summary[index:].strip()


def split_files(value: str) -> list[str]:
    if not value:
        return []
    parts = re.split(r"[,;]", value)
    cleaned = []
    for part in parts:
        item = part.strip()
        if item.endswith("."):
            item = item[:-1]
        if item:
            cleaned.append(item)
    return cleaned


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
    latest_cycle_excerpt: str
    recommended_action: str


def triage() -> FailureTriage:
    summary = read_text(MEMORY / "NOVA_TASK_LOOP_SUMMARY_LATEST.md")
    batch = read_text(MEMORY / "NOVA_SUPERVISED_AUTONOMY_BATCH_LATEST.md")
    failure = read_text(MEMORY / "NOVA_TASK_FAILURE_REVIEW_LATEST.md")

    latest_section = latest_cycle_section(summary)
    focused = "\n".join([latest_section, failure])
    broad = "\n".join([summary, batch, failure])

    latest_result = find_last(r"^Result:\s*(.+)$", latest_section) or find_last(r"Final Status:\s*(.+)$", batch)
    latest_task = find_last(r"^Task:\s*(.+)$", latest_section) or find_last(r"Selected task:\s*(.+)$", latest_section)
    outcome_category = find_last(r"^Outcome category:\s*(.+)$", latest_section)

    why_line = find_last(r"^Why:\s*(.+)$", latest_section)
    parse_target = why_line or focused

    missing_required_files = split_files(
        find_last(r"missing required changed file\(s\):\s*([^\n]+?)\.\s*Changed file", parse_target)
    )
    changed_files = split_files(find_last(r"(?<!required )Changed file\(s\):\s*([^\n]+)", parse_target))
    denied_noneditable_files = split_files(
        find_last(r"Aider add-file prompts denied for non-editable file\(s\):\s*([^\n]+)", focused)
    )
    validation_command_failed = find_last(r"Command failed:\s*([^\n]+)", latest_section)

    if not latest_result:
        latest_result = find_last(r"^Result:\s*(.+)$", broad) or "unknown"
    if not latest_task:
        latest_task = find_last(r"^Task:\s*(.+)$", broad) or find_last(r"Selected task:\s*(.+)$", broad) or "unknown"
    if not outcome_category:
        outcome_category = find_last(r"^Outcome category:\s*(.+)$", broad) or "unknown"

    status = git_status_short()
    git_clean = not bool(status.strip())

    if missing_required_files:
        recommended_action = (
            "Latest task changed only part of its contract. Repair manually or strengthen the generated "
            "task prompt so every RequiredChangedFiles entry must be edited. Do not run another live cycle "
            "until source+test evidence exists."
        )
    elif denied_noneditable_files:
        recommended_action = (
            "Latest task attempted to add a non-editable file. Tighten candidate Editable/RequiredChangedFiles "
            "or prompt instructions so unrelated files are refused before Aider runs."
        )
    elif validation_command_failed:
        recommended_action = "Fix the latest failing validation command locally, then rerun Check and Preflight."
    elif outcome_category == "task-pool-exhausted":
        recommended_action = "Run Preflight after refreshing candidate discovery evidence; do not run live."
    elif not git_clean:
        recommended_action = "Clean generated noise or inspect dirty source files before any next run."
    else:
        recommended_action = "No specific latest failure pattern detected. Inspect latest task summary and batch log."

    excerpt = latest_section[-2000:] if latest_section else ""

    return FailureTriage(
        latest_result=latest_result,
        latest_task=latest_task,
        outcome_category=outcome_category,
        missing_required_files=missing_required_files,
        changed_files=changed_files,
        denied_noneditable_files=denied_noneditable_files,
        validation_command_failed=validation_command_failed,
        git_clean=git_clean,
        latest_cycle_excerpt=excerpt,
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
        "## Detected latest-cycle failure evidence",
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
        "## Latest cycle excerpt",
        "",
        "```text",
        result.latest_cycle_excerpt or "none",
        "```",
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
