# Nova Arcade + Help Completion Patch

Patch ID: `remaining-tasks-arcade-help-runtime-v1`.

This patch completes the safest remaining tasks from the interaction overhaul pass:

- Adds `Nova Arcade` as a local-only modular mini-game framework.
- Adds the first game, `Nova: System Runner`, as a cyberpunk browser canvas game.
- Adds a backend registry in `winlocalassistant/nova_arcade.py` so future games can be listed without rewriting the core GUI.
- Adds `winlocalassistant/webui_arcade.py` to inject the local game overlay into the browser shell.
- Adds grouped/searchable command help metadata in `winlocalassistant/command_help.py`.

## Safety contract

- Arcade is local-only and stores high score in browser `localStorage`.
- It does not write project files.
- It does not execute model output as script.
- It does not make network calls.
- Command help is metadata-driven and examples only run when clicked or submitted by the user.

## Commands

- `/arcade`
- `/arcade-status`
- `/arcade-launch system-runner`
- `/arcade-manifest`
- `/command-help`
- `/command-help gui`
- `/command-help arcade`

## Browser checks

Start Nova, hard-refresh, then click:

1. `reset UI`
2. `layout`
3. `help`
4. `arcade`
5. `Launch System Runner`

Console checks:

- `window.NovaArcade.status()`
- `window.novaGuiLayoutDiagnose()`
- `window.NovaInteractionOverhaul.commandHelp()`

## Validation

Run:

```powershell
python -m compileall -q app.py nova winlocalassistant
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests_nova_arcade_help_completion.py tests_gui_interaction_overhaul.py tests_smoke.py
PYTEST_CURRENT_TEST=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m winlocalassistant.validate --all
```


Superseded by `emergency-chat-help-layout-stability-v1` for chat/help/layout emergency stabilization.
