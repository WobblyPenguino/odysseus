# Nova Wide Left Rail Layout

This patch widens the permanent non-popup left navigation rail. The earlier layout used a very narrow icon rail, which made labels such as `Search / Commands`, `Deep Research`, and `Voice / State` clip behind the docked drawer on wide monitors.

## Files to inspect first

- `winlocalassistant/webui_layout_overhaul.py` — source of the width variables and browser geometry diagnostic.
- `winlocalassistant/gui_layout_diagnostics.py` — static contract for `/gui-layout-status`.
- `tests_nova_gui_startup_routes_v55_3_161.py` — regression tests for rail width, drawer position, and browser layout markers.

## Contract

Desktop layout:

- `--orbit-left-wide` is the permanent left navigation rail width.
- The left drawer starts at `var(--orbit-left) + var(--orbit-safe-gap)`.
- Rail labels are visible and ellipsized, not hidden or clipped.
- On small screens, the rail collapses back to icon-only mode.

## Manual check

Start Nova, then click:

```text
reset UI
layout
files
layout
```

Expected: the left navigation rail has readable labels, the project/files drawer opens beside it, and the right panel remains hidden unless opened.
