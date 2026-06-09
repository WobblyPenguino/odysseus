# Nova GUI Interaction Overhaul

Patch identity: `gui-autonomous-interaction-fix-v1`.

This layer fixes the specific run-output problems where Live Activity floated over the composer, the right panel appeared dark/blurred, help `?` buttons overlapped text, and autonomous mode was not visually isolated enough.

## Files

- `winlocalassistant/webui_interaction_overhaul.py` — browser-only interaction layer.
- `winlocalassistant/webui.py` — imports and applies the layer.
- `winlocalassistant/behavior_rules.py` — user correction/preference rules.
- `winlocalassistant/deterministic_generation.py` — narrow one-file fallback for simple script requests when Ollama times out.

## Runtime checks

Open Nova and run in the browser console:

```js
window.NovaInteractionOverhaul.version
window.NovaInteractionOverhaul.updateMicStatus()
window.NovaInteractionOverhaul.updateModelMini()
```

Expected GUI features:

- Mic/listener status box in the left/right status area.
- Local model status mini-card near the listener controls.
- Live Activity stays above the composer, is draggable/resizable, and can be minimized.
- Chat message headers have ↑/↓ navigation buttons.
- Code fences become copyable code boxes.
- `help` button opens searchable grouped command help.
- Autonomous mode shows a visible overlay with stop/status/log controls.

## Behaviour rules

Commands:

```text
/remember-behavior When I ask for one file, only make one file
/behavior-rules
/forget-behavior RULE_ID
```

Rules are planning preferences only. They cannot bypass safety, permissions, validation, or rollback.

## Visual verification artifact

- `docs/NOVA_GUI_INTERACTION_OVERHAUL_VISUAL_20260609.png`
- `logs/gui_interaction_overhaul_visual_20260609.json`
