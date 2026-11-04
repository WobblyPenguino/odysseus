# Nova Agent Browser Research Latest

Source reviewed: `vercel-labs/agent-browser`.

Agent Browser is a browser automation CLI for AI agents. It provides useful commands for Nova-style GUI/browser validation, including accessibility snapshots, element refs, screenshots, annotated screenshots, text/HTML/value reads, clicks, fills, keyboard input, and browser state checks.

## Best Nova integration direction

Do not integrate unrestricted browsing first.

Best safe first step:
- Add a pure safety-policy layer.
- Allow localhost/127.0.0.1 by default.
- Do not reuse personal browser profiles.
- Do not import saved browser state by default.
- Do not run destructive browser actions automatically.
- Prefer read-only evidence commands first: snapshot, screenshot, get title, get url, console/error checks.
- Require explicit manual approval before install, remote debugging, profile reuse, upload, download, login, or external-domain browsing.

## Useful future Nova tasks

1. Agent Browser safety policy helper.
2. Agent Browser localhost command plan builder.
3. Agent Browser JSON/console/error output parser.
4. Agent Browser GUI evidence report.
5. Agent Browser preflight doctor wrapper.
6. Agent Browser Playwright fallback comparison.
7. Agent Browser screenshot/snapshot routing into Nova validation reports.

## Overnight relevance

Agent Browser could become a good GUI regression backend for overnight Nova work, but only after safety policy, domain restrictions, read-only mode, and evidence reports exist.
