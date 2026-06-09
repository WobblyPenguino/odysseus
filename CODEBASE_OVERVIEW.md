# Nova Codebase Overview

## Purpose
Nova is a local Windows assistant framework for planning, code generation, autonomous review, tool execution, and safety-aware self-improvement. It is organized as a Python package under `winlocalassistant/` with a small CLI/web launcher in `app.py` and `winlocalassistant/main.py`.

## High-level architecture

- `app.py`
  - Top-level launcher. Calls `winlocalassistant.main.main()`.
  - Supports `--web` for browser UI and one-shot CLI commands like `/nova-mega-test --confirm`.

- `winlocalassistant/main.py`
  - Configures console output.
  - Loads the assistant runtime from `AssistantCore.load()`.
  - Sets workspace context if the current working directory contains `app.py` and `winlocalassistant/`.
  - Dispatches one-shot commands or starts the CLI.

- `winlocalassistant/core.py`
  - Contains the main assistant runtime and command handling loop.
  - Loads configuration, tool registry, event logging, idle/autonomous candidates, model routing, and state.
  - Handles user commands, chat messages, tool execution, idle/autonomous cycles, and self-improvement.
  - Defines safe mutation and auto-apply policies.

- `winlocalassistant/tools.py`
  - Tool registry and tool execution engine.
  - Manages `ToolResult` objects, safe file writes, backups, self-improve candidates, and rollback support.
  - Contains the core machinery for safe code changes and file editing.

- `winlocalassistant/idle_engine.py`
  - Idle candidate collection and selection.
  - Verification command support and candidate evaluation.
  - Strategy persistence and report generation.

- `winlocalassistant/idle_policy.py`
  - Idle behaviour policy levels 0-3.
  - Controls whether idle cycles may only watch, propose, prepare patches, or auto-apply low-risk changes.

- `winlocalassistant/eventlog.py`
  - Persistent JSONL event logging for activities and model I/O.
  - Maintains run IDs and supports tailing logs for debugging.

- `winlocalassistant/model_router.py`
  - Routes model chat requests.
  - Integrates with local model runtimes and runtime-specific conversation handling.

- `winlocalassistant/command_verifier.py`
  - Verifies tool commands and generates verification reports.
  - Provides a second safety layer for generated or executed commands.

- `winlocalassistant/quality_*` and audit modules
  - `quality_dashboard.py`, `architecture_audit.py`, `bug_review.py`, `codebase_integrity_audit.py`, `improvement_roadmap.py`, `release_hygiene.py`, and many `nova_*` labs.
  - These modules create reports, audits, and improvement proposals rather than directly mutating code.

## Core runtime flow

1. User starts `python app.py` or `python app.py /command`.
2. `main.py` loads `AssistantCore`.
3. `core.py` initializes `AssistantCore` state, including:
   - config and workspace context
   - tool registry and sandbox permissions
   - idle/autonomous strategy state
   - event log and run metadata
4. The user interacts through CLI, web UI, or one-shot command.
5. Commands are routed to the appropriate module:
   - tool commands via `tools.py`
   - audit/report generation via `quality_*` modules
   - idle/autonomous candidates via `idle_engine.py`
   - model chat via `model_router.py`
6. Outputs and file edits are produced through safe I/O helpers in `safe_io.py`.
7. Changes are backed up, validated, and logged before promotion.

## Important invariants and safety rules

- `SYSTEM_PROMPT` in `core.py` defines the visible persona and key behaviour rules.
- `core.py` protects files like `core.py`, `tools.py`, and `security.py` from automatic idle auto-apply.
- `safe_io.py` contains atomic write helpers and quarantine behavior.
- Idle auto-apply is restricted to low-risk categories and requires explicit policies.
- Many modules use event logging and fail-safe wrappers, but broad `except Exception: pass` blocks are still present and should be reviewed carefully.
- `APP_DIR` is the trusted storage location for runtime state, logs, policies, and settings.

## Major module groups

- Launcher and runtime: `app.py`, `winlocalassistant/main.py`, `winlocalassistant/core.py`
- Configuration and state: `config.py`, `assistant_box.py`, `project_state_db.py`, `project_memory.py`
- Tools and execution: `tools.py`, `safe_io.py`, `sandbox_manager.py`, `sandbox_permissions.py`, `custom_tools.py`
- Idle/autonomy: `idle_engine.py`, `idle_policy.py`, `autonomous_loop_guard.py`, `autonomous_journal.py`, `autonomous_failure.py`, `autonomy_idle_intelligence.py`
- Audit and quality: `architecture_audit.py`, `bug_review.py`, `code_review_audit.py`, `codebase_integrity_audit.py`, `completion_audit.py`, `flow_audit.py`, `quality_dashboard.py`
- Model and local runtime: `model_router.py`, `ollama.py`, `model_health.py`, `local_model_optimizer.py`, `model_download_manager.py`
- Proposal/report labs: `nova_capability_drift_lab.py`, `nova_reliability_lab.py`, `nova_route_resilience_lab.py`, `nova_improvement_assurance_lab.py`, `nova_system_test.py`, `improvement_roadmap.py`, `proposal_ledger.py`
- UI and integration: `webui.py`, `jarvis_bridge.py`, `planning_dashboard.py`, `performance_profiler.py`, `docker_manager.py`

## How to verify

- Run `python tests_smoke.py` for smoke validation.
- Additional tests are under root filenames starting with `tests_`.
- Use `python -m pytest tests_smoke.py` if pytest is available.

## Known issues and audit notes

- There are many broad `except Exception: pass` blocks across the codebase, which are audit and reliability risks.
- `README.md` currently contains repeated release-note text; this is a documentation redundancy.
- New major features or command families should update this file immediately.
- Use this file as the first pass for architecture and command flow before digging into code.

## Update instructions for AI readers

If you modify the codebase, update this file.
- Add or remove major modules here.
- Update the runtime flow if the command dispatch or auto-apply lifecycle changes.
- Update the safety invariants and known issue list if new protections are added.
- Use this as the canonical "birds-eye" summary for top-level architecture.
