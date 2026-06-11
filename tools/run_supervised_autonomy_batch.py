import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Allow direct execution via:
#   python tools/run_supervised_autonomy_batch.py --help
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from winlocalassistant.autonomy_readiness import build_autonomy_readiness

# --- Configuration ---
TASK_LOOP_SCRIPT = REPO_ROOT / "run_nova_task_queue_loop.ps1"
BATCH_SUMMARY_MD = REPO_ROOT / "local_ai_cycles" / "memory" / "NOVA_SUPERVISED_AUTONOMY_BATCH_LATEST.md"
BATCH_SUMMARY_JSON = REPO_ROOT / "local_ai_cycles" / "memory" / "NOVA_SUPERVISED_AUTONOMY_BATCH_LATEST.json"
TASK_LOOP_SUMMARY_LATEST = REPO_ROOT / "local_ai_cycles" / "memory" / "NOVA_TASK_LOOP_SUMMARY_LATEST.md"
TASK_LOOP_MANUAL_REVIEW_LATEST = REPO_ROOT / "local_ai_cycles" / "memory" / "NOVA_TASK_LOOP_MANUAL_REVIEW_LATEST.md"

MIN_SCORE_THRESHOLD = 70
AUTONOMY_READINESS_SCORE_REQUIRED = 100

# --- Helper Functions ---
def _run_powershell_cmd(cmd: str, cwd: Path = REPO_ROOT, timeout: int = 300) -> Dict[str, Any]:
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False # Do not raise CalledProcessError
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "ok": result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Command timed out", "returncode": 1, "ok": False}
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "returncode": 1, "ok": False}

def _run_git_cmd(cmd: List[str], cwd: Path = REPO_ROOT) -> Dict[str, Any]:
    try:
        result = subprocess.run(
            ["git"] + cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "ok": result.returncode == 0
        }
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "returncode": 1, "ok": False}

def _get_git_status() -> Dict[str, Any]:
    return _run_git_cmd(["status", "--porcelain"])

def _parse_task_loop_summary(summary_path: Path) -> Dict[str, Any]:
    summary_content = ""
    if summary_path.exists():
        summary_content = summary_path.read_text(encoding="utf-8", errors="ignore")

    parsed = {
        "selected_task_id": None,
        "selected_task_score": None,
        "task_pool_exhausted": False,
        "validation_passed": False,
        "commit_happened": False,
        "repeated_failed_task": False,
        "raw_summary": summary_content
    }

    # Parse selected task and score. Preflight summaries can include an initial
    # low-score candidate before autonomous fallback, followed by the real final
    # selected task. Prefer the final candidate/selected-task evidence.
    score_matches = re.findall(r"Best task candidate (.+?): score=(-?\d+)", summary_content)
    if score_matches:
        selected_task_id, selected_task_score = score_matches[-1]
        parsed["selected_task_id"] = selected_task_id.strip()
        parsed["selected_task_score"] = int(selected_task_score)

    selected_task_match = re.search(r"^Selected task:\s*(\S+)\s*$", summary_content, re.MULTILINE)
    fallback_score_match = re.search(r"^Autonomous candidate fallback score:\s*(-?\d+)\s*$", summary_content, re.MULTILINE)
    if selected_task_match:
        parsed["selected_task_id"] = selected_task_match.group(1).strip()
        if fallback_score_match:
            parsed["selected_task_score"] = int(fallback_score_match.group(1))

    # Check for task pool exhaustion
    if "task-pool-exhausted" in summary_content or "No healthy or recoverable task available" in summary_content:
        parsed["task_pool_exhausted"] = True

    # Check for validation and commit
    if "Result: committed" in summary_content and "Validation gates passed" in summary_content:
        parsed["validation_passed"] = True
        parsed["commit_happened"] = True
    elif "Validation gates passed" in summary_content:
        parsed["validation_passed"] = True

    # Check for repeated failed task markers. A normal rejected/validation-failed
    # cycle is not necessarily repeated; repeated detection must require explicit
    # repeated/recent-failed outcome language.
    lower_summary = summary_content.lower()
    if (
        "outcome category: repeated-failure" in lower_summary
        or "reason=repeated-failure" in lower_summary
        or "repeated failed task detected" in lower_summary
    ):
        parsed["repeated_failed_task"] = True

    return parsed

def _check_autonomy_readiness() -> Dict[str, Any]:
    # Real read-only readiness call
    report = build_autonomy_readiness(".")
    score = int(report.get("score", 0))
    return {"score": score, "ok": score == 100, "summary": f"Autonomy readiness {score}/100"}

def _write_batch_summary(batch_summary: Dict[str, Any]):
    BATCH_SUMMARY_MD.parent.mkdir(parents=True, exist_ok=True)
    
    md_content = [
        f"# Supervised Autonomy Batch Summary - {batch_summary['batch_id']}",
        f"Generated: {batch_summary['timestamp']}",
        f"Max Cycles: {batch_summary['max_cycles']}",
        f"Final Status: {batch_summary['final_status']}",
        f"Stop Reason: {batch_summary['stop_reason']}",
        "",
        "## Cycle Details:"
    ]
    for cycle in batch_summary['cycles']:
        md_content.append(f"### Cycle {cycle['cycle_num']}")
        md_content.append(f"Status: {cycle['status']}")
        md_content.append(f"Preflight Task: {cycle['preflight_task_id']} (Score: {cycle['preflight_task_score']})")
        md_content.append(f"Live Cycle Status: {cycle['live_cycle_status']}")
        md_content.append(f"Validation Passed: {cycle['validation_passed']}")
        md_content.append(f"Commit Happened: {cycle['commit_happened']}")
        md_content.append(f"Git Clean Post-Cycle: {cycle['git_clean_post_cycle']}")
        md_content.append(f"Autonomy Readiness Post-Cycle: {cycle['autonomy_readiness_post_cycle_score']}")
        md_content.append(f"Stop Reason (if any): {cycle['cycle_stop_reason']}")
        md_content.append("")
    
    md_content.append("## Full Batch Log:")
    md_content.append("```json")
    md_content.append(json.dumps(batch_summary, indent=2))
    md_content.append("```")

    BATCH_SUMMARY_MD.write_text("\n".join(md_content), encoding="utf-8")
    BATCH_SUMMARY_JSON.write_text(json.dumps(batch_summary, indent=2), encoding="utf-8")

# --- Main Controller Logic ---
def run_supervised_autonomy_batch(max_cycles: int, batch_id: str, dry_run: bool = False):
    batch_log: Dict[str, Any] = {
        "batch_id": batch_id,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "max_cycles": max_cycles,
        "dry_run": dry_run,
        "cycles": [],
        "final_status": "running",
        "stop_reason": "N/A"
    }

    for i in range(1, max_cycles + 1):
        cycle_log: Dict[str, Any] = {
            "cycle_num": i,
            "status": "started",
            "preflight_task_id": None,
            "preflight_task_score": None,
            "live_cycle_status": "N/A",
            "validation_passed": False,
            "commit_happened": False,
            "git_clean_post_cycle": False,
            "autonomy_readiness_post_cycle_score": None,
            "cycle_stop_reason": None
        }
        batch_log["cycles"].append(cycle_log)

        print(f"\n--- Supervised Autonomy Batch: Cycle {i}/{max_cycles} ---")

        # 1. Check git is clean
        git_status = _get_git_status()
        if not git_status["ok"] or git_status["stdout"].strip():
            stop_reason = "Dirty git state detected before preflight."
            print(f"STOP: {stop_reason}")
            cycle_log["status"] = "stopped"
            cycle_log["cycle_stop_reason"] = stop_reason
            batch_log["final_status"] = "stopped"
            batch_log["stop_reason"] = stop_reason
            _write_batch_summary(batch_log)
            return 1

        # 2. Check autonomy readiness
        readiness = _check_autonomy_readiness()
        if not readiness["ok"] or readiness["score"] < AUTONOMY_READINESS_SCORE_REQUIRED:
            stop_reason = f"Autonomy readiness below {AUTONOMY_READINESS_SCORE_REQUIRED}/100: {readiness['summary']}"
            print(f"STOP: {stop_reason}")
            cycle_log["status"] = "stopped"
            cycle_log["cycle_stop_reason"] = stop_reason
            batch_log["final_status"] = "stopped"
            batch_log["stop_reason"] = stop_reason
            _write_batch_summary(batch_log)
            return 1

        # 3. Run preflight-only mode
        print("Running task loop in preflight-only mode...")
        preflight_cmd = f"{TASK_LOOP_SCRIPT} -Cycles 1 -Mode code -PreflightOnly -MaxRecoveryCandidates 3"
        preflight_result = _run_powershell_cmd(preflight_cmd)
        
        if not preflight_result["ok"]:
            stop_reason = f"Preflight command failed: {preflight_result['stderr']}"
            print(f"STOP: {stop_reason}")
            cycle_log["status"] = "stopped"
            cycle_log["cycle_stop_reason"] = stop_reason
            batch_log["final_status"] = "stopped"
            batch_log["stop_reason"] = stop_reason
            _write_batch_summary(batch_log)
            return 1

        preflight_summary = _parse_task_loop_summary(TASK_LOOP_SUMMARY_LATEST)
        cycle_log["preflight_task_id"] = preflight_summary["selected_task_id"]
        cycle_log["preflight_task_score"] = preflight_summary["selected_task_score"]

        # 4. Stop if task pool exhausted before requiring a selected task.
        if preflight_summary["task_pool_exhausted"]:
            stop_reason = "Task pool exhausted in preflight."
            print(f"STOP: {stop_reason}")
            cycle_log["status"] = "stopped"
            cycle_log["cycle_stop_reason"] = stop_reason
            batch_log["final_status"] = "stopped"
            batch_log["stop_reason"] = stop_reason
            _write_batch_summary(batch_log)
            return 1

        # 5. Parse selected task and score, require score >= 70.
        if preflight_summary["selected_task_id"] is None:
            stop_reason = "No task selected in preflight."
            print(f"STOP: {stop_reason}")
            cycle_log["status"] = "stopped"
            cycle_log["cycle_stop_reason"] = stop_reason
            batch_log["final_status"] = "stopped"
            batch_log["stop_reason"] = stop_reason
            _write_batch_summary(batch_log)
            return 1
        if preflight_summary["selected_task_score"] is None or preflight_summary["selected_task_score"] < MIN_SCORE_THRESHOLD:
            stop_reason = f"Selected task score {preflight_summary['selected_task_score']} below {MIN_SCORE_THRESHOLD}."
            print(f"STOP: {stop_reason}")
            cycle_log["status"] = "stopped"
            cycle_log["cycle_stop_reason"] = stop_reason
            batch_log["final_status"] = "stopped"
            batch_log["stop_reason"] = stop_reason
            _write_batch_summary(batch_log)
            return 1
        
        print(f"Preflight passed. Selected task: {preflight_summary['selected_task_id']} (Score: {preflight_summary['selected_task_score']})")

        if dry_run:
            stop_reason = "Dry run complete after preflight."
            print(f"INFO: {stop_reason}")
            cycle_log["status"] = "completed"
            batch_log["final_status"] = "completed"
            batch_log["stop_reason"] = stop_reason
            _write_batch_summary(batch_log)
            return 0

        # 6. Run exactly one existing task-loop live cycle
        print("Running one live task loop cycle...")
        live_cycle_cmd = f"{TASK_LOOP_SCRIPT} -Cycles 1 -Mode code -MaxRecoveryCandidates 3"
        live_cycle_result = _run_powershell_cmd(live_cycle_cmd)
        
        cycle_log["live_cycle_status"] = "completed" if live_cycle_result["ok"] else "failed"

        if not live_cycle_result["ok"]:
            stop_reason = f"Live task loop cycle failed: {live_cycle_result['stderr']}"
            print(f"STOP: {stop_reason}")
            cycle_log["status"] = "stopped"
            cycle_log["cycle_stop_reason"] = stop_reason
            batch_log["final_status"] = "stopped"
            batch_log["stop_reason"] = stop_reason
            _write_batch_summary(batch_log)
            return 1
        
        live_summary = _parse_task_loop_summary(TASK_LOOP_SUMMARY_LATEST)
        cycle_log["validation_passed"] = live_summary["validation_passed"]
        cycle_log["commit_happened"] = live_summary["commit_happened"]
        cycle_log["repeated_failed_task"] = live_summary["repeated_failed_task"]

        # 7. Post-cycle checks
        if live_summary["repeated_failed_task"]:
            stop_reason = "Repeated failed task detected in live cycle."
            print(f"STOP: {stop_reason}")
            cycle_log["status"] = "stopped"
            cycle_log["cycle_stop_reason"] = stop_reason
            batch_log["final_status"] = "stopped"
            batch_log["stop_reason"] = stop_reason
            _write_batch_summary(batch_log)
            return 1

        if not live_summary["validation_passed"]:
            stop_reason = "Validation failed in live cycle."
            print(f"STOP: {stop_reason}")
            cycle_log["status"] = "stopped"
            cycle_log["cycle_stop_reason"] = stop_reason
            batch_log["final_status"] = "stopped"
            batch_log["stop_reason"] = stop_reason
            _write_batch_summary(batch_log)
            return 1
        
        post_cycle_git_status = _get_git_status()
        cycle_log["git_clean_post_cycle"] = post_cycle_git_status["ok"] and not post_cycle_git_status["stdout"].strip()
        if not cycle_log["git_clean_post_cycle"]:
            stop_reason = "Dirty git state detected after live cycle."
            print(f"STOP: {stop_reason}")
            cycle_log["status"] = "stopped"
            cycle_log["cycle_stop_reason"] = stop_reason
            batch_log["final_status"] = "stopped"
            batch_log["stop_reason"] = stop_reason
            _write_batch_summary(batch_log)
            return 1
        
        post_cycle_readiness = _check_autonomy_readiness()
        cycle_log["autonomy_readiness_post_cycle_score"] = post_cycle_readiness["score"]
        if not post_cycle_readiness["ok"] or post_cycle_readiness["score"] < AUTONOMY_READINESS_SCORE_REQUIRED:
            stop_reason = f"Autonomy readiness below {AUTONOMY_READINESS_SCORE_REQUIRED}/100 after live cycle: {post_cycle_readiness['summary']}"
            print(f"STOP: {stop_reason}")
            cycle_log["status"] = "stopped"
            cycle_log["cycle_stop_reason"] = stop_reason
            batch_log["final_status"] = "stopped"
            batch_log["stop_reason"] = stop_reason
            _write_batch_summary(batch_log)
            return 1


        cycle_log["status"] = "completed"
        print(f"Cycle {i} completed successfully.")
    
    batch_log["final_status"] = "completed"
    batch_log["stop_reason"] = "Max cycles reached."
    print(f"\n--- Supervised Autonomy Batch: Completed {max_cycles} cycles ---")
    _write_batch_summary(batch_log)
    return 0

# --- Entry Point ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a supervised autonomy batch controller.")
    parser.add_argument("--max-cycles", type=int, default=3, help="Maximum number of cycles to run.")
    parser.add_argument("--batch-id", type=str, default=f"batch_{time.strftime('%Y%m%d_%H%M%S')}", help="Unique ID for the batch run.")
    parser.add_argument("--dry-run", "--preflight-only", action="store_true", help="Validate preflight and exit without running live tasks.")
    args = parser.parse_args()
    sys.exit(run_supervised_autonomy_batch(args.max_cycles, args.batch_id, args.dry_run))
