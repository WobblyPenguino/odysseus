# Nova Odysseus GUI Workbench Plan

Generated: 2026-06-01 18:53:50
Web UI present: **True**

## Layout to emulate/adapt
- Left command rail: permanent compact launcher for Nova workspaces
- Wide sidebar: chats/projects/models/commands remain searchable
- Centre: chat plus active workspace surface
- Right: status, voice, editor, receipts and transparent diff
- Modal/fullscreen surfaces: documents, cookbook, compare, research reports and tasks
- Mobile mode: collapse wide sidebars into the rail and keep touch targets large

## Rail / panel mapping
- **Suite** -> `/nova-odysseus-suite` -> Feature coverage
- **Gates** -> `/nova-tool-permissions` -> Privilege table
- **Cookbook** -> `/nova-cookbook whatif ram=32 vram=16 => coding` -> Hardware-aware model fit
- **Compare** -> `/nova-compare plan improve Nova => qwen2.5-coder:7b, qwen2.5:14b` -> Blind model test
- **Docs** -> `/nova-docs list` -> Documents vault
- **Notes** -> `/nova-notes list` -> Quick notes
- **Tasks** -> `/nova-tasks list` -> Task checklist
- **Skills** -> `/nova-skills` -> Reusable behaviours
- **Memory** -> `/nova-memory-vault audit` -> Memory export/audit
- **FastAPI** -> `/nova-fastapi-plan` -> Architecture migration

## Current UI markers
- `odysseus_workbench_panel`: True
- `workbench_panel`: True
- `launcher_buttons`: True
- `rail_buttons`: True
- `fastapi_plan_button`: True

## Next GUI panels
- real JSON-backed docs panel
- blind compare scoreboard
- model cookbook cards
- skills/memory import-export modal
- settings tab for permission gates
