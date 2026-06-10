
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.validate_idea_promotion_candidates import load_candidates, validate_candidates


def recent_git_log(limit: int = 100) -> str:
    try:
        result = subprocess.run(
            ["git", "--no-pager", "log", "--oneline", f"-{limit}"],
            check=False,
            capture_output=True,
            text=True,
        )
        return result.stdout or ""
    except Exception:
        return ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("local_ai_cycles/config/NOVA_IDEA_PROMOTION_CANDIDATES.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("local_ai_cycles/memory/NOVA_IDEA_CANDIDATE_DOCTOR_LATEST.md"),
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=Path("local_ai_cycles/memory/NOVA_IDEA_CANDIDATE_DOCTOR_LATEST.json"),
    )
    parser.add_argument(
        "--fail-on-rejected",
        action="store_true",
        help="Return exit code 1 when rejected candidates are present.",
    )
    args = parser.parse_args()

    candidates = load_candidates(args.config)
    accepted, rejected = validate_candidates(candidates)
    log = recent_git_log()

    accepted_ids = [r.candidate_id for r in accepted]
    rejected_ids = [r.candidate_id for r in rejected]

    skipped_recent = [candidate_id for candidate_id in accepted_ids if candidate_id in log]
    fresh = [candidate_id for candidate_id in accepted_ids if candidate_id not in log]
    next_candidate = fresh[0] if fresh else ""

    args.out.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Nova Idea Candidate Doctor Latest",
        "",
        f"Config: `{args.config}`",
        "",
        "## Counts",
        f"- Accepted: {len(accepted)}",
        f"- Rejected: {len(rejected)}",
        f"- Recently completed/skipped: {len(skipped_recent)}",
        f"- Fresh available: {len(fresh)}",
        "",
        "## Next fresh candidate",
        f"- {next_candidate or 'none'}",
        "",
        "## Accepted candidates",
    ]

    for candidate_id in accepted_ids:
        marker = "fresh"
        if candidate_id in skipped_recent:
            marker = "recently-completed"
        lines.append(f"- {candidate_id} [{marker}]")

    lines += ["", "## Rejected candidates"]

    if rejected:
        for result in rejected:
            reason = "; ".join(result.errors)
            lines.append(f"- {result.candidate_id or '<missing-id>'}: {reason}")
    else:
        lines.append("- none")

    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    rejected_payload = [
        {
            "candidate_id": result.candidate_id,
            "errors": result.errors,
        }
        for result in rejected
    ]
    payload = {
        "config": str(args.config),
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "skipped_recent_count": len(skipped_recent),
        "fresh_count": len(fresh),
        "next_candidate": next_candidate,
        "accepted_candidates": accepted_ids,
        "rejected_candidates": rejected_payload,
        "skipped_recent": skipped_recent,
        "fresh": fresh,
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(f"candidate doctor accepted={len(accepted)} rejected={len(rejected)} fresh={len(fresh)} skipped_recent={len(skipped_recent)}")
    print(f"candidate doctor next={next_candidate or 'none'}")
    print(f"candidate doctor report={args.out}")
    print(f"candidate doctor json={args.json_out}")

    return 1 if rejected and args.fail_on_rejected else 0


if __name__ == "__main__":
    raise SystemExit(main())
