# Nova GUI Architecture Notes

## Current state
The GUI is a legacy single-file static HTML shell inside `winlocalassistant/webui.py`. It includes many historic compatibility markers and tests depend on route strings being present.

## New layout rule
Do not keep patching random CSS inside the huge `HTML` string unless unavoidable. Current layout fixes are injected by:

- `winlocalassistant/webui_layout_overhaul.py`
- `apply_gui_layout_overhaul(HTML)` in `webui.py`

This is deliberately additive. It avoids deleting old UI modes while making the active layout sane.

## Drawer behavior contract
- The left rail always owns a fixed narrow column.
- The left drawer is an overlay starting after the rail, so it must not cover the rail.
- The right drawer is an overlay from the right edge, so it must not create a blank reserved column.
- Opening either drawer must not resize or crush the central chat canvas.
- The `focus` button closes left/right/activity drawers and restores the chat.

## Regression tests to run after GUI changes
```powershell
python -m compileall -q winlocalassistant/webui.py winlocalassistant/webui_layout_overhaul.py
python -m pytest -q tests_nova_gui_startup_routes_v55_3_161.py tests_command_suggestions.py
python -m pytest -q tests_v55_3_24_webui_js_syntax.py tests_v55_3_141_clean_studio_gui.py tests_v55_3_142_orbit_workspace_drawer.py tests_webui_planning_visibility.py tests_webui_idle_status.py
```

## Manual GUI checks
Start Nova, then click:

- `focus`
- `routes`
- `commands`
- `files`
- left rail drawer items
- right `voice/state` or `output/editor`

Then run:

```text
/media-status
/image-plan cinematic robot dog mascot
/video-status
/validation-status
/tool-use-plan fix GUI layout and choose correct tools
```
