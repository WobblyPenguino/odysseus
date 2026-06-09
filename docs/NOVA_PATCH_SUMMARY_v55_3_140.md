# Nova v55.3.140 patch summary

## Fixed

- Bug-review stale-version detection now ignores the `wlaWakeDefaultApplied` localStorage migration marker instead of treating it as user-visible stale release text.
- `winlocalassistant/nova_odysseus_suite.py` no longer uses a raw `Path.open("ab")` append handle at the launcher call site.
- `winlocalassistant/safe_io.py` now owns `open_binary_append_handle()` for subprocess stdout/stderr log redirection.
- Release metadata now points to v55.3.140.

## Improved

- The main GUI now includes an Odysseus-style validation command dock directly below the voyage workspace cards.
- The dock exposes safe, reviewable fill-buttons for `/release-hygiene`, `/architecture-audit`, `/nova-eval-packs core`, and `/patch-impact-plan ...`.

## Safety

- The new GUI buttons fill commands only; they do not auto-run checks or mutate project files.
- No existing Odysseus runtime, FastAPI bridge, voice, sandbox, or autonomous paths were removed.

## Validation

- Compileall passed for `app.py` and `winlocalassistant`.
- All 177 `tests_*.py` files were run in smaller chunks and passed.
- Final targeted regression slice passed 33/33.
- `/doctor` passed 9/9 on a clean release tree.
- `/architecture-audit` passed all release/version/runtime checks and only retained the existing large-module advisory for `core.py` and `tools.py`.
- `/bug-review` passed 5/5 with no critical, high or medium findings.
- `/command-verify` passed 19/19.
