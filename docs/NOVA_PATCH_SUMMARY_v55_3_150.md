# Nova v55.3.150 Patch Summary

Repo research and codebase sanity audit pass.

## Added
- `/codebase-sanity-audit` for redundancy/risk/rewrite scanning.
- `/repo-research-radar` for installed repo ideas and future integration priorities.
- Expanded capability manifests: agent observability, SWE-style issue repair, AgentGit-style checkpoint branching, Agno-style control plane.

## Hardened
- Several small state writers now use `safe_io` atomic writes.

## Validation
- Compileall, targeted pytest, startup validation, Doctor, command verify, repo assurance, browser smoke, bug review and regression sweep.
