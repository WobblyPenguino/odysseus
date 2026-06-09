# Nova v55.3.152 Integration Blueprint Adaptation

This patch adapts the first safe slice of the 6 June 2026 Nova Repo Integration Blueprint.

Implemented now:

- `winlocalassistant/orchestration_foundation.py`
  - `NovaState` state enum.
  - transition validator that blocks microphone/listening re-entry while processing or speaking unless explicit interrupt mode is enabled.
  - `JobQueue`, a durable SQLite queue with enqueue, dedupe, lease, cancel, mark, zombie detection and summary.
  - `ToolContract`, risk levels, approval requirements and validation rules.
  - integration foundation report renderer.
- `winlocalassistant/validate.py`
  - layered validation command: `python -m winlocalassistant.validate --all`.
  - compatibility shim: `python -m nova.validate --all`.
  - writes `logs/validation_latest.txt` and `logs/validation_latest.json`.
- ToolRegistry additions:
  - `integration_foundation`
  - `orchestrator_foundation`
  - `job_status` / `job_queue_status`
  - `job_enqueue` / `job_create`
  - `job_cancel`
  - `validate_all` / `nova_validate_all`
- CLI commands:
  - `/integration-foundation`
  - `/integration-status`
  - `/job-status`
  - `/job-enqueue KIND GOAL`
  - `/job-cancel JOB_ID`
  - `/validate-all`
- Tests:
  - `tests_nova_orchestration_foundation_v55_3_152.py`

Design notes:

- This is adapter-first and does not copy external repo code.
- The job queue does not execute commands by itself. Workers must still pass policy and validation gates.
- Risky browser, Windows utility and autonomous execution work remains gated by future worker-specific approvals.
- The already-added video manifest worker remains the creative-media foundation; this patch adds the orchestration layer it should eventually run through.
