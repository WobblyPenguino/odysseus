# Nova GUI visual verification

This patch was visually checked with a headless Chromium/Playwright render at a 1920x1000 viewport using Nova's generated HTML.

Verified states:

- Left drawer opened to `files`.
- Icon rail stayed separate and did not show clipped text labels under the drawer.
- Drawer left edge was positioned after the icon rail, not on top of it.
- Right inspector drawer was closed and hidden, removing the previous blank/grey right-side panel.
- Chat canvas remained full width behind the reserved drawer space.
- Composer stayed inside the viewport and did not drift off the right side.

Evidence image:

- `docs/NOVA_GUI_VISUAL_VERIFICATION_20260608.png`

Key measured geometry from the verification render:

```json
{
  "rail": {"x": 0, "width": 58},
  "left_drawer": {"x": 72, "width": 380},
  "right_drawer": {"visibility": "hidden", "opacity": 0},
  "chat": {"x": 58, "width": 1862},
  "composer": {"x": 719, "width": 920}
}
```

Future GUI-edit rule: do not put new layout overrides back into the large HTML string unless unavoidable. Prefer `winlocalassistant/webui_layout_overhaul.py`, then add a route/static test in `tests_nova_gui_startup_routes_v55_3_161.py`.
