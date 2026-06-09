# Nova GUI Layout Status and Recovery

This document is for humans or AI agents who have no previous chat context and need to diagnose the Nova web UI layout.

## Primary files

- `winlocalassistant/webui.py` is the legacy static HTML/server file. Avoid broad rewrites here.
- `winlocalassistant/webui_layout_overhaul.py` contains the modular CSS/JS override layer for drawer/chat layout.
- `winlocalassistant/gui_layout_diagnostics.py` contains read-only static layout contract checks.
- `tests_nova_gui_startup_routes_v55_3_161.py` contains the focused GUI route/layout regression tests.

## Commands

Run:

```powershell
python app.py /gui-layout-status
python app.py /gui-visual-test
python -m pytest -q tests_nova_gui_startup_routes_v55_3_161.py
```

In the browser header, click:

- `focus` to close drawers and reclaim the chat canvas
- `layout` to run browser geometry checks
- `routes` to test backend command routing
- `files` or `commands` to reopen the left drawer

## Browser console check

Open DevTools and run:

```javascript
window.novaGuiLayoutDiagnose && window.novaGuiLayoutDiagnose()
```

Healthy output should have `ok: true`, no warnings, a hidden right drawer when closed, and the left drawer x-position greater than the icon rail right edge.

## Cache/stale server recovery

If the old broken layout persists:

1. Stop the Nova terminal.
2. Close the browser tab.
3. Start the patched folder with `START_NOVA_HERE.bat`.
4. Open `http://127.0.0.1:8766/?layout_check=1`.
5. Press `Ctrl+Shift+R`.
6. Click `layout` and upload the screenshot plus `logs/validation_latest.txt` if it still fails.


## Latest visual verification artifact

- `docs/NOVA_GUI_LAYOUT_STATUS_VISUAL_20260608.png`
- `logs/gui_layout_status_patch_visual_20260608.json`

The latest verification opened the files drawer at 1920x1000 and reported `ok: true` with no geometry warnings.
