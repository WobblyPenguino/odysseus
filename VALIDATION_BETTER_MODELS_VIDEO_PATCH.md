# Nova better-model + video-manifest patch validation

Patch date: 2026-06-06

## Implemented

- Added explicit better-PC model environment launcher: `start_better_models_env.ps1`.
- Added environment override support for `NOVA_MODEL`, `NOVA_CODE_MODEL`, `NOVA_CHAT_MODEL`, `NOVA_PLANNER_MODEL`, `NOVA_VISION_MODEL`, and `NOVA_LOCAL_MODEL_TIMEOUT_SEC`.
- Updated default local model roles toward:
  - main/code/planner: `qwen3-coder:30b`
  - fast/chat fallback: `gemma2:2b`
  - vision: `llama3.2-vision:11b`
  - embeddings: `nomic-embed-text:latest`
- Added actual CLI thinking-time display in `AssistantCore.repl()` and one-shot command routing in `main.py`, not only a helper stub.
- Added `winlocalassistant/nova_video.py` manifest-first video planning layer.
- Added `/video-plan`, `/nova-video-plan`, `/movie-plan`, `/video-status`, and `/nova-video-status` command routes.
- Added ToolRegistry tools: `video_plan`, `nova_video_plan`, `video_status`, and `nova_video_status`.
- Added tests:
  - `tests_nova_video_manifest.py`
  - `tests_nova_better_model_env.py`

## Validation run in this container

Commands run:

```powershell
python -m compileall app.py winlocalassistant
python -m pytest -q tests_nova_video_manifest.py tests_nova_better_model_env.py tests_v55_3_149_repo_upgrade_readiness.py tests_v55_3_150_repo_research_codebase_audit.py
python -m pytest -q tests_v52_roadmap.py tests_v52_5_roadmap.py tests_v55_3_23_sandbox_permission_ui.py tests_v55_3_24_webui_js_syntax.py tests_v55_3_25_docker_diagnostics.py tests_v55_3_26_docker_validation_backend.py tests_v55_3_28_docker_history_cleanup.py tests_v55_3_32_less_strict_sandbox_policy.py tests_v55_3_39_gui_project_validation_polish.py tests_v55_3_42_remaining_features.py tests_v55_3_93_browser_runtime_reference_hardening.py tests_v55_3_94_codebase_flow_review.py tests_v55_3_95_nova_gui_project_generation.py tests_v55_3_97_gui_overhaul.py
python -m pytest -q tests_model_health_timeout.py tests_image_generation_backend.py tests_v55_3_140_safety_validation_dock.py tests_v55_3_139_odysseus_layout_sanity.py
python -m pytest -q tests_nova_video_manifest.py tests_nova_better_model_env.py tests_v55_3_139_odysseus_layout_sanity.py tests_v55_3_140_safety_validation_dock.py tests_v55_3_149_repo_upgrade_readiness.py tests_v55_3_150_repo_research_codebase_audit.py
```

Results:

- Compile: passed.
- New video/model env tests: passed.
- Current-version readiness/research tests: passed.
- GUI compatibility group: passed.
- Image/model-health/safety layout tests: passed.
- Final focused regression group: 22 passed.

Full-suite note: the full `python -m pytest -q` command was attempted in this Linux/Python 3.13 container, but it exceeded the tool execution window before completion. The same suite had already passed in the user's Windows/Python 3.12 environment before this patch, and the focused groups covering the changed areas passed here.

## Use after extract

From the extracted project folder:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
& "..\.venv\Scripts\Activate.ps1"
. .\start_better_models_env.ps1
python -m pytest -q tests_nova_video_manifest.py tests_nova_better_model_env.py
python app.py
```

Video planning smoke command inside Nova:

```text
/video-plan 10 second cinematic trailer about Nova building a project
```

Status command:

```text
/video-status
```
