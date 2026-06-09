# Nova AI Context Start Here

Read this first when you are an AI or human developer entering Nova without prior context.

## What Nova is
Nova is a Windows-first local assistant with a CLI, browser GUI, optional FastAPI bridge, local model routing, project tooling, scheduling, autonomous/idle workflows, remote PC access helpers, and validation/reporting gates.

## Start map
- `app.py`: entry point for CLI, one-shot commands, web UI and optional API modes.
- `winlocalassistant/main.py`: loads `AssistantCore` and dispatches commands.
- `winlocalassistant/core.py`: slash-command router and high-level assistant state.
- `winlocalassistant/tools.py`: safe tool registry and file/shell operations.
- `winlocalassistant/webui.py`: legacy static browser UI shell. Avoid large rewrites.
- `winlocalassistant/webui_layout_overhaul.py`: current modular GUI layout override layer. Prefer editing this for drawer/layout fixes.
- `winlocalassistant/nova_api.py`: optional FastAPI bridge and API command safety classifier.
- `winlocalassistant/remote_access.py`: remote access, Wake-on-LAN and remote profile helpers.
- `winlocalassistant/validate.py`: compile, test and chunked validation runner.

## Safe patch workflow
1. Reproduce the issue with a command or test.
2. Change the smallest module that owns the behavior.
3. Add or update a regression test.
4. Run compile checks and targeted tests.
5. Run `python -m winlocalassistant.validate --all`.
6. Only claim success for commands that actually passed.

## High-risk files
`core.py`, `tools.py`, `nova_api.py`, scheduler/remote/network code, and self-repair code all have safety implications. Prefer additive modules and tests over broad rewrites.


## GUI contextual AI help overlay

If the user says the GUI is confusing or asks for small help symbols on controls, inspect:

- `winlocalassistant/webui_ai_help_overlay.py`
- `winlocalassistant/gui_context_help.py`
- `winlocalassistant/gui_layout_diagnostics.py`
- `tests_nova_gui_startup_routes_v55_3_161.py`

The commands `/gui-ai-help`, `/gui-context-help`, `/gui-command-help`, and `/gui-ai-upgrades` are read-only help/planning helpers. They must not auto-run mutating commands.
