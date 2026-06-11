# Nova Autonomy Full Codebase Audit

Generated: 2026-06-11T21:07:23

## Summary

- Python files scanned: `434`
- Doc/script/config files with autonomy-related hits: `238`
- Python parse errors: `0`
- Slash command count estimate: `991`
- Tool registry key count estimate: `459`
- Screen/image command bridge present: `True`
- Task loop present: `True`
- Roadmap updater present: `True`

## Highest-value next improvements

### 1. `task-loop-failure-recovery-ranking` — score `95`

Autonomy improves fastest when failed tasks are converted into better future candidate ranking instead of repeated weak retries.

Target files:
- `run_nova_task_queue_loop.ps1`
- `tests_task_loop_static_contract.py`

Validation:
- `PowerShell parser`
- `tests_task_loop_static_contract.py`
- `validate_task_loop_patch.ps1`

### 2. `autonomy-capability-audit-command` — score `90`

Nova needs a first-class command that reports autonomy readiness across task selection, tool routing, validation, memory, recovery, and project-state continuity.

Target files:
- `winlocalassistant/tools.py`
- `winlocalassistant/core.py`
- `tests_*.py`

Validation:
- `compileall`
- `targeted command/tool tests`
- `command suggestions tests`

### 3. `screen-analysis-image-analyze-bridge` — score `82`

The screen prompt command now exists; the next safe step is clearer bridge output telling users exactly how to pass the generated prompt into /image-analyze.

Target files:
- `winlocalassistant/screen_analysis.py`
- `tests_screen_analysis.py`

Validation:
- `tests_screen_analysis.py`
- `tests_command_suggestions.py`

### 4. `project-state-next-action-snapshot` — score `80`

Long-running autonomy needs a compact project-state snapshot: latest release, latest commit, known failures, changed files, validation evidence, and next safe action.

Target files:
- `winlocalassistant/project_state_db.py`
- `winlocalassistant/tools.py`
- `tests_*.py`

Validation:
- `project state tests`
- `tool registry contract tests`

### 5. `aider-output-damage-classifier` — score `78`

The recent failed status-count task damaged tests; a deterministic classifier for destructive diffs would improve automated repair/reject decisions.

Target files:
- `run_nova_task_queue_loop.ps1`
- `tests_task_loop_static_contract.py`

Validation:
- `task loop static contract`
- `validate_task_loop_patch.ps1`

## Largest Python files

- `winlocalassistant\tools.py` — `9691` lines, `475` functions, `2` classes
- `winlocalassistant\core.py` — `7728` lines, `217` functions, `1` classes
- `winlocalassistant\webui.py` — `2606` lines, `13` functions, `1` classes
- `winlocalassistant\nova_odysseus_suite.py` — `1734` lines, `61` functions, `0` classes
- `winlocalassistant\remote_access.py` — `1162` lines, `41` functions, `0` classes
- `winlocalassistant\docker_manager.py` — `882` lines, `31` functions, `0` classes
- `winlocalassistant\jarvis_bridge.py` — `851` lines, `25` functions, `1` classes
- `tests_task_loop_static_contract.py` — `807` lines, `80` functions, `0` classes
- `winlocalassistant\sandbox_manager.py` — `795` lines, `35` functions, `1` classes
- `winlocalassistant\autonomy_capabilities.py` — `644` lines, `10` functions, `4` classes
- `winlocalassistant\nova_video.py` — `637` lines, `23` functions, `3` classes
- `winlocalassistant\release_readiness.py` — `629` lines, `23` functions, `1` classes
- `tests_smoke.py` — `617` lines, `17` functions, `1` classes
- `winlocalassistant\validate.py` — `606` lines, `23` functions, `0` classes
- `winlocalassistant\autonomous_failure.py` — `542` lines, `22` functions, `2` classes
- `winlocalassistant\image_generation.py` — `534` lines, `25` functions, `1` classes
- `winlocalassistant\idle_engine.py` — `529` lines, `25` functions, `4` classes
- `winlocalassistant\task_execution.py` — `523` lines, `26` functions, `2` classes
- `tests_nova_remote_access_v55_3_164.py` — `516` lines, `30` functions, `0` classes
- `winlocalassistant\nova_coding_capabilities.py` — `485` lines, `12` functions, `1` classes

## Autonomy-related pattern counts

- `test`: `381` files
- `tool`: `287` files
- `project`: `219` files
- `validation`: `174` files
- `state`: `158` files
- `registry`: `142` files
- `autonomous`: `140` files
- `gui`: `129` files
- `validate`: `123` files
- `repair`: `115` files
- `browser`: `113` files
- `context`: `113` files
- `task`: `104` files
- `memory`: `92` files
- `mission`: `87` files
- `idle`: `74` files
- `image`: `58` files
- `screen`: `40` files
- `vision`: `25` files
- `roadmap`: `22` files
- `scheduler`: `22` files

## Python parse errors

- None detected by AST parser.

## Recommendation

The next patch should be small and source+test backed. Best current direction: add an autonomy capability/readiness report command or improve task-loop failure ranking. Do not run broad automated edits across the whole repo.

