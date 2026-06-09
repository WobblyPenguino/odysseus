# Nova GUI Reset and Route Diagnostics

Purpose: give future humans or AI agents a fast way to diagnose the exact class of GUI bug where the browser shows a stale drawer, a ghost right panel, or command buttons that look available but return `Unknown command`.

## Files to inspect first

- `winlocalassistant/webui.py` — legacy static web UI, endpoint handlers, header buttons and browser helpers.
- `winlocalassistant/webui_layout_overhaul.py` — isolated CSS/JS layout override layer. Prefer editing here for layout fixes.
- `winlocalassistant/gui_layout_diagnostics.py` — static layout contract and reset guidance shown by `/gui-layout-status` and `/gui-reset-help`.
- `tests_nova_gui_startup_routes_v55_3_161.py` — GUI route/layout regression tests.

## Runtime buttons

Header buttons that matter for this issue:

- `focus` closes drawers and recentres chat.
- `routes` probes safe backend command routes.
- `layout` runs browser geometry diagnostics.
- `reset UI` clears stale browser layout keys and reapplies `gui-overhaul-v3` without deleting backend data.
- `files` and `commands` intentionally open the docked left drawer.

## Commands to run in Nova chat

```text
/gui-layout-status
/gui-reset-help
/media-status
/image-plan cinematic robot dog mascot
/video-status
/validation-status
```

## Browser console check

```js
window.novaGuiLayoutDiagnose && window.novaGuiLayoutDiagnose()
```

Expected: `ok: true` and `warnings: []`.

## What `reset UI` is allowed to do

It may clear browser-only layout localStorage keys such as old drawer widths and collapse state. It must not delete project files, logs, memory, remote profiles, custom tools or backend data.

## Test ladder after GUI changes

```powershell
python -m compileall -q app.py nova winlocalassistant
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -m pytest -q tests_nova_gui_startup_routes_v55_3_161.py tests_command_suggestions.py tests_v55_3_24_webui_js_syntax.py tests_webui_planning_visibility.py tests_webui_idle_status.py
python -m pytest -q tests_smoke.py
python -m winlocalassistant.validate --all
```
