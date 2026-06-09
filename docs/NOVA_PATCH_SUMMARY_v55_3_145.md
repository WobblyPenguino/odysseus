# Nova v55.3.145 patch summary

Focus: database/state review and safe-write hardening.

## Changes

- Added `/db audit [DB]` for read-only assistant SQLite integrity checks.
- Added guarded `/db compact --confirm` for explicit SQLite checkpoint and VACUUM maintenance.
- Rewrote `project_state_db.py` to use `safe_io` atomic JSON writes and corrupt-file quarantine.
- Added project-state retention caps to stop very old recovery logs from bloating every run.
- Routed broad database/state review prompts to deterministic database audit, project-state audit, bug review and regression sweep instead of creating unrelated projects.

## Validation intent

This patch is intentionally small and deterministic. It avoids broad refactors of `core.py` and `tools.py`, and it keeps existing `/db put/get/merge/schema/export/search/delete` behaviour intact while adding audit/compact paths.
