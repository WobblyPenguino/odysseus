# Nova Development Director Rules

Purpose:
Guide the guarded loop toward the next best Nova improvement, not just random small edits.

Allowed work types:
1. Regression test improvement
2. Validation/release-readiness improvement
3. Project-state/current-release memory improvement
4. Command/help consistency improvement
5. Model timeout/fallback improvement
6. Generated-report hygiene improvement
7. Small approved feature increment from NOVA_APPROVED_FEATURE_BACKLOG.md
8. Research note when external/current knowledge or Daniel approval is needed

Decision rules:
- Prefer the highest value safe target, not always the first target.
- If a target has no useful improvement, record it and try a different target next cycle.
- Do not repeatedly retry the same target unless mistake memory explains a fix.
- Prefer source + test when adding small functionality.
- Prefer test-only when hardening known behaviours.
- Prefer research note when feature scope is unclear.

Evidence rules:
- Inspect real implementation files before asserting APIs.
- Use command output, test output, git diff, and existing code as evidence.
- Do not invent classes, functions, command handlers, or report fields.
- If unsure, make no code change and write a research/approval note.

User-style sanity checks:
- For command/help work, verify /help, /help-full, command verification tests.
- For release-readiness work, verify validation/report hygiene tests.
- For model timeout/fallback work, verify model health/timeout tests.
- For project-state work, verify context/continuity tests.
- For GUI/runtime work, require manual review unless existing safe browser/runtime tests exist.

Stop conditions:
- Risky files touched
- generated reports touched as source changes
- placeholder tests
- new dependency proposed
- broad refactor
- unclear feature scope
- repeated failure in same area
