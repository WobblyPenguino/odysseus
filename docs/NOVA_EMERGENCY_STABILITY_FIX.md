# Nova emergency stability fix

Patch ID: `emergency-chat-help-layout-stability-v1`

This patch addresses the real broken UX seen in the pasted run output: the legacy `/help` wall, model-timeout fallback for normal chat, cluttered drawer menus, bottom composer overlap, and Live Activity covering the chat controls.

## Key behaviour
- `/help` now shows concise grouped help and points to `/command-help QUERY`.
- `/help-full` keeps the old full command wall for compatibility.
- Tiny greetings like `hi` and capability questions have instant deterministic replies when the local model is slow.
- The floating `fix UI` button closes popups/drawers/activity and restores the composer.
- Live Activity starts compact and only expands when opened.
- The left overlay drawer hides unrelated sections so Search/Projects/Files do not all appear at once.

## Browser checks
Open the GUI and run in console:

```js
window.NovaEmergencyStability.diagnose()
window.novaGuiLayoutDiagnose()
```

Both should report no composer/activity overlap warnings after clicking `fix UI`.

## Commands to verify

```powershell
python -m compileall -q app.py nova winlocalassistant
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests_emergency_stability.py tests_smoke.py
PYTEST_CURRENT_TEST=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m winlocalassistant.validate --all
```
