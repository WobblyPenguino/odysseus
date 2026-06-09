# Nova Integration Radar

Goal: **improve validation**
Ready integrations: **7**
Missing/optional integrations: **3**

Recommendation: Highest value next integration: Playwright browser smoke tests, because Nova has had real GUI regressions that static tests only partly cover.

## Next best integrations
- **Docker validation backend** (ready, priority 95): Validate copied workspaces and proposed patches without touching the live tree.
  - Next: Keep Docker as the main patch simulation backend and add profile history/GUI review.
  - Command: `/docker-status`
- **Pre-commit release hooks** (ready, priority 90): Run a consistent local gate before promotion: syntax, formatting, static checks and tests.
  - Next: Add a .pre-commit-config.yaml template and /precommit-check command.
  - Command: `pre-commit run --all-files`
- **Ruff lint/format** (ready, priority 88): Fast Python linting catches unused imports, obvious bugs and style drift before Docker tests.
  - Next: Add optional /ruff-check and include it in release-gate when available.
  - Command: `ruff check winlocalassistant tests_*.py`
- **Playwright browser smoke tests** (ready, priority 86): Catch Send-button and JavaScript UI failures through real browser interaction, not just static JS parsing.
  - Next: Add a browser smoke test for sending chat, toggling tabs and Docker panel buttons.
  - Command: `npx playwright test`
- **Defensive security status** (ready, priority 74): Inventory Windows Defender/AVG-style tooling, firewall state, listening ports and Nova/Docker lab context before security work.
  - Next: Run /security-status before lab/security tasks and include the report in release checklist context.
  - Command: `/security-status`
- **Git safety/worktree backend** (optional/missing, priority 100): Make every autonomous/promotion change reviewable, reversible and branch/worktree isolated.
  - Next: Add /git-guard and optional git worktree validation before live promotion.
  - Command: `git status --short`
- **Mypy type checking** (optional/missing, priority 72): Find interface drift between modules as Nova grows.
  - Next: Start with a relaxed mypy profile for new modules only, then expand.
  - Command: `mypy winlocalassistant`
- **Semgrep security/static rules** (optional/missing, priority 70): Find risky subprocess, unsafe path handling, injection-prone strings and weak validation gates.
  - Next: Add optional semgrep scan profile to /release-gate.
  - Command: `semgrep scan --config auto`

## Full candidate list
⚪ **Git safety/worktree backend** — git available but current folder is not a repo — risk `low`
✅ **Docker validation backend** — integrated; docker CLI available — risk `low`
✅ **Pre-commit release hooks** — ready — risk `low`
✅ **Ruff lint/format** — ready — risk `low`
✅ **Playwright browser smoke tests** — ready — risk `medium`
✅ **Defensive security status** — integrated; read-only local inventory available — risk `low`
⚪ **Mypy type checking** — optional tool missing — risk `medium`
⚪ **Semgrep security/static rules** — optional tool missing — risk `medium`
✅ **uv environment manager** — ready — risk `low`
✅ **ripgrep code search** — ready — risk `low`