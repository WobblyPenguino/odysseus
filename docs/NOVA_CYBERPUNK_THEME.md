# File: NOVA_CYBERPUNK_THEME.md

# Nova Cyberpunk 2077 Style Theme

This patch adds a modular **Cyberpunk 2077 inspired** visual skin to Nova's GUI.

## Files
- `winlocalassistant/webui_cyberpunk_theme.py`
- `winlocalassistant/webui_layout_overhaul.py`
- `winlocalassistant/webui_ai_help_overlay.py`
- `winlocalassistant/webui.py`

## What changed
- neon yellow primary actions
- cyan and magenta accent glows
- darker HUD-like panels
- angular clipped card/button shapes
- scanline/grid background overlays
- stronger cyberpunk styling for the AI help overlay
- runtime status helper: `window.novaCyberpunkThemeStatus()`

## Validation
Run:
- `python -m compileall -q app.py nova winlocalassistant`
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests_gui_cyberpunk_theme.py tests_nova_gui_startup_routes_v55_3_161.py tests_smoke.py`
- `PYTEST_CURRENT_TEST=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m winlocalassistant.validate --all`

## Runtime visual check
1. Start Nova.
2. Open the GUI and hard refresh.
3. Click `reset UI` then `layout`.
4. Confirm the UI uses a dark neon cyberpunk palette and the left rail + drawers remain readable.
5. In the browser console run:
   - `window.novaGuiLayoutDiagnose()`
   - `window.novaCyberpunkThemeStatus()`
