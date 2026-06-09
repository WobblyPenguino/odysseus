# Agent Tool Use Guide

1. Inspect first: `/project-open NAME`, `/tree`, `/read`, `/search`.
2. Reproduce: `/run-project`, `/auto-verify`, or `/verify COMMAND`.
3. Investigate logs: `/investigate-logs`.
4. Use small repairs first: `/surgical-repair exact error`.
5. Create helper tools only when repeated inspection is useful: `/tool-create ...`, `/tool-view`, `/tool-test`, `/tool-run`.
6. Improve current project: `/improve-project ...`.
7. Propose source improvements: `/propose-improvements`, then optionally `/self-improve` for small safe patches.
8. Backtrack only when targeted repair fails: `/backtrack`.
