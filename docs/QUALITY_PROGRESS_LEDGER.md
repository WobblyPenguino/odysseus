# Quality Progress Ledger

This file tracks code-quality/integrity issues patched across Nova releases so future progress can be compared.

## v55.3.6

- Reviewed the v55.3.5 CodeRabbit-style quality gate installation and verified the suite compiled and passed before patching.
- Fixed quality-gate report filename collisions by adding nanosecond-stamped output names and collision-safe fallback numbering.
- Fixed misleading quality-gate counts: the gate now preserves total blocking/warning/note counts separately from displayed comments, so large reports are not under-counted when capped.
- Reduced duplicate markdown rendering in the `code_quality_gate` tool result path for better command efficiency.
- Added `code_quality_gate`, `code_review_audit`, and `code_repair_audit` to the tool catalogue so installed quality tools are discoverable and documented.
- Added `/quality-progress` and this ledger so future patched issues can be tracked across releases.
