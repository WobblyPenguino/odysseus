# Nova GUI AI Help Overlay

This patch adds small semi-transparent `?` symbols to interactive GUI elements and important panels.

## What it does

- Adds contextual help dots to buttons, inputs, drawers, command rows, project rows, the chat canvas, and the composer.
- Clicking a dot opens a local browser help panel with element context.
- The help panel can ask Nova to explain the element with `/gui-ai-help`, or generate adaptive plans with `/tool-use-plan`, `/pipeline-route`, and `/role-router`.
- The overlay is client-side and deterministic. It does not automatically run mutating commands.

## Files to inspect first

- `winlocalassistant/webui_ai_help_overlay.py` — browser overlay CSS/JS injection.
- `winlocalassistant/gui_context_help.py` — backend context-to-command help renderer.
- `winlocalassistant/webui.py` — imports and applies the overlay.
- `winlocalassistant/core.py` — routes `/gui-ai-help`, `/gui-context-help`, `/gui-command-help`, and `/gui-ai-upgrades`.
- `winlocalassistant/gui_layout_diagnostics.py` — static contract checks for layout and help overlay.

## Useful commands

```text
/gui-ai-help {"label":"files","command":"toggleOrbitDrawer('files')"}
/gui-ai-upgrades
/gui-layout-status
/tool-use-plan use the Files drawer to inspect project files
/pipeline-route fix a GUI layout issue and verify command routes
```

## Browser checks

Open the browser console and run:

```js
window.NovaGuiAiHelp && window.NovaGuiAiHelp.count
window.novaGuiAiHelpScan && window.novaGuiAiHelpScan()
window.novaGuiLayoutDiagnose && window.novaGuiLayoutDiagnose()
```

Expected:

- help dot count greater than zero
- layout diagnostic `ok: true`
- no visible right drawer unless explicitly opened

## Design rule for future edits

Do not bury future help-overlay changes inside the giant `webui.py` HTML string. Edit `webui_ai_help_overlay.py` and `gui_context_help.py` instead, then run the GUI route tests.


## Visual verification artifact

- `docs/NOVA_GUI_AI_HELP_OVERLAY_VISUAL_20260608.png`
- `logs/gui_ai_help_overlay_visual_20260608.json`
