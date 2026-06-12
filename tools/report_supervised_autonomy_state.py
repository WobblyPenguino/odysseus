#!/usr/bin/env python3
import subprocess
import re
import sys
from pathlib import Path

# Setup paths to allow importing from the repository root
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    # Directly source readiness check as required
    from winlocalassistant.autonomy_readiness import build_autonomy_readiness
except ImportError:
    def build_autonomy_readiness(root):
        return {"score": 0, "status": "unknown (ImportError)"}

# Standalone Constants
GOAL = "safely continue improving Nova without losing context, repeating failed work, or running live cycles without readiness/preflight/validation."
SUMMARY_PATH = REPO_ROOT / "local_ai_cycles" / "memory" / "NOVA_TASK_LOOP_SUMMARY_LATEST.md"

def run_git(args: list[str]) -> str:
    """Run a git command safely and return output."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False
        )
        return result.stdout.strip()
    except Exception:
        return ""

def parse_latest_task_info():
    """Extract task ID, score, and result from the latest summary."""
    info = {"task_id": "none", "score": "N/A", "result": "none"}
    if not SUMMARY_PATH.exists():
        return info
    try:
        content = SUMMARY_PATH.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return info

    # Result categorization
    if "Result: committed" in content:
        info["result"] = "committed"
    elif "Result: preflight-only" in content:
        info["result"] = "preflight-only"
    elif "Result: rejected" in content:
        info["result"] = "rejected"
    elif "Outcome category: task-pool-exhausted" in content:
        info["result"] = "task-pool-exhausted"

    # Task and Score parsing - Prefer explicit final selections
    score_matches = re.findall(r"Best task candidate (.+?): score=(-?\d+)", content)
    if score_matches:
        tid, tscore = score_matches[-1] # Take the final one
        info["task_id"] = tid.strip()
        info["score"] = tscore

    # Overwrite with explicit "Selected task" markers if present
    selected_task_match = re.search(r"^Selected task:\s*(\S+)\s*$", content, re.MULTILINE)
    fallback_score_match = re.search(r"^Autonomous candidate fallback score:\s*(-?\d+)\s*$", content, re.MULTILINE)
    if selected_task_match:
        info["task_id"] = selected_task_match.group(1).strip()
        if fallback_score_match:
            info["score"] = fallback_score_match.group(1)

    return info

def generate_report():
    """Generate and display the supervised autonomy state report."""
    branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"]) or "unknown"
    head = run_git(["rev-parse", "--short", "HEAD"]) or "unknown"
    tag = run_git(["describe", "--tags", "--always", "--dirty"]) or "none"
    dirty_out = run_git(["status", "--porcelain"])
    
    # Readiness from actual function call
    readiness = build_autonomy_readiness(".")
    score = readiness.get("score", 0)
    status = readiness.get("status", "unknown")
    task_info = parse_latest_task_info()
    
    is_clean = not bool(dirty_out)
    live_allowed = (score == 100) and is_clean
    next_safe_cmd = r"python .\tools\run_supervised_autonomy_batch.py --max-cycles 1 --dry-run"

    print("# Nova Supervised Autonomy State Report")
    print(f"\n**Autonomous Goal:** {GOAL}")
    print(f"**Current Working Area:** {branch}")
    print(f"**Branch and HEAD:** {branch} ({head})")
    print(f"**Latest Supervised Checkpoint:** {tag}")
    print(f"**Autonomy Readiness:** {score}/100 ({status})")
    print(f"**Latest Task-Loop Result:** {task_info['result']}")
    print(f"**Selected Candidate:** {task_info['task_id']} (Score: {task_info['score']})")
    print(f"**Live Supervised Autonomy Allowed:** {live_allowed}")
    print(f"**Next Safest Command:** `{next_safe_cmd}`")
    print(f"**Dirty / Generated-Noise Status:** {'Dirty' if not is_clean else 'Clean'}")

if __name__ == "__main__":
    generate_report()