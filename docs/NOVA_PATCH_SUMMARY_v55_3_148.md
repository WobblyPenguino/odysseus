# Nova v55.3.148 - Autonomous/Idle Tool-Awareness Orchestration

## Summary
This patch continues the repo-inspired upgrade plan by connecting pipeline routing, capability manifests, tool registry evidence and idle/autonomous mode. It does not copy external repo code. It translates the useful ideas into Nova-owned contracts and commands.

## Implemented
- Added `winlocalassistant/tool_orchestrator.py`.
- Added `/tool-awareness`, `/tool-awareness-audit`, `/autonomous-tool-plan` and `/idle-tool-plan`.
- Added ToolRegistry tools: `tool_awareness`, `tool_awareness_audit`, `tool_use_plan`, `autonomous_tool_plan`, and `idle_tool_plan`.
- Autonomous cycles now log a tool-awareness plan before running cycle tools.
- Idle cycles now include the same awareness/preflight evidence before selecting/reporting proposals.
- Tool plans combine:
  - pipeline router selection,
  - repo-inspired capability manifests,
  - autonomy capability catalogue matches,
  - registered ToolRegistry tool availability,
  - stop conditions and validation rules.
- Added regression tests in `tests_v55_3_148_tool_awareness_orchestration.py`.

## Future timeline

### Next 1-2 patches
- Add real Playwright click-through for the Orbit GUI, not just static browser smoke markers.
- Convert `/command-verify` into a direct ToolRegistry tool so all command contracts are callable from autonomous planning without command-handler fallback.
- Add a compact live “tool rationale” card to the GUI activity drawer.

### Next 3-5 patches
- Split the very large `core.py` command routing into route modules by area: GUI/voice, project, autonomy, validation, docker/sandbox.
- Split `tools.py` into tested tool groups: project tools, validation tools, repo/self tools, memory/database tools, external/sandbox tools.
- Add a per-project local code index cache that feeds `/project-patterns`, patch impact, and coding plans.

### Later integrations
- Add browser-use-style visual assertions and screenshot diffs.
- Add Mem0-style typed memory expiry/confidence/source fields.
- Add OpenHands-style full session transcript cards under assistant messages.
- Add optional MCP/sidecar adapters only after policy and permission gates are stable.

## Validation
See packaged validation artifacts for startup validation, Doctor, command verification, browser smoke, bug review, regression sweep, architecture audit and tool-awareness audit.
