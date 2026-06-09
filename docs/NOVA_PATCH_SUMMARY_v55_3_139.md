# Nova v55.3.139 Patch Summary

## Bugs / sanity issues found

- Recent FastAPI/Odysseus/self-apply/eval/layout regression tests passed, but `RELEASE_MANIFEST.json` was still stuck on `55.3.136` while the code reported `55.3.138`.
- `CHANGELOG.md` and `tests_release_hygiene.py` did not expose the current release version, causing Nova Doctor version-consistency warnings.
- `winlocalassistant.architecture_audit` required the entire long legacy `VERSION_LABEL` to appear in docs/UI. That was too strict and produced false version warnings after otherwise valid releases.
- The GUI already had Odysseus-inspired workbench pieces, but the main centre workspace still looked like a chat panel first and hid the workspace map inside the left drawer/popup.

## Implemented improvements

- Bumped Nova metadata to `55.3.139`.
- Added an Odysseus-style voyage workspace deck above the chat: Chat & Agents, Cookbook, Deep Research, Compare, Documents, Notes & Tasks, Memory and Themes.
- Kept each deck action routed through existing Nova functions, existing workbench popups, or command-fill flows. No new privileged command path was added.
- Fixed architecture audit version checking to require the current version and current release theme instead of the whole long legacy label.
- Synced `README.md`, `CHANGELOG.md`, `RELEASE_MANIFEST.json`, web UI visible strings and release hygiene tests.
- Added `tests_v55_3_139_odysseus_layout_sanity.py` to lock in the new layout markers and preserved routes.

## Validation

- `python -m compileall -q app.py winlocalassistant` -> PASS.
- Targeted pytest slice -> PASS 55/55.
- `python app.py /doctor` with bytecode disabled after cache cleanup -> PASS 9/9.
- `/architecture-audit` -> version/modules/docs/routes pass; remaining advisory risk is large legacy modules and local runtime-state presence.
- `/nova-api-status` -> optional FastAPI bridge status rendered with expected routes.
