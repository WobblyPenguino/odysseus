# Nova v55.3.141 clean Studio GUI hotfix

This patch rebuilds the visible Nova web shell around a cleaner Studio layout inspired by VS Code, ChatGPT and Odysseus while preserving the same backend routes and command flows.

## User-visible changes

- Central chat is the primary workspace again.
- Left panel focuses on controls, command search, projects, files and tools.
- Right panel remains state/output/voice/receipts, but duplicate visual noise is reduced.
- Odysseus voyage cards and validation dock are still present in the source/workbench, but no longer dominate the default screen.
- Horizontal resize bars are still functional but visually quiet.

## Safety

No broad backend refactor was made. This is a UI-shell and test-contract patch. Existing routes, project tools, voice pipeline, activity polling and workbench actions remain wired.
