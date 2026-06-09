# Nova v55.3.167 Task Execution Flow

This pass keeps Nova's existing architecture and adds a small reliability layer around current commands.

## Current command flow before the patch

- `/do GOAL` is routed in `winlocalassistant/core.py`, creates a planner plan with `make_plan(...)`, then calls `run_plan()`.
- `/code QUESTION` routes through the coding skill path and does not automatically scaffold a project.
- `/write PATH CONTENT` routes through `core.py` to `ToolRegistry.write_file(...)` in `winlocalassistant/tools.py`.
- `/read PATH` routes through `ToolRegistry.read_file(...)`.
- `/verify COMMAND` routes through `ToolRegistry.verify(...)`, which runs a safe shell command and scans output for obvious errors.
- `/shell COMMAND` routes through `ToolRegistry.run_shell(...)` with dangerous-command blocking and timeout handling.
- Autonomous routes are handled by `core.py` state plus existing autonomous helper modules.
- Scheduler routes go through the scheduler foundation and `ToolRegistry` wrappers.
- Strict project generation request contracts live in `winlocalassistant/project_request_contract.py`.
- `/release-readiness --full` lives in `winlocalassistant/release_readiness.py` and gates packaging.
- `/release-package` lives in `winlocalassistant/release_packager.py` and already blocks unless the latest readiness report passed.
- Searchable command help is centralized in `winlocalassistant/command_help.py`.

## What changed

- Added `winlocalassistant/task_execution.py`.
- Added `/task-contract GOAL` so broad prompts are decomposed before mutation.
- Added `/task-evidence` so code/write/run/verify evidence is easy to inspect.
- `/write`, `/write_files`, `/shell`, and `/verify` now record JSON and Markdown evidence under `logs/task_evidence/`.
- `/shell` now uses the repeated-failure guard before running and records repeated failures after failed runs.
- `/verify` now supports a summary mode when no command is supplied, and still supports direct verification commands.
- `/release-readiness --full` now includes task contract/evidence/repeated-failure checks.

## Stop conditions reinforced

Nova should stop and mark REVIEW/FAIL instead of looping when:

- the same command/action fails twice with the same error family;
- release-readiness fails;
- a high-risk edit lacks explicit permission;
- a code change has no verification command;
- task evidence is missing before packaging.
