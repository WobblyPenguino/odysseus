# Nova Legacy Continuity Guard

Nova has accumulated many valuable features across v55.3.139-v55.3.164: Odysseus-style workspace surfaces, wake/voice reliability, resize rails, live timeline observability, command verification, provider routing, remote access, scheduling, performance tuning, GUI recovery, concise help, behaviour rules and arcade/help runtime surfaces.

The new guard lives in:

- `winlocalassistant/legacy_continuity.py`
- `tests_legacy_continuity_guard.py`

## Commands

- `/legacy-continuity-audit`
- `/legacy-regression-lock`
- `/feature-regression-guard`
- `/legacy-continuity-audit --write`

## Purpose

Before any major patch is packaged, Nova should check that important historic capability anchors still exist. This prevents accidental deletion of old functionality when new GUI/theme/autonomous patches are added.

## How to use

```powershell
python app.py /legacy-continuity-audit
python app.py /legacy-continuity-audit --write
python -m pytest -q tests_legacy_continuity_guard.py
```

## Adding future anchors

When a valuable feature is restored or added, add a `LegacyAnchor` entry with:

- files that must exist
- marker strings that must remain routable
- commands that users rely on
- tests that protect the feature

Do not delete anchors just because they fail. If an anchor fails, either restore the feature or explicitly document why it is superseded and add a replacement anchor/test.
