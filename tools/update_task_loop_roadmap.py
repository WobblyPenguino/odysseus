from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROADMAP_MD = ROOT / "docs" / "NOVA_TASK_LOOP_ROADMAP.md"
ROADMAP_JSON = ROOT / "docs" / "NOVA_TASK_LOOP_ROADMAP.json"
DOCTOR_JSON = ROOT / "local_ai_cycles" / "memory" / "NOVA_IDEA_CANDIDATE_DOCTOR_LATEST.json"
MANUAL_START = "<!-- NOVA_ROADMAP_MANUAL_START -->"
MANUAL_END = "<!-- NOVA_ROADMAP_MANUAL_END -->"


def run_git(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def extract_manual_section(existing: str) -> str:
    if MANUAL_START in existing and MANUAL_END in existing:
        start = existing.index(MANUAL_START)
        end = existing.index(MANUAL_END) + len(MANUAL_END)
        return existing[start:end].strip()

    return f"""{MANUAL_START}
## Long-term roadmap

### Phase 1 — Make the loop easier to operate

- Add a command that runs the standing audit rule.
- Add a compact latest-state report.
- Link this roadmap from task-loop summaries.

### Phase 2 — Improve candidate generation quality

- Generate fresh candidates that are narrow, deterministic, source+test, and low-risk.
- Reject vague or broad candidates earlier.
- Prefer small existing modules over runtime/GUI changes.

### Phase 3 — Improve failure learning

- Add failed command, exit code, and Aider output tail to failure review reports.
- Categorise failures more precisely.
- Suggest the next safe recovery action after each failed task.

### Phase 4 — Release-readiness

- Keep roadmap and JSON state updated after every pass.
- Add a release-readiness note when the loop reaches a stable milestone.
{MANUAL_END}"""


def comparable_state(state: dict) -> dict:
    comparable = dict(state or {})
    comparable.pop("last_updated", None)
    return comparable


def build_state() -> dict:
    doctor = load_json(DOCTOR_JSON)
    return {
        "last_updated": datetime.now().isoformat(timespec="seconds"),
        "head": run_git(["rev-parse", "--short", "HEAD"]),
        "branch": run_git(["branch", "--show-current"]),
        "latest_commits": run_git(["--no-pager", "log", "--oneline", "-12"]).splitlines(),
        "candidate_doctor": {
            "accepted_count": doctor.get("accepted_count"),
            "rejected_count": doctor.get("rejected_count"),
            "fresh_count": doctor.get("fresh_count"),
            "skipped_recent_count": doctor.get("skipped_recent_count"),
            "next_candidate": doctor.get("next_candidate"),
        },
        "next_recommended_action": "Add a fresh narrow source+test external candidate or improve task-loop workflow safety.",
    }


def render_markdown(state: dict, manual_section: str) -> str:
    doctor = state["candidate_doctor"]
    commits = "\n".join(f"- `{line}`" for line in state["latest_commits"])

    return f"""# Nova Task Loop Roadmap

Last updated: {state["last_updated"]}

## Current status

- Branch: `{state["branch"]}`
- HEAD: `{state["head"]}`
- Candidate doctor accepted: `{doctor.get("accepted_count")}`
- Candidate doctor rejected: `{doctor.get("rejected_count")}`
- Fresh candidates available: `{doctor.get("fresh_count")}`
- Recently completed/skipped candidates: `{doctor.get("skipped_recent_count")}`
- Next candidate: `{doctor.get("next_candidate") or "none"}`

## Latest commits

{commits}

## What we have achieved

- External JSON task candidates are validated before use.
- Candidate doctor reports tell us whether there is fresh work.
- Runtime task registration and picker merge work.
- Preflight localization shows exact editable files and tests before Aider runs.
- Compile, targeted test, baseline test, generated-noise cleanup, and clean-git gates protect commits.
- Failed live tasks write failure review evidence.
- Stale patch/subagent reviews are cleared before live runs.
- Double-quoted Markdown code fences in PowerShell are rejected by validation.
- A local roadmap exists and can now be updated by script.

## Current blockers / weak spots

- External candidate pool can become exhausted after successful runs.
- Older built-in tasks are still low-scoring or quarantined.
- Aider can still produce syntax mistakes, so narrow scoped tasks are safer.
- The task loop does not yet call this updater automatically.

## Next recommended action

{state["next_recommended_action"]}

## Standing audit rule

Before committing or running the next live task:

1. PowerShell parser audit.
2. Markdown fence audit.
3. Python compile.
4. Pytest audit.
5. Candidate validation.
6. Task-loop validation.
7. Generated-noise cleanup.
8. `git diff --check`.
9. Inspect diff.
10. Commit.
11. Preflight proof.
12. Update this roadmap.

{manual_section}
"""


def main() -> None:
    state = build_state()
    previous_state = load_json(ROADMAP_JSON)
    if comparable_state(previous_state) == comparable_state(state):
        state["last_updated"] = previous_state.get("last_updated", state["last_updated"])

    ROADMAP_MD.parent.mkdir(parents=True, exist_ok=True)
    existing = ROADMAP_MD.read_text(encoding="utf-8") if ROADMAP_MD.exists() else ""
    manual_section = extract_manual_section(existing)
    ROADMAP_MD.write_text(render_markdown(state, manual_section), encoding="utf-8")
    ROADMAP_JSON.write_text(json.dumps(state, indent=2), encoding="utf-8")
    print(f"Updated {ROADMAP_MD}")
    print(f"Updated {ROADMAP_JSON}")


if __name__ == "__main__":
    main()
