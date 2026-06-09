# Nova Odysseus Feature Suite

Source: uploaded odysseus-main.zip and public README feature map
Generated: 2026-06-01 18:31:37
Coverage: **13/13** (100.0%)

## Commands added or mapped
- `/nova-odysseus-suite`
- `/nova-tool-permissions`
- `/nova-cookbook`
- `/nova-compare`
- `/nova-docs`
- `/nova-notes`
- `/nova-tasks`
- `/nova-skills`
- `/nova-presets`
- `/nova-memory-vault`
- `/nova-integration-gates`

## Feature coverage
- **Chat / provider switching** — `native_plus_mapped` via `/providers, /provider, /ollama-multi, /openrouter-model`
  - Adaptation: Nova keeps its existing provider commands and exposes this suite as the feature coverage audit.
- **Agent tools + guarded autonomy** — `native_plus_new_gate` via `/autonomous, /nova-self-apply, /nova-tool-permissions`
  - Adaptation: Nova already has autonomous/tool routing; this patch adds an Odysseus-style privilege policy table and command checker.
- **Hardware-aware model cookbook** — `implemented` via `/nova-cookbook`
  - Adaptation: Nova now detects RAM/CPU/NVIDIA VRAM where available, accepts what-if hardware hints, ranks local model choices and prints install/serve guidance without auto-downloading.
- **Deep research reports** — `native_plus_mapped` via `/research, /nova-deep-research, /nova-odysseus-suite`
  - Adaptation: Nova keeps its existing research engine and documents the Odysseus deep-research target in the suite manifest.
- **Blind model comparison** — `implemented` via `/nova-compare`
  - Adaptation: Nova now creates blind comparison packets and stores comparison/vote receipts under the workspace runtime directory.
- **Documents-first editing** — `implemented` via `/nova-docs`
  - Adaptation: Nova now has a workspace document vault with create/list/read/suggest/export commands and explicit AI-suggestion sidecars.
- **Memory and skills** — `implemented` via `/nova-memory-vault, /nova-skills, /memory, /remember`
  - Adaptation: Nova now adds skill library CRUD/export and memory-vault audit/export commands on top of its existing memory commands.
- **Email triage scaffold** — `safe_scaffold` via `/nova-email-plan`
  - Adaptation: Nova now exposes a no-secret integration checklist and triage schema. It does not connect to mail until credentials and explicit consent are configured.
- **Notes and tasks** — `implemented` via `/nova-notes, /nova-tasks`
  - Adaptation: Nova now stores notes/tasks as workspace JSON with add/list/search/done/export operations.
- **Calendar scaffold** — `safe_scaffold` via `/nova-calendar-plan`
  - Adaptation: Nova now provides an .ics-oriented integration plan and event schema without silently syncing external calendars.
- **Mobile/PWA readiness** — `implemented_as_audit` via `/nova-mobile-plan`
  - Adaptation: Nova now has a mobile/PWA readiness checklist command that maps required files and regression checks for the current web UI.
- **Extras: uploads, vision, image, themes, sessions, web search, presets, 2FA style hardening** — `native_plus_scaffold` via `/attach-file, /image-analyze, /image-generate, /chats, /nova-presets, /nova-theme-plan, /nova-auth-plan`
  - Adaptation: Nova already has file/image/chat/web search surfaces; this patch adds presets plus theme/auth hardening plans.
- **Backup, vault and webhooks** — `safe_scaffold` via `/nova-integration-gates, /webhook-status`
  - Adaptation: Nova now has a privileged-integration gate command that classifies risky actions before implementation or use.

## Local Nova signals
- `nova_modules`: 140
- `docs_markdown`: 23
- `has_verified_self_apply`: True
- `has_eval_packs`: True
- `has_research_lab`: True
- `has_file_context`: True