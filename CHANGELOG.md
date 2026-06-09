## v55.3.168 — Project-state continuity memory

- Added project-state snapshots under `docs/NOVA_PROJECT_STATE_LATEST.*` and `logs/project_state/`.
- Added `/project-state`, `/project-state --json`, and `/project-state --next`.
- Connected latest release-readiness, task evidence, package manifest, host-only checks, limitations, packaging permission, and safest next action.
- Added continuation handling for `continue`, `again`, `continue where this left off`, and next-improvement prompts.
- Added autonomous continuity guard output and release-readiness project-state checks.
- Added docs and focused project-state continuity tests.

## v55.3.167 — Task execution evidence and autonomy hardening

- Added a lightweight task contract system for broad and risky prompts.
- Added task evidence JSON/Markdown receipts under `logs/task_evidence/`.
- Added repeated-failure guard support for command execution.
- Improved `/verify` summary behavior without making default verification slow.
- Added `/task-contract` and `/task-evidence` command routes and help metadata.
- Extended `/release-readiness --full` with task execution/evidence/autonomous safety checks.

## v55.3.165 - Real-machine model calibration release candidate

- Added `/model-calibration` / `/model-calibrate` and `python -m winlocalassistant.model_calibration` for host Ollama/GPU probes and optional real prompt timing on the Windows Nova PC.
- Hardened `/release-readiness --full` with clearer plain-English evidence categories for chat fallback, model health, GUI runtime, help, tools, scheduler, autonomous, remote/API, legacy continuity, project contracts and packaging permission.
- Reworked the browser runtime evidence path so it starts a real Nova server, verifies `/chat`, renders Nova in Chromium, checks composer/help/drawer/live-activity geometry, and saves screenshot/JSON evidence without relying on Node Playwright.
- Added strict direct request-contract checks for one-file Python, browser games, PowerShell scripts and Nova source edits.
- Added docs/PHONE_ACCESS_TAILSCALE.md for safe phone access over LAN or Tailscale.
- Updated build identity/cache markers to v55.3.165 while preserving v55.3.164 legacy continuity anchors.

## v55.3.164 - Legacy continuity regression guard patch

- Added `/legacy-continuity-audit`, `/legacy-regression-lock` and `/feature-regression-guard`.
- Added deterministic historical capability anchors for Odysseus workspace surfaces, voice/wake reliability, resize/live-activity protection, pipeline observability, command verification, provider routing, remote access, validation and emergency chat/help stability.
- Added `tests_legacy_continuity_guard.py` so future patches must keep valuable older features or explicitly replace them.
- Updated build identity/cache markers to `legacy-continuity-regression-guard-v1`.

# emergency-chat-help-layout-stability-v1

- Replaced default `/help` wall with concise grouped/searchable help; legacy list remains `/help-full`.
- Added deterministic instant replies for greetings/capability checks so chat feels responsive when the local model times out.
- Added final GUI stability layer for composer, Live Activity, cluttered drawers, popup cleanup and `fix UI`.
- Added runtime browser diagnostic `window.NovaEmergencyStability.diagnose()`.


## v55.3.164 — remaining-tasks-arcade-help-runtime-v1 (2026-06-09)

- Added Nova Arcade registry and local-only playable `Nova: System Runner`.
- Added grouped/searchable backend command help via `/command-help [query]`.
- Added arcade GUI runtime and header launcher.
- Updated build identity/layout storage/cache markers so stale browser builds are visible.
- Added tests for arcade metadata, command help, GUI runtime markers and old smoke routes.

## v55.3.164 - SubQ/NVIDIA/local provider runtime hardening

- Added provider abstraction and status/route/test/queue commands for Ollama, llama.cpp, vLLM, SGLang, local Gemma-style servers, SubQ, NVIDIA NIM and OpenRouter.
- Kept Nova local-first: remote providers require explicit internet permission and BYO keys.
- Added provider route bar/permission wording in the GUI and dry-run provider validation plans.
- Added docs/SUBQ_NVIDIA_PROVIDER_INTEGRATION_V55_3_163.md from the uploaded PDFs.


## v55.3.164 - research-backed efficiency audit and focus GUI

- Added `/nova-efficiency-audit` to write a deterministic local-model, GUI and code-health audit.
- Added focus workspace GUI mode to reduce drawer/panel clutter and keep chat central.
- Added research-backed validation notes for Ollama, local inference optimization, Playwright visual checks and structured tracing.
- Synced version metadata, launcher text and validation markers.

## v55.3.164 - GUI/startup/media route hardening
- Fixed START_NOVA_HERE.bat/PowerShell launcher version drift and stale server reuse.
- Added /api/version and launcher stale-instance detection so the browser cannot silently connect to an older Nova server on port 8766.
- Hardened .venv setup: invalid partial venvs are repaired, pip self-upgrade is skipped during startup, and dependency install uses the venv Python directly.
- Rewired media commands into help/command palette/quick controls and added regression tests for /media-status, /image-plan, /video-storyboard and /video-package.
- Added calm workspace GUI defaults: narrower drawers, right/activity panels closed on first v55.3.164 load, less noisy legacy panels, and a clearer version badge.

## v55.3.160 - Media pipeline refinement

- Added unified `/media-status` for image/video readiness and clean next steps.
- Added `/image-plan` for style-aware prompt variants, seeds, safety metadata and negative prompts before expensive image generation.
- Added `/video-storyboard` for storyboard SVG, shotlist CSV and keyframe prompt export.
- Added `/video-package` to write manifest, preview AVI/HTML, storyboard, shotlist, validation report, image prompts and FFmpeg assembly plan in one resumable folder.
- Added focused regression tests for the new media command/tool surface.

## v55.3.159 - Clean GUI and Docker validation hardening

- Added a clean workspace GUI mode with visible version badge, reduced drawer clutter, safer panel z-index ordering, and user-toggle persistence.
- Docker validation now reports a clear skipped/degraded result when Docker Desktop/Linux engine is unavailable instead of looking like a broken Nova validation failure.
- Added regression tests for GUI cleanup/version visibility and Docker unavailable handling.


## v55.3.159 - Self-repair and Ollama queue hardening

- Added bounded mistake-learning/self-repair commands and tools.
- Recorded failed tool results into Nova's local mistake memory.
- Queued same-model Ollama calls so multi-agent work cannot collide with the local model.
- Added regression tests for Ollama queueing, self-repair command routing and safe repair validation.

## v55.3.159 - Natural research, truthfulness and spoken personality hardening

- Fixed plain-English research/search requests so Nova uses its internet/research tools when the user asks to search, research, look up, or produce a report.
- Added `/internet-search` and `/search-web`.
- Added seeded source discovery for World War II and Neil the Seal/Tasmanian seal research so the research path still has useful public sources when generic search fails.
- Fixed theme extraction so interactive clarification text does not pollute project names, acceptance terms, or game themes.
- Improved spoken reply summaries so speech sounds more natural and does not cut off halfway through a sentence.
- Added tests for research routing, internet search surface, dog-game theme extraction, `/compare` alias, and voice summary stability.

## v55.3.159 - Autonomous mission, media proof and safe subagent hardening

- Keeps `/autonomous start` running in continuous mission mode unless the user asks for `--finite`, a cycle limit is reached, or `/autonomous stop` is sent.
- Preserves the Ollama prompt lock while adding subagent-safe planning for parallel diagnostics and serialized LLM calls.
- Adds a high-spec local profile for the upgraded PC model stack and longer validated timeouts/context budgets.
- Adds GUI affordances for internet/status/authority controls without silently granting unrestricted shell access.
- Stabilises Live Activity scroll behaviour so refreshes do not yank the view while a user is reading older events.
- Keeps manifest-first video proof generation and includes deterministic local preview artifacts.

## v55.3.155 - Start Here launcher and extracted-tree setup hardening

- Added `START_NOVA_HERE.bat` as the obvious Windows entry point for setup and launch.
- Added `SETUP_NOVA_FIRST.bat` and `README_START_HERE.txt` for first-run users.
- Hardened `start_nova_best_models.ps1` with `-Setup`, `-SkipValidation`, venv creation, dependency install attempts, better path detection, Ollama warming and clearer validation output.
- Extended layered validation with launcher obviousness/startup file checks so releases fail fast if the setup path drifts.
- Preserved v55.3.154 release hardening, v55.3.153 integration review, v55.3.152 orchestration foundation, v55.3.151 UI/video guards and v55.3.150 audit continuity.

## v55.3.154 - Regression research launcher hardening

- Synchronized core version metadata, README, release manifest and web UI visible strings.
- Added `start_nova_best_models.ps1` and `start_nova_best_models.bat` for extract-and-run Windows setup.
- Delegated legacy launchers to the new better-model startup path.
- Expanded `python -m winlocalassistant.validate --all` with version-sync, launcher, CLI smoke and GUI smoke checks.
- Deduplicated model-registry missing-model suggestions.
- Excluded logs and transient runtime folders from release packaging.
- Added release-sync and launcher regression tests.

# Changelog

## v55.3.150 - Repo research radar and codebase sanity audit

- Added expanded repo-inspired capability manifests for OpenTelemetry/Langfuse/AgentOps-style observability, SWE-agent-style issue repair, AgentGit-style checkpoint branching and Agno-style control-plane permissions.
- Added `/codebase-sanity-audit` to scan Nova for large modules, risky raw writes, blocking sleeps, broad exception density, command/tool drift and rewrite candidates.
- Added `/repo-research-radar` to connect repo research, installed manifests, repo assurance and codebase sanity into one future-timeline view.
- Hardened several small state-writing modules to use `safe_io` atomic writes instead of raw `Path.write_text`.
- Extended repo-upgrade assurance so it validates the expanded manifest/tool/command surface.


## v55.3.149 - Repo readiness gate and direct command verification

- Added `/repo-upgrade-assurance` and `/future-timeline` to verify repo-inspired integrations as one connected system.
- Added direct ToolRegistry-backed `/command-verify` so autonomous/idle tool planning can select command verification instead of relying on a core-only branch.
- Audits installed manifests, routes, tools, browser smoke assets, voice/GUI observability markers, and autonomous/idle tool-plan wiring.
- Preserves the v55.3.148 autonomous/idle tool-awareness orchestration, pipeline manifests, session evidence, typed memory inventory and Orbit GUI protections.

Repo-inspired readiness gate and direct command verification

## v55.3.149 Repo-inspired capability manifests, session evidence and memory inventory hotfix - 2026-06-02

- Added `winlocalassistant/pipeline_manifests.py` with repo-inspired capability contracts for checkpointed patches, session evidence, browser GUI smoke, typed memory audit, voice state machine and local code indexing.
- Added `winlocalassistant/session_evidence.py` to summarize run/tool/file/model evidence from activity and model logs.
- Added `winlocalassistant/memory_inventory.py` to audit typed memory stores, assistant databases and project-state health.
- Added `/pipeline-catalog`, `/pipeline-manifest`, `/session-evidence`, `/run-evidence`, `/memory-inventory` and `/memory-audit` commands.
- Added planner routing for repo-integration prompts to run manifest/evidence/validation stages instead of unrelated project generation.
- Preserved the prior pipeline preflight, browser smoke, live timeline and project-pattern memory behavior.

## v55.3.149 - Autonomous/idle tool-awareness orchestration

- Added a repo-inspired tool-awareness broker that combines pipeline routing, capability manifests, autonomy capability matching and the actual registered ToolRegistry surface.
- Added `/tool-awareness`, `/tool-awareness-audit`, `/autonomous-tool-plan` and `/idle-tool-plan`.
- Autonomous cycles now record a tool-awareness plan before acting and include it in cycle evidence.
- Idle cycles now inspect the same tool-awareness plan before selecting proposal/repair tools.
- Added regression coverage for capability broker output, command wiring and background-mode awareness.


## v55.3.144 Orbit live-activity, voice cue, project routing and readability hotfix

- Fixes voice-ready cue visibility and audio unlock fallback.
- Routes broad project-review and validation follow-ups to diagnostics instead of creating unrelated new apps.
- Improves Orbit live activity readability, live working updates, chat timestamps, terminal evidence indicators and drawer clarity.

## v55.3.144 Orbit voice/file workspace hotfix - 2026-06-02

- Forced the Orbit GUI shell to be active on first load and changed the service worker to network-first shell caching so refreshes do not show the old GUI first.
- Removed the stale Command ready artifact panel and replaced it with a quiet composer/status update.
- Added per-chat mute, rename/edit and delete controls in the Odysseus-style chat drawer and chat tabs.
- Made spoken replies concise and voice-triggered by default instead of reading long technical chat output aloud.
- Added a larger top-left Nova state pill showing Ready, Listening, Thinking and Speaking, with speaking pulse.
- Added a displayed voice challenge phrase, lock-on-load behaviour, testing bypass, and a foreign-voice lock guard when an enrolled voice profile does not match.
- Added an Odysseus-style draggable file window for opening, editing, saving, downloading and running/opening project files.
- Routed current-project verification follow-ups like “test each individual functionality” to deterministic project QA tools instead of starting a new project build.
- Added a deterministic file-string-search script fallback so requests for a script that looks for a string inside file types no longer produce an unrelated file-creator project.

## v55.3.142 Orbit workspace drawer hotfix - 2026-06-02

- Changed Orbit drawers from overlay popups into layout-reserving docked panels so left/right views push the chat/composer into remaining free space.
- Replaced the saved-chats popup with an Odysseus-style Chats drawer panel that supports search, switch, rename and delete without covering the chat.
- Docked Live Activity inside the chat column instead of letting it cover the conversation.
- Added a mini pulsing Nova avatar beside the top-left logo, with listening/thinking/speaking states and speech flashing.
- Strengthened the Hey Nova ready chime and restored voice/wake speech handoff so spoken replies work during voice-mode flows.
- Added a Theme customizer for primary/secondary/background/panel/text colours and chat width instead of a vague theme toggle.
- Added an Odysseus-style Nova apps panel mapping Chat, Deep Research, Compare, Cookbook, Library/Files, Voice/State, Activity and Theme to existing safe Nova routes.

## v55.3.141 Odysseus Orbit GUI shell hotfix

- Rebuilt the default Nova Web UI into an Odysseus-inspired Orbit shell instead of another small cosmetic CSS pass.
- Added a compact left app rail, centred chat canvas, dark grid background, slide-out tools drawer, slide-out voice/output inspector, and slide-up live activity drawer.
- Preserved existing backend IDs/routes so projects, files, AI tools, Hey Nova, live activity, transparent output, workbench windows and validation commands keep working.

## v55.3.141 Clean Studio GUI shell hotfix - 2026-06-02

- Rebuilt the visible Web UI shell into a cleaner VS Code / ChatGPT-style Studio layout while preserving existing Nova routes, workbench windows, voice controls, projects, tools, activity and inspector panels.
- Hid the large Odysseus voyage/validation deck from the default screen and replaced it with a compact Studio action hub.
- Softened centre resize rails so they remain draggable but no longer dominate the interface with large coloured labels.
- Reduced duplicate voice waveform clutter by keeping voice state in the right inspector and compact status line.

## v55.3.141 - Voice cue, resize rails, activity scroll and coding-flow hardening

- Fixed the attached failure pattern where a request to test Nova's functionality could be routed into project generation and trigger local-model JSON/timeout loops.
- Added a Hey Nova ready cue, wake-listener pause while Nova is thinking/speaking, and softer no-speech handling.
- Expanded centre-panel resize rails across banner/workspace/subframe/activity panels and preserved Live Activity scroll position during polling.
- Added early deterministic fallbacks for simple coding requests after local model parse/timeout failures and a broader verified-simple-app review-loop guard.
- Added `/user-feedback-tests` and `tests_v55_3_141_voice_resize_coding_flow.py` to protect these behaviours.

## v55.3.140 - Safe subprocess logging and Odysseus validation command dock

- Fixed the broader regression failure where `nova_odysseus_suite.py` used a direct binary append log handle outside `safe_io`. The launcher now uses `open_binary_append_handle()` so append-mode file access stays centralised.
- Added an Odysseus-style validation command dock to the main workspace with one-click fill buttons for release hygiene, architecture audit, eval packs and patch-impact checks.
- Added `tests_v55_3_140_safety_validation_dock.py` to protect the new GUI markers and safe-I/O launcher contract.
- Continued release metadata sync for v55.3.140 without removing existing FastAPI/Odysseus routes, panels, sandbox tabs or voice controls.

## v55.3.139 - Odysseus layout sanity and release metadata cleanup

- Added a hoverable Odysseus-style voyage workspace deck to the main GUI with direct cards for Chat & Agents, Cookbook, Deep Research, Compare, Documents, Notes & Tasks, Memory and Themes.
- Fixed release/version drift by syncing `winlocalassistant.__version__`, `README.md`, `CHANGELOG.md`, `RELEASE_MANIFEST.json`, web UI visible strings and release hygiene tests.
- Added a regression test that checks the new deck markers, route buttons and current version visibility while preserving the existing FastAPI/Odysseus workbench routes.
- No broad refactor: existing left/right panels, sandbox tabs, voice controls, FastAPI bridge and command safety gates are preserved.

## v55.3.135 - Odysseus adaptation and verified self-apply

- Added `winlocalassistant/nova_verified_changes.py`.
- Added `/nova-self-apply [plan|preview|apply] [CHANGE_ID] [--confirm]`.
- Added low-risk built-in changesets for Odysseus adaptation reporting and verified self-change flow documentation.
- Added `tests_nova_verified_self_apply_v55_3_135.py`.
- Preserved existing `/patch-*`, idle auto-apply and eval-pack flows while making self-application real, receipt-based and rollback-aware.

## v55.3.134 - Nova eval packs and deterministic upgrade checks

- Added `/nova-eval-packs` with core, release, agent, coding, voice and all packs.
- Added deterministic command-level upgrade checks so Nova can validate routed capabilities after refactors.
- Kept checks read-only/profile-report oriented to avoid damaging project code during verification.

## v55.3.134 - Version and documentation sync

- Bumped package version to `55.3.134`.
- Synced `README.md`, release metadata, UI version labels, and version docs.
- No functional changes beyond version/documentation consistency.

## v55.3.132 - Capability drift and feedback-loop lab

- Added `winlocalassistant/nova_capability_drift_lab.py`.
- Added `/capability-drift-audit`, `/feature-preservation-contract`, `/agent-feedback-loop`, `/behavior-fuzzer-plan`, and `/local-spec-search`.
- Added `tests_nova_capability_drift_v55_3_132.py` and smoke/system/completion-audit integration.
- Kept the patch read-only and additive: no wake-word/audio, autonomous, shell, rollback, scheduler, project generation or live model runtime behaviour changes.

## v55.3.131 - Route resilience lab, guardrail memory and local runtime sentinel

## v55.3.131 - Improvement assurance lab

- Added `winlocalassistant/nova_improvement_assurance_lab.py`.
- Added `/improvement-assurance`, `/test-impact-graph`, `/patch-quality-score`, `/success-claim-audit`, and `/regression-bisect-plan`.
- Added `tests_nova_improvement_assurance_v55_3_131.py` and smoke/system/completion-audit integration.
- Kept the patch read-only and advisory: no changes to voice/audio, autonomous execution, shell execution, rollback, scheduler, provider config, project generation, or live model runtime switching.


- Added `winlocalassistant/nova_route_resilience_lab.py` with read-only route resilience, tool health, guardrail memory, context router and local runtime sentinel planners.
- Added `/route-resilience-plan`, `/tool-health-map`, `/guardrail-memory`, `/context-router-policy` and `/local-runtime-sentinel` plus aliases.
- Added `tests_nova_route_resilience_v55_3_130.py` and wired it into smoke, Nova system test and completion audit slices.
- Preserved v55.3.124-v55.3.129 analytics, inspiration, coding, agent-upgrade, reliability and deep-research features; no wake-word/audio/autonomous/shell/rollback execution paths were changed.

## v55.3.129 - Deep research advisory lab, topology, trace, local stack and voice pipeline review

- Implemented the Nova Improvement Report's low-regression advisory module as `winlocalassistant/nova_deep_research_lab.py`.
- Added `/agent-topology`, `/trace-observability`, `/local-stack-advisor`, `/verifier-ladder`, `/tool-namespace-plan` and `/voice-pipeline-review` with matching aliases.
- Added deterministic plans for specialist handoffs, trace/redaction contracts, Ollama-vs-llama.cpp model stack choice, runtime-aware verification ladders, conditional tool namespaces and Jarvis-style modular voice review.
- Added `tests_nova_deep_research_v55_3_129.py` and wired it into `tests_smoke.py`, `nova_system_test.py` and the completion-audit regression slice.
- Preserved v55.3.124-v55.3.128 analytics, inspiration, coding, agent-upgrade and reliability features; no wake-word/audio/autonomous/shell/rollback execution paths were changed.

## v55.3.128 - Reliability lab, impact tests, context maps and local model benchmarking

- Added `/repo-context-map`, `/patch-impact-plan`, `/permission-scope-review`, `/local-model-benchmark` and `/tool-contract-audit`.
- Added `winlocalassistant/nova_reliability_lab.py` as a read-only diagnostics/planning layer inspired by context engineering, behaviour-driven coding-agent tests, permission/scope research and local-model benchmarking.
- Added targeted regression planning so Nova can choose tests based on changed files instead of guessing or always running unrelated checks.
- Added a ToolRegistry/core command contract audit that distinguishes real broken wiring from existing legacy config/monkey-patch patterns.
- Added `tests_nova_reliability_v55_3_128.py` and wired it into `tests_smoke.py`.
- Preserved v55.3.124 analytics/scheduler/webhook tools, v55.3.125 inspiration tools, v55.3.126 multi-runtime coding tools and v55.3.127 agent upgrade tools.

## v55.3.127 - Agent upgrade lab, context budget and regression continuity

- Added `winlocalassistant/nova_agent_upgrade_lab.py`.
- Added `/agent-upgrade-radar`, `/context-budget`, `/coding-behavior-tests`, `/ollama-runtime-profile` and `/upgrade-regression-audit`.
- Added request-specific behaviour checks so coding outputs are validated against what the user asked for, not only syntax.
- Added compact local-model context budgeting to reduce prompt bloat and context-window failures.
- Added read-only Ollama Modelfile/runtime profile drafts for task/hardware-specific local model use.
- Added a patch continuity audit covering v55.3.124 analytics/scheduler, v55.3.125 inspiration workflow intelligence, v55.3.126 multi-runtime coding and v55.3.127 upgrade lab tools.
- Updated smoke tests and Nova system-test regression slices to include the latest functional tests.

## v55.3.126 - Multi-runtime coding capability and local model performance

- Added `winlocalassistant/nova_coding_capabilities.py` for deterministic coding execution plans, coding capability audits, and task-specific local-model performance guidance.
- Added `/coding-plan`, `/coding-audit`, and `/local-model-performance` slash commands.
- Upgraded project brief and acceptance contracts so Java, Python, Node, PowerShell and FastAPI prompts keep the correct runtime/files instead of being downgraded into browser-only HTML projects.
- Added Python, Java and PowerShell syntax/sanity checks to project verification while preserving existing browser/JS checks.
- Expanded runtime/project detection and run instructions for `.py`, `.js`, `.java`, `.ps1` and browser projects.
- Added `tests_nova_coding_v55_3_126.py` and included it in the smoke suite.

## v55.3.125 - Inspiration-backed Nova workflow intelligence

- Added read-only `/inspiration-radar`, `/tool-context-pack`, `/handoff-plan`, and `/improvement-preflight` commands.
- Added `winlocalassistant/nova_inspiration_engine.py` to rank inspiration-backed improvements, trim tool context for local models, build deterministic handoff plans, and preview patch risk/validation requirements.
- Wired the new commands through the ToolRegistry and chat slash-command router without changing wake-word, shell, idle, autonomous, backup, rollback, or mutation behaviour.
- Added `tests_nova_inspiration_v55_3_125.py` and included the direct functional subset in `tests_smoke.py`.

## v55.3.124 - Analytics, proposal ledger and scheduler command integration

- Completed the previously interrupted analytics/proposal/scheduler feature chain without regressing the v55.3.123 wake-handoff and layout fixes.
- Wired `/analytics`, `/performance-report`, `/webhook-status`, `/list-tasks`, `/proposal-ledger-view`, `/completed-improvements` and `/anti-repeat-check` through the ToolRegistry.
- Fixed the broken tool registration path where new methods were accidentally nested inside an unrelated helper function.
- Hardened analytics empty-state rendering so zero-metric dashboards do not fail on missing cost/token aliases.
- Fixed cron step parsing for scheduler expressions like `*/5 * * * *` and added malformed-cron rejection before task creation.
- Added guarded scheduler callbacks so safe registered tools can be scheduled while obvious high-risk source-editing/shell commands are refused for unattended execution.
- Added `tests_improvement_features_v55_3_124.py` and included it in the smoke suite.


## v55.3.123 - Wake handoff, desktop launcher, layout reclaim and build loop guard

- Fixed the Hey Nova handoff so the always-on listener pauses while the command listener captures the full post-wake request.
- Added continuous post-wake capture with a silence gate to avoid cutting off phrases like "what's going on".
- Added Windows desktop voice launcher helper scripts and non-interactive `NOVA_START_CHOICE` startup support.
- Reclaimed hidden left/right panel space in the main CSS grid.
- Hardened game creation verification to accept `rectsHit` collision helpers and avoid unnecessary post-pass LLM review loops.
- Added `tests_v55_3_123_wake_handoff_build_loop.py`.

# v55.3.122 - Voice Profile Lock + Communication Centre

- Added browser-side voice-profile lock with testing bypass so spoken commands start locked on load.
- Added fuzzy Hey Nova wake matching for common recognition errors like `hanover`, `hangover`, `hova`, `noah`, `novah`, and `nover`.
- Reworked wake flow into wake-detect then post-wake request capture so commands are sent only after the request finishes.
- Replaced the right-panel improvement state with a communication centre.
- Isolated Live Activity to the current browser/server session by default so stale previous operations do not look active after restart.

# v55.3.121 - Voice Reliability, Security and Layout Hardening

- Fixed repeated interim speech fragments causing duplicated transcripts.
- Added coherent voice transcript screening and silence-gated command submission.
- Added local voice login/command gate, optional password, remember unlock and lock/unlock controls.
- Added AI speech selector, volume/rate/pitch controls, Test AI voice and Stop AI speech.
- Disabled automatic permanent idle resume unless explicitly opted in again.
- Added VS Code-style resize gutter polish and stronger scroll containment for activity/run panes.
- Added tests_v55_3_120_voice_reliability_security.py and v120 docs.

v55.3.121 voice reliability, Hey Nova voice activation, voice auth/login, no auto-idle resume and VS Code-style resize gutters

# v55.3.121 - Autonomous Cockpit Reasoning Timeline

- Added compact scrollable autonomous cockpit UI.
- Added current autonomous reasoning/status notes and self-validation summaries.
- Added scrollable prior-thought timeline per autonomous run.
- Added scrollable subwindows for cycle explanation, cycle plan and latest autonomous events.
- Added `/autonomous run GOAL` and `/autonomous go GOAL` aliases.
- Added `tests_v55_3_119_autonomous_cockpit_reasoning.py`.
- Preserved v55.3.118 unified voice/orb UI, v55.3.117 completion audit and v55.3.116 Nova system test.

# v55.3.121 - Completion Audit + Massive-Test Hardening

- Added `/completion-audit`, `/previous-task-audit`, and `/task-completion-audit`.
- Added a completion audit GUI quick command and command-palette entry.
- Hardened `/massive-test --confirm` so quick mode covers latest v117-v106 regressions, Nova contract checks, and previous-task completion audit before optional legacy groups.
- Kept `/massive-test --confirm full` available for the slower legacy stack.
- Added tests in `tests_v55_3_117_completion_hardening.py`.
- Preserved `/nova-system-test`, GUI Nova full test, batch option 3, Hey Nova labels, and the legacy `data-ui-overhaul="v55.3.115"` marker.

# Nova v55.3.121 - Nova full-system one-button validation

Adds `/nova-system-test`, GUI quick command wiring, batch-file option 3, and staged capability checks for chat routing, coding fallback, GUI/JS contract, voice/persona, Jarvis bridge policy, startup validation and regression slices.

# v55.3.115 - Persona + Local Model Harness Upgrade

- Added Nova persona profile, custom chat window, personality sliders and persona prompt addendum.
- Added voice command audit, local model optimiser and iterative agent harness tools.
- Injected persona/local-model/harness contracts into build/repair context.
- Wired persona/local model controls into the left action cockpit and settings panel.
- Hardened feature continuity and validation matrix checks for the new surfaces.

# v55.3.89 Autonomous/Idle Mission Intelligence

- Added mission dashboard, tool-choice trace, cycle scoring, repetition guard, background-only idle settings, mistake log/regression seed commands and detailed autonomous reports.
- Autonomous/idle can now use patch-queue-first and mistake-learning signals to avoid repeating useless cycles.

## v55.3.89 - Quality/runtime/reliability suite

- Added build quality, browser runtime, model reliability, patch queue, GUI cockpit v2, voice diagnostics, templates, preview, feature readiness, error translator, support report, docs index, regression-to-test, new PC tuning and mistake-learning commands.
- Extended mega-test and autonomy capability coverage.

# Changelog

## v55.3.89 - Custom tool routing and feature-regression fix
- Route natural self-tool requests to guarded custom-tool creation instead of generic app planning.
- Add deterministic read-only project_health_snapshot fallback for broad useful-tool requests.
- Restore feature-audit markers for voice/file-card/model-context/browser hygiene after planning-panel UI changes.


## v55.3.89 - Bug review hardening and formatter integration

- Added `/bug-review`, `/bug-hunt`, `/bug-sweep`, and `/error-review`.
- Added autonomy/tool-registry access for bug review.
- Render ToolRegistry `markdown` fields directly in chat output.
- Added structured logging for ToolRegistry exceptions.

## v55.3.89 - Whole-codebase review and CLI diagnostics

- Added a whole-codebase review engine and commands.
- Added direct one-shot command execution through `python app.py /command`.
- Exposed the review capability to idle/autonomous planning.
- Added regression coverage for command/tool integration and codebase review reporting.

## v55.3.75 - Improvement proposal completion loop

- Added `/improvement-proposals`, `/improvement-cycle --confirm`, `/completed-improvements`, and `/improvement-status`.
- Added deterministic improvement proposal ranking and completion reports.
- Exposed improvement proposal completion as idle/autonomous tools and a capability.
- Added regression-memory seed reporting for repeated Nova failures.
- Added v55.3.75 regression tests.

## v55.3.75 - Weakspot and autonomy hardening

- Added /weakspot-audit, /error-hunt, /stability-audit and /weakspots.
- Added weakspot/error-hunt as a first-class idle/autonomous capability and ToolRegistry tool.
- Hardened custom tool validation against workspace-escape-prone Path attributes.
- Replaced several silent exception paths with structured/debug logging or recoverable warnings.
- Added v55.3.75 regression tests.

## v55.3.75 - Major autonomy, validation, repair, trace and connector upgrade

- Added prompt-to-test compiler and contract validation.
- Added candidate tournament scoring and diff/failure reports.
- Added surgical repair v2 diagnostics, plans, verify/replay/rollback guidance.
- Added trace timeline/errors and replay command.
- Added safe MCP connector risk/permission commands.
- Added autonomous mission planner v2.
- Added local model output coach commands.
- Added environment profiles, new-PC benchmarks, project-state database and regression memory.

## v55.3.75 - Comprehensive code review hardening

- Added release package hygiene checks to prevent `__pycache__`, `.pytest_cache` and `.pyc` artifacts from shipping.
- Hid pytest/temp/cache paths from the GUI file-focus panel and live communication snapshot.
- Added a comprehensive review regression suite covering version labels, packaging cleanliness and UI focus filtering.
- Preserved sandbox/dependency compatibility labels for release-gate and massive-test continuity.

## v55.3.75 - Significant upgrade radar and optional installer and voice device selector

- Added `/upgrade-radar`, `/upgrade-plan`, `/significant-upgrades`, and `/optional-upgrades` to rank major Nova improvements, including optional downloads, checks, risks, and setup commands.
- Added a browser microphone device selector plus Refresh mics control so Sony WH-1000/WH-1000XM Bluetooth users can choose the active headset microphone instead of only relying on the Windows/browser default.
- Added explicit handling for selected-device failures such as stale Bluetooth device IDs and unavailable headset microphones.
- Added optional dev tooling scaffolds: `pyproject.toml`, `.pre-commit-config.yaml`, and `requirements-dev.txt` for Ruff/pre-commit release gates when the user chooses to install them.
- Preserved sandbox/dependency compatibility wording in visible release labels and README.

## v55.3.75 - Failure-mode hardening and voice microphone preflight

- Added browser microphone preflight and Mic test controls for voice mode.
- Added SpeechRecognition/getUserMedia/device-enumeration diagnostics with Chrome/Edge and Sony WH-1000 Bluetooth headset guidance.
- Prevented repeated idle test proposals from turning into no-op patches by recording a docs completion entry when the generated test already exists.
- Kept sandbox/dependency wording in visible version labels for release-gate compatibility.
- Revalidated syntax, smoke, voice/intent, release label, idle, GUI JS and feature-continuity suites.
## v55.3.75

- Fixed project creation crash when model output wrote into a sibling folder such as Tinyappproject while the active project was Tinyapp.
- Hardened sandbox startup diagnostics so Docker CLI present but Docker Desktop daemon stopped gives an actionable message instead of a raw npipe failure.
- Prevented diagnostic text such as “Dodge Game default appeared...” from forcing game-domain validation during repair prompts.
- Added Codex repair prompt and sandbox/project hardening regression tests.

## v55.3.75

- Added startup dependency checking in `start_windows_assistant.bat` via `winlocalassistant.dependency_check`.
- Added `/dependency-check` and `/massive-test --confirm` commands.
- Added a one-click confirmed massive system test button in the GUI left rail.
- Added `winlocalassistant/system_test.py` for sequential monitored validation runs and reports.
- Updated feature audit, Nova Doctor and release gate defaults for dependency/system-test coverage.

## v55.3.75
- Fixed stale version assertions that prevented full-suite validation from collecting cleanly.
- Added requested-feature audit compatibility alias for direct module/API use.
- Added full-validation hardening tests covering version consistency, release-gate defaults and feature-audit exports.
- Updated Nova Doctor/release-gate defaults so current validation uses the latest hardening checks.

## v55.3.75
- Hardened browser-console behaviour by serving `/favicon.ico` with no-content instead of 404.
- Stopped Web Audio beeps from creating AudioContext autoplay warnings before a user gesture.
- Preserved chat-session titles when saving/restoring browser transcript sessions.
- Ensured custom quick buttons can execute sequential commands split by newline or `;;`.
- Added a regression test for GUI console hygiene and remaining requested-feature behaviour.

## v55.3.75
- Validated the accumulated GUI/audio/project-memory/Docker/autonomous changes from recent builds.
- Fixed `/image-generate` so it refuses cleanly when no real backend is configured, rather than creating an SVG placeholder from the real-generation command.
- Kept `/image-draft` as the explicit SVG placeholder path.
- Fixed deterministic vague-game candidate refinement so older game-domain validation accepts the generated fallback.
- Preserved compatibility markers for older GUI layout tests while retaining the newer taller/resizable Live Activity panel.
- Kept the Linux sandbox Python-ready default so recreated Linux sandboxes can run Python tooling.

## v55.3.75
- Added persistent backend conversation store and commands for multiple chats.
- Added release checklist command, API, and GUI popup.
- Added Playwright browser smoke-test scaffold for send/audio/quick-command/activity/changelog flows.
- Integrated project memory into build/edit prompts and saved project facts after successful changes.
- Added tests for conversation storage, release checklist, Playwright scaffold, and project-memory prompt integration.

## v55.3.75
- Added Integration Radar for evaluating future Nova integrations beyond Docker.
- Added `/integration-radar`, `/next-integrations`, and `/integration-plan`.
- Added checks for Git, Playwright/Node, Ruff, mypy, Semgrep, pre-commit, uv and ripgrep availability.
- Nova Doctor now checks the integration radar module and command routes.
- Added GUI buttons for integration planning.

## v55.3.75
- Added SHA256 hash locking for Docker patch validation and promotion.
- `/docker-promote-patch` now refuses promotion if the saved patch file differs from the validation report hash.
- Added `/release-gate`, `/validate-release`, and `/preflight-release` for pre-zip validation.
- Nova Doctor now checks patch hash-locking guardrails.
- Added regression tests for patch integrity and release gate behaviour.

## v55.3.75
- Added Nova doctor self-diagnosis commands: `/nova-doctor`, `/doctor`, `/bug-scan`, and `/improvement-plan`.
- Added static checks for Python syntax, version consistency, required modules, command routing, web UI inline JavaScript safety, web UI JS parsing when Node is installed, and regression-test presence.
- Added Nova doctor controls to the web UI.
- Fixed README visible version/label drift.
- Hardened the plus-menu attach-file example by moving it to `data-command`.

## v55.3.75
- Added less strict trusted lab sandbox policy mode.
- Added `/sandbox-policy`, `/sandbox-less-strict`, and `/sandbox-trusted-lab`.
- Trusted lab mode enables network, authorised-lab mode, and sandbox autonomy together for owned/local lab work.
- Kali tools no longer require per-command approval in trusted lab mode.
- Host escape and destructive root patterns remain blocked.
- GUI now exposes less strict/balanced/strict policy controls and displays policy status.
- Added regression tests for less strict sandbox policy behaviour.

## v55.3.75
- Added guarded promotion for Docker-validated patches.
- Added `/docker-promote-patch`, `/docker-patch-promote`, and `/autonomous-promote-patch`.
- Autonomous can now explicitly promote a previously validated patch using `--promote-patch RUN_ID`.
- Promotion writes reports, captures pre-promotion git status/diff, reruns live apply checks, and attempts rollback if local validation fails.
- Docker GUI now includes patch promotion controls and history-based Promote buttons.
- Added regression tests for patch promotion and autonomous parser coverage.

## v55.3.75
- Added a cohesion engine combining self-awareness, architecture audit, Docker validation history and iterative development protocol.
- Added `/cohesion-report`, `/architecture-cohesion`, `/validation-ladder`, `/iteration-plan` and `/development-loop`.
- Integrated a read-only cohesion self-map step into autonomous cycles.
- Extended self-awareness and architecture audits to understand the new cohesion/validation modules.
- Added regression tests for cohesion reports and command routing.

## v55.3.75
- Added Docker patch-only validation using copied workspaces and `git apply --check`.
- Added `/docker-validate-patch` and `/docker-patch-validate`.
- Added Docker GUI patch-validation command filler.
- Added patch validation metadata to Docker history.
- Added regression tests for patch validation success, patch rejection and command routing.

## v55.3.75
- Added Docker validation history with `/docker-history`.
- Added Docker validation run cleanup with `/docker-clean`.
- Added recent validation history to `/docker-status` and the Docker GUI panel.
- Added quick/tests/gui Docker validation profiles for easier user testing.
- Hardened Docker workspace copying to exclude local runtime/cache folders.
- Added regression coverage for history, cleanup, command wiring and GUI controls.

## v55.3.75
- Integrated Docker validation into autonomous cycles as pre-action and post-action validation gates.
- Added Docker readiness/image preflight so autonomous mode skips cleanly when Docker is missing, stopped, or the validation image is not local.
- Added `/autonomous status` reporting for last Docker validation and skip reasons.
- Added `--no-docker` / `--skip-docker` handling for autonomous goals.
- Added regression tests for autonomous Docker validation edge cases.

## v55.3.75
- Added Docker project validation backend with `/docker-validate` and `/docker-test`.
- Docker validation copies the source tree into a temporary Nova Docker run workspace instead of mounting the real project directly.
- Added validation report persistence under `~/.nova/docker_runs`.
- Docker status and GUI now show the last validation result.
- Added GUI button to validate Nova in Docker.

## v55.3.75
- Integrated optional Docker diagnostics from the Nova Docker design notes.
- Added `/docker-status`, `/docker-diagnostics`, `/docker-ps`, `/docker-smoke`, and `/docker-help`.
- Added a Docker tab in the GUI plus `/api/docker-status`.
- Added robust missing-Docker and daemon-offline handling.
- Removed a duplicate redirect response in the web UI file viewer.
- Added `tests_v55_3_25_docker_diagnostics.py`.

## v55.3.75
- Fixed the web UI Send button not working after the pending sandbox permission UI was added.
- Replaced broken nested JavaScript quotes in pending permission buttons with safe data-command handlers.
- Hardened dynamic custom-tool buttons to use dataset handlers instead of interpolated inline JavaScript calls.
- Added regression tests for the broken approval-button pattern and web UI script safety.

## v55.3.75
- Added visible pending sandbox permission workflow for Kali/security commands that need authorised-lab or network approval.
- Added `/sandbox-approve`, `/sandbox-cancel`, `/sandbox-pending`, and related aliases.
- Sandbox status and the GUI now surface pending permission requests with approve/cancel controls.
- Approval now enables only the required flags and reruns the original pending command.
- Running sandboxes are recreated when network mode changes, preventing stale `none` networking after approval.
- Added regression tests for permission state, status visibility, GUI controls, and local/public network target detection.


## v55.3.75

- Auto-opened the browser UI from `start_windows_assistant.bat` in Browser UI mode.
- Restored missing `checkModelSetup()` GUI hook.
- Stabilised Live Activity minimize/expand layout.
- Preferred `nova-kali-tools:latest` over the bare Kali image when available.
- Recreated stale Kali containers if running from the wrong image.
- Made sandbox-focused autonomous goals run direct sandbox checks instead of generic slow proposal loops.

# v55.3.75 - GUI activity/autonomous/sandbox status repair

- Added Docker/Podman-backed Linux and Kali sandbox manager with safe defaults.
- Added `/sandbox-status`, `/sandbox-linux`, `/sandbox-kali`, `/sandbox-exec`, `/sandbox-autonomy`, `/sandbox-network`, and `/sandbox-authorized-lab`.
- Added GUI top tabs for General, Linux Sandbox, Kali Sandbox, and Sandbox Settings.
- Added sandbox runtime/status API endpoints for the localhost Web UI.
- Added sandbox-aware autonomous planning so higher-risk efficiency experiments can be routed into a disposable sandbox when enabled.
- Added policy gates: no network by default, read-only project mount, dropped capabilities, command audit logging, and high-risk Kali tools blocked unless authorised lab mode is enabled.
- Added regression tests in `tests_sandbox_integration_v55_3_16.py`.

# v55.3.8 - Whole-codebase bugfix and integrity hardening

- Directly audited full v55.3.7 codebase and patched command-routing, autonomous loop guard, research/database report collision, quality-gate count, datastore reliability and code-review false-positive issues.
- Added regression tests for the fixed behaviours.

## v55.2.9 - Local model context packs

- Added automatic compact Nova context packs to local model calls.
- Context packs include workspace/project markers, active file/photo context, assistant communication box state, recent activity, recent audit previews, model roles and command capabilities.
- Added `/model-context` preview/toggle command.
- Added context-pack tests and command contract coverage.

## v55.2.7 - Repair audit and autonomous project reliability

- Added deterministic `/repair-audit` / `/code-repair-audit` command for broad bug/repair analysis across the active workspace.
- Added `code_repair_audit` internal tool so autonomous cycles can inspect syntax, duplicate definitions, swallowed broad exceptions, oversized functions, release cache artifacts and autonomous safety guard markers before mutating files.
- Integrated the repair audit into autonomous base checks and project repair/improvement sequences.
- Hardened autonomous mutation gating so timed-out base checks or failed repair audits prevent risky build/edit steps in that cycle.
- Added regression tests for repair-audit reporting, command routing and report generation.

## v55.2.2 - Autonomous freeze protection

- Added bounded autonomous tool timeouts so heartbeat/model/check steps cannot leave autonomous mode visibly stuck forever.
- Improved `/autonomous start` status so the UI immediately shows the worker is starting instead of stale idle state.
- Added visible between-cycle cooldown status and progress timestamps.
- Added tests for autonomous timeout recovery and start-state telemetry.

## v55.2 - Easy image context and uploaded-photo analysis

- Fixed the main uploaded-photo workflow bug: web-uploaded images are stored as shared context outside the workspace, but `/image-analyze` only accepted workspace paths. It now accepts `latest`, `context:ID`, bare context IDs, and uploaded filenames.
- Added GUI shortcuts for analyzing the latest uploaded photo and generating deterministic SVG image drafts.
- Added safer upload validation, including 25 MB upload limit checks and data-URL base64 handling.
- Hardened image metadata handling by correcting JPEG SOF parsing and adding SVG dimension parsing.
- Added regression tests for uploaded-image context resolution and `/image-analyze latest`.

## v55.1 - File and photo context sharing

- Added local file/path prompt context via `/attach-file` and `/context-files`.
- Added Web UI file/photo context upload endpoint and composer controls.
- Added image metadata handling and deterministic SVG draft generation via `/image-generate`.
- Added tests for shared file context, image context and SVG generation.

## v55.1 - UX command planning and game syntax hardening

- Fixed generic/custom browser game fallback JavaScript syntax so generated games pass `node --check`.
- Added chat quality-of-life controls: Enter sends, Shift+Enter creates a newline, and Up/Down recall command history.
- Improved active planning choices so users can click choice buttons instead of typing `/reply 1`.
- Improved LLM status display with a human-readable health summary, active model cards, and installed-model cards.
- Added refresh spinner feedback for project/file refresh buttons.
- Added closable Created Output cards.
- Added compact Live Activity mode so collapsed activity still shows current run/activity summary.
- Added project multi-select UI with confirmation-aware bulk delete buttons.

## v55.1 - UX command planning and game syntax hardening

- Added `model_health.py` for non-blocking model dependency/degraded-mode assessment.
- Added `/model-health` to explain local model readiness, prompt/cooldown state, provider configuration and recommended fixes.
- Added `/command-timeout status|SECONDS` so shell/verification timeout policy is visible and configurable.
- Extended `/llm-status` with a structured `model_health` payload.
- Added command-contract coverage and regression tests for the new commands.

## v54.3 - report hygiene and UI duplicate cleanup

- Added evidence-based Nova self-awareness reports with capability inventory, safety boundaries, known limitations and recent autonomous state.
- Added `/self-awareness`, `/self-aware` and `/capability-audit`.
- Added Web UI quick action for self-awareness.
- Restored `/quality-dashboard` chat routing coverage.
- Updated visible version metadata and documentation to v54.3.

## v54.1 - autonomous journal redaction and resilience

- Redacted secrets from autonomous sequence journal argument summaries, including API keys, tokens, authorization headers and bearer-token strings.
- Made latest journal lookup resilient to corrupt newest JSON journals by falling back to the newest readable journal.
- Added regression tests for journal secret redaction and corrupt-journal recovery.
- Updated visible version metadata and documentation to v54.1.

## v54.0 - autonomous sequence journaling and review observability

- Added `autonomous_journal.py` for durable per-step autonomous sequence journals.
- Autonomous sequenced runs now record executed, skipped, blocked and failed steps with watcher status, reasons, durations and summaries.
- Added `/autonomous-journal` to show the latest run journal.
- Added tests for journal writing, summary counts and latest-journal loading.
- Updated GUI/version text to v54.0.

## v54.0 - continuity audit and interactive reply hardening

- Added a feature-continuity audit test to catch accidental loss of roadmap modules, commands and docs across future releases.
- Added documentation summarising continuity across the v51-v53 roadmap.
- Hardened interactive `/reply` handling so numeric and lettered options such as `c` resolve to the full selected option instead of being passed through as a meaningless single letter.
- Improved generic interactive-run goal enrichment so broad category choices become more useful build goals.
- Added parser regression coverage for model JSON containing Windows paths and JavaScript escaped single quotes.
- Updated GUI/version text to v54.0.

## v53.5 - planning dashboard integration and watcher redaction

- Connected `/planning-dashboard` to the richer task decomposition engine so it now reuses normalized text, intent confidence, ambiguity/clarification decisions and success criteria instead of maintaining a separate shallow splitter.
- Hardened action watcher logging with recursive secret redaction for keys and token-bearing strings.
- Updated version metadata, GUI visible version text and documentation.
- Added regression coverage for planning dashboard/task-decomposition integration and watcher redaction.

## v53.4 - OpenClaw-inspired watcher, tool catalogue and interaction learning

- Added `action_watcher.py` to score proposed actions, require approval, block protected or repeated-risk actions and append watcher logs.
- Added `tool_catalog.py` and upgraded `/tool-catalog` with risk, verification and fallback metadata.
- Added `interaction_learning.py` so user feedback/outcomes can be stored as local JSONL lessons.
- Added `planning_dashboard.py` and `/planning-dashboard` to show intent, confidence, subtasks, watcher decision and verification plan.
- Added tests for watcher, catalogue, lessons and planning dashboard.
- Updated GUI visible version text to v53.4.

## v52.9 - quality dashboard and review improvements

- Added `/quality-dashboard` for a combined Nova/project readiness report.
- Added `winlocalassistant/quality_dashboard.py` to combine version, workspace, autonomous memory, project iteration and runtime-probe signals.
- Added markdown/JSON dashboard reports under the Nova profile directory.
- Added a Web UI quick action and command-palette entry for quality dashboard generation.
- Fixed a visible typo in the active two-way planning panel.
- Updated GUI visible version text to v52.9.

## v52.8.1 - panel restore controls

- Fixed collapsed left, right and Live Activity panels so they can be expanded again using visible restore tabs.
- Added regression tests for panel restore controls and visibility CSS.

## v52.8 - review hardening and packaging hygiene

- Verified the v52.7 roadmap changes with compile, smoke and pytest suites.
- Hardened project iteration log writing to append safely instead of read/rewrite cycles.
- Added packaging hygiene guardrails so runtime profiles, pytest cache and Python bytecode are excluded from release zips.
- Updated README install instructions to the current release package name.
- Added regression tests for project-iteration append behaviour, README version text and release hygiene expectations.

## v52.7 - project iteration reports and repair loop hardening

- Added persistent project iteration logs and human-readable verification reports.
- Hardened repair loops against repeated identical model repair proposals.
- Created PROJECT_ITERATION_LOG.jsonl and PROJECT_VERIFICATION_REPORT.md for generated projects.
- Preserved verified, rollback-aware, no-auto-self-improve safety posture.

## v52.6 - runtime probe and project interaction verification

- Verified existing roadmap features through smoke and pytest suites, including intent planning, task decomposition, project quality scoring, acceptance contracts, generic game generation, autonomous failure memory, command suggestions, and request-intent guards.
- Added robust profile-directory fallback so tests and sandboxed runs do not crash when `~/.nova` is read-only or partially owned by another process.
- Added a first-load GUI tutorial overlay using `localStorage` with highlighted sections for chat input, command launcher, avatar state, idle self-improvement, live activity, projects, files, editor, settings, and safety.
- Expanded GUI Settings controls to hide/show created outputs, Live Activity, avatar state, top quick actions, composer buttons, suggested command chips, and feedback buttons.
- Preserved safety: suggestion chips fill the input only; no auto-running destructive commands was added.
- Added tests for profile fallback and tutorial/settings UI hooks.

## v52.4 - Generic game generation and acceptance

- Added `winlocalassistant/game_design.py` to infer custom game type, objects, mechanics and acceptance requirements from arbitrary game prompts.
- Replaced non-dodge game fallback with a generic canvas-game generator that adapts title, objective, objects and README to the requested game instead of always using the Dodge template.
- Kept explicit Dodge Game support only when the user asks for a dodge game.
- Extended creation intent and acceptance contracts so named games such as fishing, maze, racing, clicker, platformer and other custom game requests require visible theme/mechanic evidence.
- Added `tests_game_design.py` and wired it into smoke testing.

## v52.3 - Project acceptance contracts and repair planning

- Added `winlocalassistant/project_acceptance.py` with request-specific acceptance contracts.
- Project quality scoring now includes explicit contract checks and repair plans.
- Creation mismatch reports now include missing behaviours and a surgical correction plan.
- Added `tests_project_acceptance.py` and wired it into direct smoke testing.

## v52.2 - Task decomposition, quality scoring and planning visibility

- Added deterministic task decomposition and intent confidence metadata.
- Added project quality scoring that combines request match, file completeness, behaviour evidence and verification checks.
- Added GUI planning visibility markup for active planning decisions.
- Fixed stale version consistency expectation in /test-all.

## v52.1 - Interactive intent planning and UI choice highlighting

- Added a two-way intent-planning gate for vague, misspelled, multi-task, or active-project-conflicting requests.
- Natural chat and `/do` can now pause before running tools, ask a multiple-choice planning question, highlight a recommended answer, and accept a custom reply.
- Added numbered `/reply 1` style option selection for active two-way runs.
- Updated the Web UI active-run panel so recommended choices are visually highlighted.
- Updated GUI/version documentation to v52.1.

## v52.0 - Developer-in-loop QA and UI feedback polish

- Added project-target decision logic to prevent unrelated new artifact requests from being silently mixed into the active project.
- Added a `project_target_decision` tool and planner hook so ambiguous current-vs-new project requests ask the user to choose.
- Strengthened behavioural checks for calculators and todo apps with clearer clear/backspace, equals/compute, delete, and complete/done requirements.
- Added richer created-output metadata in successful project results and clearer web UI output cards.
- Added UI feedback controls and settings toggles for command suggestions, composer buttons, quick buttons, and feedback controls.
- Improved auto-refresh hints and refresh calls after generated outputs appear.
- Added regression tests for project-target decisions and UI feedback/output metadata.

## v51.3 - Autonomous memory and behavioural verification hardening

- Added schema-versioned, atomic autonomous failure memory saves with corrupt-memory archiving.
- Added memory compaction so stale failure/cooldown records do not grow indefinitely.
- Broadened autonomous failure classification for invalid input and tool crashes.
- Added stronger behavioural project-contract checks for calculators, todo apps and games.
- Updated project quality verification so syntax/static checks are not enough for common generated apps.
- Added tests for robust autonomous memory and behavioural project verification.

## v51.2 - Coding engine and autonomous verification hardening

- Added pytest discovery configuration so `python -m pytest` now finds the repo's `tests_*.py` suites by default.
- Added autonomous failure-memory cooldown clearing when a previously failing action/tool/target later succeeds.
- Extended deterministic surgical fallback to repair obvious missing-colon Python syntax damage after verification errors.
- Strengthened project-quality checks for calculators and games, including digit/clear behaviour for calculators and restart/instruction requirements for games.
- Extended deterministic game repair to add restart behaviour and user instructions for generated canvas games when safe.
- Added regression tests for pytest discovery, stronger project-quality gates, Python surgical fallback, and autonomous cooldown clearing.

## v51.1 - Project quality and UI usability hardening

- Added stricter human-level acceptance checks for generated calculator, todo, and game projects so Nova no longer claims success for dead UIs, placeholder todo lists, or games without controls/objective/interaction.
- Strengthened the project quality review prompt so local-model repair must implement calculator operations, todo add/delete/complete behaviour, and real gameplay loops with controls, score/progress, collision/interaction and restart.
- Improved the Web UI created-output card: it now appears above Live Activity and describes the output file/project before the user opens or downloads it.
- Live Activity event details now open by default, while still allowing collapse.
- Added panel-local hide controls for left/right panels, a lightweight Settings panel for reducing top-button clutter, and an AI file-focus display in the Open File area.
- Added tests_project_quality_ui.py and wired it into direct smoke testing.

## v51 - Verified auto-apply with surgical fallback

- Added conservative surgical fallback helpers for tiny, deterministic fixes such as common documentation spelling mistakes, confusable semicolons, non-breaking spaces, and simple JavaScript semicolon damage.
- Extended explicit `/idle auto-apply run` so a low-risk report/docs patch that fails verification can attempt a surgical fallback, re-run verification, and either keep the repair or roll back to the backup.
- Auto-apply remains explicit, gated, and narrow: background idle still does not edit source files automatically, `/self-improve` is not called automatically, and only low-risk report/docs candidates are supported.
- Auto-apply reports now include a Surgical Fallback section plus JSON payload data describing whether fallback was attempted, changed files, and why.
- Improved deterministic browser-game fallback verification by avoiding a mandatory PowerShell-only manifest check, making CLI recovery tests portable while preserving Windows run commands.
- Added `tests_surgical_fallback.py` plus an integrated auto-apply rollback/fallback smoke test.

## v50 - Iterative candidate refinement

- Added recursive in-memory refinement for parseable but rejected local-model code candidates.
- Deterministic candidate edits now run before repeating full project-generation prompts.
- Added a focused candidate-edit prompt that includes the actual draft files and the exact validation failure.
- Accepted refined candidates preserve attempt history and refinement traces.
- This makes generation more iterative and less blocky when the local model returns imperfect but usable code.

## v49 - Reasoning skill and known-error recovery

- Added `/reasoning` and `/recovery-plan` for visible recovery diagnostics.
- Added `/recover-known-error` to retry the last error using remembered deterministic fixes.
- Plan execution now runs known-error recovery before giving up on a failed step.
- Known-error recovery classifies model timeouts, JSON parse failures, validation misses, JavaScript syntax/input-state bugs, browser reference issues and acceptance mismatches.
- Create-project failures can preserve and repair the best parseable rejected candidate instead of stopping immediately.

## v48 - CLI user testing and game build recovery

- Added deterministic browser-game fallback recovery for vague prompts such as `make a game` when the local model times out or returns unusable JSON.
- Added model attempt history for timeouts, parse failures, validation failures and accepted candidates.
- Preserved best parseable rejected candidates in diagnostics and project manifests.
- Added browser-game sanity checks for controls, score/state, collision/update loop and runnable file structure.
- Added deterministic repair for the common Pong `rightPressed`/`leftPressed` arrow-key state bug.
- Added `tests_cli_user_mode.py`, including direct CLI command testing and the `start_windows_assistant.bat` choice `1` path.

## v47 - Tool inputs, internet watchers, audio unlock and smarter routing

- Added friendly `/tool-run` parsing for JSON, `{plain text}`, bare text and simple `key=value` arguments.
- Added `/tool-help`, `/tool-inputs`, `/tool-pipeline`, `/safe-script-demo`, `/watch-topic`, `/topic-watchers`, `/topic-check` and `/internet-fetch`.
- Added explicit permission-gated topic watching; internet fetch/check commands require `/allow-internet on`.
- Added AI Toolbox inputs for tool name, args and pipeline JSON.
- Added browser audio unlock with a test beep and optional speech synthesis for avatar state changes and `/speak`.
- Fixed idle/autonomous lesson review so profile lessons are read through an internal tool instead of workspace-confined `/read`.
- Improved natural-language routing for "use a tool", "do something interesting" and "internet tool" requests.

## v44 Avatar-state sync and idle chat cycle telemetry

- Synced backend avatar mood/expression pairs.
- Added persistent idle-cycle chat bubbles.
- Added structured idle start/step/done/error events.
- Improved avatar styling and idle telemetry visibility.

## v43 - Idle agent, interrupt controls, avatar and richer telemetry

- Added idle self-analysis mode.
- Added confirmed interrupt command for stuck current tasks.
- Added Ollama multi-model report.
- Added avatar/status panel in the GUI.
- Added richer JSON/code formatting in chat.
- Improved model doctor so embedding-only models are not selected for normal chat.
- Improved model benchmark reliability.
- Added command/tool catalogue.

## v42 - Reliability harness and visual repair prep

- Added /test-all, model doctor, model benchmark, visual repair scaffold, known issues, self-improvement queue and project quality scoring.


## v45 - Self-guide, idle learning, avatar sync and no-timeout local prompts
- Fixed `/avatar` returning a transient working state that did not match the GUI.
- Added `/self-guide`, `/how-to-use`, and `/full-guide`.
- Added `/model-timeout status|off|SECONDS`; default local Ollama timeout is off/wait indefinitely.
- Fixed idle `APP_DIR` crash and added `IDLE_LESSONS.md` learning from idle failures.
- Idle cycles now review previous idle lessons before repeating maintenance work.

## v54.6.0 - Command contract and download hardening
- Added `winlocalassistant/architecture_audit.py` for module, docs, command-routing, version, testing and release-hygiene checks.
- Added `/architecture-audit` to write markdown/JSON architecture reports under the local Nova profile.
- Added architecture audit to command verification and the Web UI quick actions/command palette.
- Added regression tests for architecture-audit reports and command routing.

## v55.3.5 - CodeRabbit-style quality gates

- Added a local CodeRabbit-style quality gate with structured PR-review comments and pass/warn/block verdicts.
- Added `/code-quality-gate`, `/code-rabbit-review`, and `/review-gate` commands.
- Integrated the quality gate into autonomous base diagnostics and post-build/post-improvement verification.
- Added GUI quick action and regression tests for the new gate.

## v55.3.4 - Autonomous loop guard

- Added autonomous loop detection and no-progress tracking.
- Added repeated optional diagnostic skipping.
- Added repeated mutation blocking after no-progress cycles.
- Added finite-goal stopping so continuous autonomous mode does not redo completed tasks forever.
- Added regression tests for autonomous loop guard behaviour.

## v55.3.99 adaptive model requirements

This build adds a confirmable local model requirement/download planner so Nova can request missing Ollama models when a task needs stronger coding, chat, vision or embedding capability. New commands include `/model-readiness GOAL`, `/model-download-plan GOAL`, `/model-requirements GOAL` and `/model-install NAME --confirm`. Downloads are never started without explicit confirmation and the exact `ollama pull ...` command is shown first.
## 2026-06-09 — gui-autonomous-interaction-fix-v1

- Added browser-only GUI interaction overhaul module for right-panel blur prevention, stable Live Activity positioning, movable/resizable panels, non-invasive help dots, message navigation arrows, code boxes, searchable command help, local model status and autonomous guard overlay.
- Added behaviour rule commands: `/remember-behavior`, `/behavior-rules`, `/forget-behavior`.
- Added deterministic one-file script fallback for simple script requests when the local model is unavailable, preventing unrelated HTML/template scaffolds.
- Updated build identity/cache version to `gui-autonomous-interaction-fix-v1`.
- Added tests and docs for the new interaction layer and generation-scope safeguards.


## 2026-06-09 — runtime-usability-release-gate

- Added `/release-readiness --full` as the blocking release gate for chat/help/GUI/code/write/read/run, legacy continuity, scheduler/autonomous smoke coverage, zip hygiene and browser runtime usability.
- Made `/release-package` refuse to create a zip unless the latest release-readiness report is `PASS` unless explicitly forced for diagnostics.
- Added tiered model timeout defaults so normal chat can fall back quickly while code/autonomous work keeps longer waits.
- Replaced duplicated GUI command-help cards with the shared Python command registry and added `/release-readiness` to concise/searchable help.
- Added strict request-contract generation so one-file Python, browser game, PowerShell script and Nova-source-edit requests do not drift into the wrong scaffold.
- Added a real-browser runtime test that starts a Nova server, verifies `/chat`, renders Nova in Chromium, opens searchable help, forces activity/drawer states, and fails if the composer is covered.

## v55.3.166 — LLM-from-scratch inspired training lab

- Added `/llm-lab` commands for safe LLM training planning, dataset inspection and rough parameter/token/VRAM estimates.
- Added `python -m winlocalassistant.llm_training_lab` CLI report writer.
- Added release-readiness coverage so the lab cannot silently regress.
- Added docs explaining safe phone-independent local training experimentation and guardrails.
