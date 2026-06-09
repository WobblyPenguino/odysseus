# Nova v55.3.168

Legacy continuity anchor: Nova v55.3.164 runtime usability/release-readiness history is preserved for old validation checks.


Current package: `Nova_v55_3_168_project_state_continuity_memory_patch.zip`

Nova v55.3.168 adds project-state snapshots, continue/again continuity, release/task/package evidence linking, and autonomous continuity guards while preserving the v55.3.167 task execution evidence/autonomy hardening patch.


Nova v55.3.160 adds bounded mistake-learning self-repair, queued Ollama model calls for multi-agent stability, and preserves v55.3.157 research/voice truthfulness fixes.
## Start here on Windows

The most obvious and recommended way to set up and start Nova is now:

```bat
START_NOVA_HERE.bat
```

That batch file runs the better-model launcher, creates/uses `.venv` when possible, loads the upgraded-PC Ollama profile, checks Git/Node/Ollama paths, runs Nova's layered validation, and opens the web UI.

Alternative launchers:

```bat
SETUP_NOVA_FIRST.bat       rem setup/validate only
start_nova_best_models.bat rem normal web launch
```

PowerShell direct mode:

```powershell
Set-ExecutionPolicy -Scope Process RemoteSigned
.\start_nova_best_models.ps1 -Setup -Mode web
python -m winlocalassistant.validate --all
python app.py /version
```

This build keeps the upgraded-PC local model profile (`qwen3-coder:30b`, `gemma2:2b`, `llama3.2-vision:11b`, `nomic-embed-text:latest`), preserves the manifest-first video pipeline, and adds clearer extracted-tree startup/packaging validation so the release itself tells users what to run first.

# Nova v55.3.160 Repo research and codebase sanity audit hotfix

Current package: `Nova_v55_3_150_repo_research_codebase_audit_hotfix_20260602.zip`

## v55.3.150 Repo research radar and full codebase sanity audit

Nova v55.3.150 continues the future timeline by adding expanded repo-inspired manifests for agent observability, SWE-agent-style issue repair, AgentGit-style checkpoint branching and Agno-style control-plane permissions. It also adds `/codebase-sanity-audit` and `/repo-research-radar`, hardens several small state writers to use `safe_io` atomic writes, and verifies that autonomous/idle tool planning can see the new surfaces.

# Nova v55.3.160 Repo readiness gate and direct command verification hotfix

Current package: `Nova_v55_3_149_repo_readiness_command_verify_hotfix_20260602.zip`

This build continues the repo-inspired upgrade timeline by making command verification a direct ToolRegistry tool and adding `/repo-upgrade-assurance` plus `/future-timeline`. These commands verify that pipeline manifests, session evidence, browser smoke, typed memory inventory, project patterns, tool awareness, autonomous planning and idle planning are installed and wired together before claiming the upgrade is user-ready.

Repo-inspired readiness gate and direct command verification

## v55.3.149 Repo-inspired capability manifests, session evidence and memory inventory hotfix

- Added repo-inspired capability manifests adapted from the OpenMontage/OpenHands/browser-use/Mem0/LiveKit/Tabby upgrade plan without copying external code.
- Added `/pipeline-catalog [GOAL] [--write]` and `/pipeline-manifest ID` so Nova

Nova v55.3.149 adds autonomous/idle tool-awareness orchestration so background modes choose tools from pipeline manifests, capability maps and the live registry before acting. can choose named capability contracts before broad upgrades.
- Added `/session-evidence [RUN] [LIMIT]` for OpenHands-style tool/file/model/timeline evidence from Nova activity logs.
- Added `/memory-inventory [PATH]` for typed memory/database/project-state inventory checks.
- Added planner routing for repo-integration prompts so they run manifests, evidence, browser smoke, bug review and regression sweep instead of jumping straight into a model edit loop.
- Preserved the prior typed pipeline preflight, browser smoke, live timeline and project-pattern memory features.

# Nova v55.3.160 Repo-inspired capability manifests/session evidence upgrade hotfix

Current package: `Nova_v55_3_149_repo_readiness_command_verify_hotfix_20260602.zip`

## v55.3.144 Orbit live-activity, voice cue, project routing and readability hotfix

- Fixes voice-ready cue visibility and audio unlock fallback.
- Routes broad project-review and validation follow-ups to diagnostics instead of creating unrelated new apps.
- Improves Orbit live activity readability, live working updates, chat timestamps, terminal evidence indicators and drawer clarity.

# Nova v55.3.160 Orbit voice/file workspace hotfix

Current package: `Nova_v55_3_144_orbit_live_activity_voice_project_routing_hotfix_20260602.zip`

This hotfix keeps the previous startup/coding/voice fixes and tightens the Orbit workspace: first load uses the new shell without showing the old GUI, chat lists stay in the drawer, per-chat mute/edit/delete is available, spoken replies are concise, the Hey Nova ready chime is stronger, the state pill shows Ready/Listening/Thinking/Speaking beside the Nova logo, file viewing/editing/running opens in an Odysseus-style draggable file window, and project-verification follow-ups route to current-project tests instead of creating a new project.

# Nova v55.3.160

## v55.3.141 - Voice cue, resize rails, activity scroll and coding-flow hardening

- Added an Alexa-style two-tone ready cue immediately after the Hey Nova wake word is accepted.
- Paused the wake listener while typed, voice and `/reply` requests are still processing so Nova does not show Listening while it is thinking.
- Made centre-panel resize rails visible across banner/workspace/subframe/activity panels and preserved manual heights.
- Preserved Live Activity scroll position when refresh polling adds new events, avoiding jumps back to the newest run.
- Routed Nova functionality-test requests to QA/regression/doctor tools instead of project generation.
- Added early deterministic coding fallbacks for simple games/apps after local model JSON/timeout failures to reduce repeated long retries.
- Added `/user-feedback-tests` for a practical manual test-command checklist.

Install example:

```powershell
Expand-Archive .\Nova_v55_3_141_voice_resize_coding_flow_20260602.zip -DestinationPath .
```

## v55.3.139 - Odysseus layout sanity and release metadata cleanup

- Added a hoverable Odysseus-style voyage workspace deck across the main chat workspace so Chat & Agents, Cookbook, Deep Research, Compare, Documents, Notes & Tasks, Memory and Themes are visible without digging through the left panel.
- Synced release metadata, changelog and release hygiene tests with the actual package version.
- Preserved existing Nova command routing, side panels, sandbox tabs, voice controls and FastAPI bridge behaviour.

## v55.3.135 - Odysseus adaptation and verified self-apply

- Investigated Odysseus as inspiration for Nova's local-first AI workspace direction.
- Added `/nova-self-apply`, a verified self-change engine with plan, preview, apply, backup, validation, rollback and receipt steps.
- Added Odysseus-to-Nova adaptation docs and verified self-change flow docs.
- Added regression tests for the new self-apply planner/preview command path.
- Kept direct code mutation behind explicit named changesets and `--confirm`; no silent broad auto-editing.


## v55.3.134 - Version and documentation sync

- Bumped package version to `55.3.134`.
- Synced readable release metadata, UI labels, and top-level documentation.
- No runtime or feature changes beyond version/documentation alignment.


## v55.3.132 - Capability drift and feedback-loop lab

v55.3.132 adds a read-only capability preservation layer for Nova. It audits recent feature families for drift, writes feature preservation contracts, proposes measured agent feedback loops, drafts behaviour-driven fuzzing scenarios, and plans local spec search for on-device model/runtime tuning. Existing wake-word/audio, autonomous, scheduler, shell, rollback, project generation and live model runtime behaviour are preserved.

New commands: `/capability-drift-audit`, `/feature-preservation-contract`, `/agent-feedback-loop`, `/behavior-fuzzer-plan`, `/local-spec-search`.

Install example:

```powershell
Expand-Archive .\Nova_v55_3_141_voice_resize_coding_flow_20260602.zip -DestinationPath .
```


## v55.3.131 - Improvement assurance lab

- Added `winlocalassistant/nova_improvement_assurance_lab.py`.
- Added `/improvement-assurance`, `/test-impact-graph`, `/patch-quality-score`, `/success-claim-audit`, and `/regression-bisect-plan`.
- Added `tests_nova_improvement_assurance_v55_3_131.py` and smoke/system/completion-audit integration.
- Kept the patch read-only and advisory: no changes to voice/audio, autonomous execution, shell execution, rollback, scheduler, provider config, project generation, or live model runtime switching.


v55.3.131 adds a read-only route resilience lab for Nova. It turns current agent reliability ideas into deterministic plans for self-healing tool routes, command/tool health maps, context-aware guardrail memory, role-aware context routing and local-runtime sentinels. Existing wake-word/audio, autonomous, scheduler, shell, rollback, project generation and model runtime behaviour are preserved.

## New in v55.3.131

- `/route-resilience-plan GOAL` plans self-healing route/fallback edges for Nova workflows.
- `/tool-health-map [FOCUS]` audits command/tool route continuity without invoking tools.
- `/guardrail-memory GOAL => RISK NOTE` creates task-triggered guardrail rules that preserve benign utility.
- `/context-router-policy GOAL` gives each specialist role a compact context budget.
- `/local-runtime-sentinel GOAL => HARDWARE` drafts observable Ollama/local-model health checks and fallback profiles.

## Preserved from v55.3.129


- `/agent-topology GOAL` builds a router → context mapper → safety gate → builder → runner → verifier → reporter topology.
- `/trace-observability GOAL` drafts trace spans, captured metrics and redaction rules for Nova workflows.
- `/local-stack-advisor GOAL => HARDWARE` recommends Ollama vs llama.cpp, local model shortlist and explicit runtime options.
- `/verifier-ladder GOAL => RUNTIME` generates runtime-specific syntax, smoke and regression checks for Python, Java, Node, PowerShell, FastAPI and browser projects.
- `/tool-namespace-plan GOAL` groups Nova's large tool surface into conditional namespaces to reduce local-model prompt bloat without removing old commands.
- `/voice-pipeline-review FOCUS` reviews wake-word/STT/TTS/device/receipt boundaries using modular Jarvis-style assistant ideas without touching live audio.

## Preserved from v55.3.128

- `/repo-context-map GOAL` builds a compact, safe repo context pack for local/coding agents.
- `/patch-impact-plan FILES` selects targeted regression tests based on changed files.
- `/permission-scope-review GOAL => ACTIONS` flags broad, destructive, network, install or secret-adjacent patch plans before execution.
- `/local-model-benchmark GOAL => HARDWARE` drafts repeatable local Ollama benchmark profiles and prompts.
- `/tool-contract-audit` checks ToolRegistry/core command wiring and recent patch continuity.

## Preserved from v55.3.127

- `/agent-upgrade-radar [FOCUS]` shows safe, additive improvement ideas inspired by current agent/coding/local-model patterns.
- `/context-budget GOAL` chooses a compact, prompt-relevant file/tool context pack instead of sending the whole repo to a local model.
- `/coding-behavior-tests GOAL` creates behaviour-level acceptance checks for generated code, complementing syntax checks.
- `/ollama-runtime-profile GOAL => HARDWARE` drafts task/hardware-specific Ollama options and a Modelfile without running downloads or changing installed models.
- `/upgrade-regression-audit` checks that recent analytics, inspiration and multi-runtime coding patches remain present, routed and included in smoke/system tests.


## Jarvis-style bridge commands

Nova v55.3.115 adds a supervised bridge inspired by Jarvis-style daemon/sidecar assistants. Start with `/jarvis-bridge`, `/jarvis-status`, `/sidecar-policy`, and `/proactive-actions list`. Sidecar, shell, browser, screen and direct file-write authority are disabled by default and should remain gated by Nova receipts/validation.
 - Jarvis-style bridge and supervised sidecar policy

This release adds a feature-continuity/no-regression audit plus preservation-aware local model repair context so GUI redesigns and implementation attempts add or improve functionality instead of accidentally removing existing surfaces.

# Nova v55.3.160 - Sandbox daemon repair and project path hardening

## v55.3.113 GUI cockpit refinement

The Web UI now uses a central-chat cockpit with a compact focus strip, tabbed right inspector, restored Nova status refresh functions, readable/stale run management, and clearer stop/delete controls for live activity.

## v55.3.113 Interaction flow and no-regression verifier

This build adds a flow-verification layer so Nova can check that new commands are not just present in chat, but are also visible to ToolRegistry and the idle/autonomous capability catalog.

New commands:

```text
/flow-audit
/interaction-flow-audit
/interaction-pathways
/command-flow-verify
/learning-loop-audit
/flow-improvements
```

The audit checks build/repair/model/autonomous/regression/sandbox pathways and verifies that prompt contracts, candidate tournaments, iterative repair, build quality, browser runtime tests, model readiness, patch queue and mistake learning are wired together.


## v55.3.113 Quality, runtime, reliability, cockpit and learning suite

Version label: `v55.3.113 sandbox dependency, significant upgrade support, voice setup wizard, capability-aware mutable local-model blueprint candidate validation, prompt-to-test compiler, candidate tournament, surgical repair v2, trace timeline, GUI cockpit preview, visual regression, safe MCP connector permissions, autonomous mission planner, model output coach, environment profiles, benchmark migration, project state database, regression memory, comprehensive code review, package hygiene and one-command comprehensive Nova test, autonomous idle command access, guarded custom tool creation/execution, weakspot audit, completed improvement proposal implementation loop, regression sweep, functionality matrix, cross-feature no-regression hardening, improvement roadmap, proposal ledger, impact matrix and safe implementation pipeline, comprehensive user testing, whole-codebase review, direct CLI command execution, integrated codebase improvement audit, bug review hardening, markdown result formatting, stale planning panel close fix, custom tool routing fallback, build quality v3, browser runtime tester, local model reliability controller, patch queue, GUI cockpit v2, voice push-to-talk diagnostics, deterministic project templates, preview server, feature readiness, error translator, support report, docs index, regression-to-test generator, new PC tuning and mistake learning loop`

Adds build quality scoring, browser runtime testing, local model reliability/fallback controls, patch queue, GUI cockpit v2 preview, voice mode diagnostics, deterministic project templates, preview server guidance, feature readiness, error translation, support reports, docs/code indexing, regression-to-test seeds, new PC tuning commands and mistake-learning status.

# Nova v55.3.160 - Sandbox daemon repair and project path hardening

## v55.3.113 Custom tool routing and deterministic fallback

Natural requests like `now make yourself a useful tool` are routed to Nova's guarded custom-tool creator instead of the generic HTML app planning dialog. Broad self-tool requests can install a deterministic read-only `project_health_snapshot` helper without waiting for the local coding model.


## v55.3.113 Bug review hardening

Adds `/bug-review`, `/bug-hunt`, `/bug-sweep`, and `/error-review` for source/integration/release-hygiene bug scans. The formatter now renders ToolRegistry `markdown` payloads directly so new autonomy-accessible tools do not appear as raw JSON-only technical details.

## v55.3.113 Whole-codebase review and direct CLI commands

- Added `/whole-codebase-review`, `/review-codebase`, and `/comprehensive-code-review` to aggregate syntax, command/tool integration, release hygiene, docs/version consistency and improvement follow-ups.
- Added direct one-shot CLI command support, so diagnostics can run as `python app.py /whole-codebase-review` or `python app.py /nova-mega-test --confirm` without opening the GUI.
- Exposed the whole-codebase review capability to idle/autonomous planning so broad review/improvement prompts choose the right evidence-gathering tool before mutation.


## v55.3.113 Comprehensive review and package hygiene

This release adds a comprehensive review pass focused on preventing regressions in release packaging, browser UI focus display and validation hygiene. It removes runtime/cache artifacts from the distributed tree, adds regression checks for package cleanliness, and hides temporary pytest/cache paths from the live AI file-focus panel so the GUI does not look like it is editing test scratch files.


Version label: `v55.3.113 sandbox dependency, capability-aware mutable local-model blueprint candidate validation, prompt-to-test compiler, candidate tournament, surgical repair v2, trace timeline, GUI cockpit preview, safe MCP connector permissions, autonomous mission planner, model output coach, environment profiles, benchmark migration, project state database, regression memory, comprehensive code review, package hygiene and one-command comprehensive Nova test`

Version label: `v55.3.113 sandbox dependency, significant upgrade support, voice setup wizard, capability-aware mutable local-model blueprint candidate validation, prompt-to-test compiler, candidate tournament, surgical repair v2, trace timeline, GUI cockpit preview, visual regression, safe MCP connector permissions, autonomous mission planner, model output coach, environment profiles, benchmark migration, project state database, regression memory, comprehensive code review, package hygiene and one-command comprehensive Nova test, autonomous idle command access, guarded custom tool creation/execution, weakspot audit, completed improvement proposal implementation loop, regression sweep, functionality matrix, cross-feature no-regression hardening, improvement roadmap, proposal ledger, impact matrix and safe implementation pipeline`

Extended version label: `v55.3.113 sandbox dependency, significant upgrade support, voice setup wizard, capability-aware mutable local-model blueprint candidate validation, prompt-to-test compiler, candidate tournament, surgical repair v2, trace timeline, GUI cockpit preview, visual regression, safe MCP connector permissions, autonomous mission planner, model output coach, environment profiles, benchmark migration, project state database, regression memory, comprehensive code review, package hygiene and one-command comprehensive Nova test, autonomous idle command access, guarded custom tool creation/execution, weakspot audit, completed improvement proposal implementation loop, regression sweep, functionality matrix, cross-feature no-regression hardening, improvement roadmap, proposal ledger, impact matrix and safe implementation pipeline`

## v55.3.113 Improvement roadmap and proposal ledger

This build adds `/improvement-roadmap`, `/improvement-impact`, `/implement-improvements --confirm`, and `/proposal-ledger` so Nova can propose high-value improvements, rank implementation impact/risk, complete safe roadmap artifacts, and avoid repeating completed proposal work.

## v55.3.113 Significant upgrade radar and optional installer

Use `/upgrade-radar` to see the next high-value Nova improvements and whether they require optional downloads. Use `/optional-upgrades` to review allowlisted downloads and `/upgrade-install NAME --confirm` only after checking the exact command. This build also includes optional dev-tool scaffolding:

```text
py -m pip install -r requirements-dev.txt
pre-commit install
pre-commit run --all-files
ruff check winlocalassistant tests_*.py
```

These downloads are optional. Nova still runs without Ruff, pre-commit, Playwright, Docker or heavy image packages.

Voice mode now has a microphone selector next to the composer. Use **Mic test**, then **Refresh mics**, then choose the active Windows input device. For Sony WH-1000/WH-1000XM headsets, Windows may expose a separate headset microphone; choose that input in Windows Sound settings and then refresh the Nova mic list.


This build adds a full codebase integrity audit on top of the existing quality gate, research, database, autonomous loop guard, efficiency profiler and image backend checks.


This build adds deterministic efficiency profiling, timing/power-estimate reports, real image backend checks, local model context packs, deterministic repair auditing and stronger autonomous project reliability checks so Nova can inspect bugs, release hygiene and safety gates before applying project changes.

Install example:

```powershell
Expand-Archive .\Nova_v55_3_131_improvement_assurance_lab_20260601_053000.zip -DestinationPath .
cd .\Nova
python app.py
```

Useful new commands:

- `/docker-status` - show Docker CLI, daemon, Compose, WSL, containers, images and raw diagnostics.
- `/docker-ps` - list Docker containers from Nova.
- `/docker-smoke` - run a disposable Python container smoke test.
- `/docker-help` - show Docker/Nova integration guidance.
- `/action-watch ACTION` - evaluate action risk before execution.
- `/tool-catalog` - show risk, verification and fallback metadata for Nova tools.
- `/interaction-lessons` - show local lessons; add text to record a lesson.
- `/planning-dashboard GOAL` - inspect intent, subtasks, watcher decision and verification.
- `/autonomous-journal` - show the latest durable autonomous sequence journal.
- `/architecture-audit` - inspect architecture continuity, docs, command routing and release hygiene.
- `/model-health` - summarise local/remote model readiness and degraded-mode advice.
- `/command-timeout status|SECONDS` - inspect or set shell/verification command timeout.


## Useful commands

```text
/idle status
/idle once investigate logs and propose safe improvements
/idle start self-analyse when quiet and propose safe improvements
/idle stop
/interrupt-current
/interrupt-current --confirm
/ollama-multi
/command-catalog
/avatar
/memory
/remember TEXT
/knowledge
/learn-errors
/reasoning
/recover-known-error
/speak TEXT
/tool-help
/tool-run big_bold_reply => {hey}
/tool-pipeline [{"tool":"tool_run","args":{"name":"html_reference_checker","args":{"subdir":"."}}}]
/safe-script-demo run something interesting
/watch-topic local AI => https://hnrss.org/newest, https://arxiv.org/rss/cs.AI
/topic-watchers
/topic-check local AI
/model-doctor
/model-benchmark
/code-review
/code-quality-gate
/quality-progress
/repair-audit
```

## Recommended model setup

```powershell
ollama serve
ollama pull qwen2.5-coder:7b
ollama pull llama3.2:3b
ollama pull llama3.2-vision:11b
```

## Notes

Nova uses one active local LLM prompt at a time for reliability. Ollama may keep multiple models loaded in memory, but Nova avoids overlapping model calls unless a future expert mode explicitly enables it.

Internet access remains off by default. Run `/allow-internet on` before `/internet-fetch` or `/topic-check`.


## v50 highlights

- Parseable but rejected local-model output is now treated as an editable draft.
- Nova performs deterministic in-memory candidate edits before asking for another full generation.
- If deterministic edits are insufficient, Nova asks a focused “edit this candidate” prompt with the actual files and failure reason.
- Candidate refinement traces are stored in attempt history and activity logs.
- This reduces repeated same-prompt retries and supports more iterative file-building behavior.

## v49 highlights

- Adds a visible reasoning diagnostic command with `/reasoning` and `/recovery-plan`.
- Adds `/recover-known-error` for the last failure.
- Plan execution now tries known-error recovery before giving up or jumping to heavier backtracking.
- Known-error recovery classifies repeated failure signatures, applies deterministic remembered fixes, verifies the same project, and only escalates when needed.
- Creation failures can preserve and repair the best parseable rejected candidate when that is safer than stopping.

## v48 highlights

- `make a game` now has deterministic browser-game fallback recovery when the local model times out or returns unusable JSON.
- Build attempts now preserve timeout, parse, validation and accepted-attempt history in logs and project manifests.
- Browser-game verification checks for controls, score/state, collision/update loop and runnable files.
- Common generated Pong bugs such as missing `rightPressed`/`leftPressed` declarations and arrow-key listeners are repaired deterministically.
- `tests_cli_user_mode.py` drives CLI mode as a real user, including the batch-file choice `1` path.

## v47 highlights

- `/tool-run` accepts strict JSON, `{plain text}`, bare text and simple `key=value` inputs.
- `/tool-help`, `/tool-inputs` and the AI Toolbox form show custom tool inputs and examples.
- `/tool-pipeline` can run bounded sequential safe tool calls and stops on failure.
- `/safe-script-demo` gives real local standard-library output for "do something interesting" style requests.
- `/watch-topic`, `/topic-watchers`, `/topic-check` and `/internet-fetch` add explicit permission-gated internet/topic watching.
- The GUI has an explicit Enable audio button to unlock browser beep/speech cues.
- Idle/autonomous lesson review uses an internal profile reader instead of workspace-bound file reads.

## v46 highlights

- `/memory`, `/remember`, `/knowledge`, and `/learn-errors` give Nova a lightweight local memory/knowledge layer.
- Normal chat uses local debug/Q&A knowledge without forcing a project build.
- Autonomous cycles now reconsider the plan before acting and review lessons from repeated mistakes.
- Cycle reports now include tool reasons, edit details and verification evidence.
- The Assistant state panel uses expressive icons and can trigger browser speech/sounds for major events.

- `/self-guide` explains every major mode, command family and safe workflow.
- `/model-timeout off` lets local Ollama calls wait until they return; use `/ollama-stop --confirm` if stuck.
- `/avatar` no longer reports a transient working state that disagrees with the GUI.
- Idle mode records lessons in `IDLE_LESSONS.md` and reviews them in later cycles.


## v52.0 note

v52.1 builds on v52.0 with developer-in-the-loop QA: ambiguous current-vs-new project requests now ask for a target decision, generated output cards describe what the user is opening/downloading, UI clutter controls are expanded, and behavioural checks for calculators and todo apps are stricter before success is claimed.


## v52.1 note

v52.1 adds an interactive planning gate for vague or ambiguous user requests. Nova can pause before running tools, offer multiple choice answers with a recommended option, and accept a custom reply so it does not guess incorrectly before making files.


## v52.2 note

v52.4 adds generic game-design intent and request-specific game fallback so Nova can build custom browser games beyond fixed templates while keeping acceptance contracts and repair plans.


## v54.3 self-awareness

Use `/self-awareness` to generate a read-only capability inventory, recent autonomous-state summary, safety-boundary list and recommended next actions.


## v54.3 report hygiene

This release prevents rapid repeated self-awareness and quality-dashboard report requests from overwriting each other and removes a duplicate Self-awareness quick-action button from the Web UI.

## v55.2.9 repair audit and autonomous project reliability

- Uploaded photos can now be analyzed directly with `/image-analyze latest` or `/image-analyze context:ID` instead of needing to move the file into the workspace.
- The GUI upload bar now includes one-click **Analyze latest photo** and **Generate SVG** actions.
- Context file listings show the exact `/image-analyze context:ID` command for each uploaded/attached image.
- Upload handling now rejects files over 25 MB before decoding and accepts data-URL or raw-base64 payloads.
- Image dimension detection was hardened for JPEG/SVG edge cases.

## v55.1 command contract verification

Nova now includes `/command-verify`, a safe read-only command contract check that verifies important existing commands return expected user-facing content and do not silently degrade into `Command error` or `Unknown command`. This helps ensure features keep working across iterations rather than merely avoiding crashes.


## v55.1 file/photo context sharing

- Added `/attach-file PATH`, `/context-files`, `/context-files clear`, and `/image-generate PROMPT`.
- Web UI can upload text files/photos as shared prompt context.
- Uploaded photos are stored locally and can be passed to `/image-analyze` when a vision model is configured.
- `/image-generate` requires a real image backend; `/image-draft` creates a labelled local SVG draft.
- `/efficiency` reports tool/model/chat timings, process CPU time and estimated energy use.
- `/efficiency time 3 /status` runs timed command comparisons for weak-spot analysis.


## v55.3.113 Optional upgrade installer and voice setup wizard

This build adds a safer path for significant optional upgrades that may require downloads:

- `/optional-upgrades` lists the allowlisted install targets, exact commands and verification commands.
- `/upgrade-install ruff` is a dry run; `/upgrade-install ruff --confirm` installs only after explicit confirmation.
- Supported install targets are `ruff`, `precommit`, and `playwright`. Heavy or risky tools remain recommendation-only.
- The installer writes reports into `docs/OPTIONAL_UPGRADE_*_LATEST.*` after a confirmed install.

Voice mode also gains a browser-side setup wizard:

- Click **Voice setup wizard** in Settings to inspect browser support, microphone permission, selected input and browser-visible devices.
- For Sony WH-1000/WH-1000XM style headsets, select the **Headset microphone** in Windows Settings > System > Sound > Input, then click **Refresh mics** and **Mic test** in Nova.
- The wizard does not upload microphone audio; it only uses browser/OS permission APIs and local diagnostics.

## v55.3.113 Cohesion architecture validation loop

Adds `/cohesion-report`, `/validation-ladder` and `/iteration-plan` to connect self-awareness, architecture checks, Docker validation and autonomous iteration into one evidence-based workflow.

## v55.3.113 less strict sandbox mode

For owned/local security labs where repeated approvals are getting in the way, Nova now supports:

```text
/sandbox-less-strict on
```

This switches the sandbox policy to `trusted_lab`, enables sandbox networking, authorised-lab mode and sandbox autonomy, and allows common Kali lab tools without per-command approval. Host escape commands and destructive root patterns remain blocked.

Use these to move between modes:

```text
/sandbox-policy strict
/sandbox-policy balanced
/sandbox-policy trusted_lab
```


## v55.3.113 Blueprint, candidate, trace, GUI and MCP upgrade

New command groups added in this release:

- `/blueprint GOAL` compiles a user prompt into a project blueprint with must-have, must-not-have and validation rules.
- `/candidate-build GOAL`, `/candidate-compare GOAL` and `/model-output-score GOAL` score candidate outputs against the prompt before promotion.
- `/trace-last`, `/trace-run RUN_ID`, `/trace-export` and `/performance-dashboard` provide a local agent trace cockpit for prompt, model, file, command, validation and repair events.
- `/gui-feature-map`, `/gui-mode cockpit`, `/gui-redesign-preview` and `/gui-regression-test` make a full GUI redesign safer by proving existing features still have homes.
- `/mcp-export-manifest`, `/mcp-tools` and `/mcp-status` export Nova tools in an MCP-style manifest for future connector work.
- `/gui-snapshot` and `/gui-visual-test` provide optional Playwright visual-regression entry points.
- `/nova-mega-test --confirm` runs the broadest single built-in Nova validation pass and writes a copy/paste report for streamlined debugging.


## v55.3.113 Major Autonomy, Validation, Trace and Connector Upgrade

Adds prompt-to-test contracts, candidate tournaments, surgical repair v2, trace timelines, cockpit GUI preview, safe MCP permission reports, autonomous mission planning, model output coaching, environment profiles, new-PC migration benchmarking, project-state database and regression memory commands.

## Improvement proposal completion

Use `/improvement-proposals FOCUS` to build ranked implementation-ready proposals, then `/improvement-cycle --confirm FOCUS` to complete safe low-risk proposal artifacts and record completed/skipped status. Use `/completed-improvements` to show the latest completion report.


## v55.3.113 adaptive model requirements

This build adds a confirmable local model requirement/download planner so Nova can request missing Ollama models when a task needs stronger coding, chat, vision or embedding capability. New commands include `/model-readiness GOAL`, `/model-download-plan GOAL`, `/model-requirements GOAL` and `/model-install NAME --confirm`. Downloads are never started without explicit confirmation and the exact `ollama pull ...` command is shown first.

## v55.3.121 validation shortcuts

- `/completion-audit` verifies previous patch tasks are actually wired and regression-protected.
- `/nova-system-test` runs the one-button Nova capability sequence.
- `/massive-test --confirm` now includes the Nova contract and completion audit in quick mode. Use `/massive-test --confirm full` for the slower legacy stack.


### Nova desktop voice launcher

Run `start_nova_desktop_voice_listener.bat` on Windows to keep a small OS-level listener active. It listens for phrases such as `hey nova`, `start nova`, or `launch nova`, then starts `start_windows_assistant.bat` in Browser UI mode using `NOVA_START_CHOICE=2`. Browser-based always-listening still requires the Nova page to be open and microphone permission to be allowed.


## Nova eval packs

Use `/nova-eval-packs plan core` to preview deterministic upgrade checks, or `/nova-eval-packs run all` to verify core, release, agent, coding and voice command paths after a refactor.


## Optional FastAPI bridge

Nova can now expose a guarded localhost API bridge without replacing the existing CLI or browser UI:

```bash
python app.py --api --host 127.0.0.1 --port 8767
```

Install optional API dependencies with:

```bash
pip install -r requirements-api.txt
```

Useful status command:

```text
/nova-api-status
```

The API command route is read-only by default and blocks mutating/self-apply style commands unless the caller explicitly sets `allow_mutation=true`.

### Nova v55.3.141 Clean Studio GUI shell hotfix

Use `Nova_v55_3_141_clean_studio_gui_hotfix_20260602.zip` if you want the cleaner VS Code / ChatGPT-style web shell. It preserves the v55.3.141 startup-validation fixes and keeps the existing project, voice, workbench, activity and validation features available behind a less cluttered layout.


Compatibility anchors: previous tested packages include `Nova_v55_3_142_orbit_workspace_drawer_hotfix_20260602.zip` and v55.3.141 voice/resize flow updates.


## v55.3.160 quick test commands

After extracting, run `START_NOVA_HERE.bat` from File Explorer or `./START_NOVA_HERE.bat` from PowerShell.

Core validation:

```powershell
python -m compileall app.py nova winlocalassistant
python tests_smoke.py
python -m pytest -q tests_nova_autonomous_continuous_v55_3_156.py tests_nova_media_and_gui_v55_3_156.py tests_nova_high_spec_subagents_v55_3_156.py
```

Media examples inside Nova:

```text
/image-status
/image-draft neon rabbit mascot for Nova
/image-generate neon rabbit mascot for Nova
/image-edit latest => make the lighting warmer while preserving composition
/video-status
/video-plan 10 second cinematic trailer about Nova improving a project
/video-validate 10 second cinematic trailer about Nova improving a project
```

Autonomous examples:

```text
/autonomous start --continuous improve Nova safely and keep choosing the next verified improvement
/autonomous start --finite --cycles 1 make a small test project
/subagents improve Nova without regressions
/authority-mode status
```


## v55.3.160 natural research and voice hardening

- Plain English requests such as `search for information about WW2` and `research Neil the seal in Tasmania` now route to Nova research tools instead of normal chat denial.
- Adds `/internet-search` and `/search-web` as obvious search commands.
- Project generation strips interactive clarification text from theme detection so `make a funny game about dogs` remains a dogs game, not `Dogsuserclarificationgame`.
- Spoken replies now use complete contextual sentences and avoid cutting off mid-sentence.
- `/compare` aliases to Nova compare tools.

## v55.3.160 clean GUI and Docker validation notes

Nova now starts with a cleaner Orbit workspace: the current version is shown in the header, command drawers are less cluttered, and side drawers reserve space instead of covering the central chat. Docker validation also distinguishes between a Nova/code failure and Docker Desktop simply not running. If Docker Desktop is unavailable, Nova reports the validation as skipped/degraded instead of a failed code validation.



## v55.3.160 media pipeline refinement

Adds a dependency-light media planning layer for images and videos:

- `/media-status` gives one clean readiness summary for image and video backends.
- `/image-plan PROMPT` creates prompt variations, seeds, recommended size and negative prompts before calling a heavy image backend.
- `/video-package PROMPT` writes a manifest, validation report, storyboard SVG, shot list CSV, preview AVI and preview HTML in one resumable project folder.
- `/video-storyboard PROMPT` writes a visual storyboard only, useful before expensive rendering.

These are safe planning/export features and do not pretend a real AI image/video render happened when no backend is configured.


Legacy note: Nova v55.3.159 clean GUI/Docker hardening remains preserved in v55.3.160.

## v55.3.164 provider runtime additions

Nova now has explicit provider lanes for local Ollama, advanced local OpenAI-compatible servers (llama.cpp, vLLM, SGLang, local Gemma-style servers), and permission-gated remote providers (SubQ, NVIDIA NIM, OpenRouter). Start with `/provider-status`, `/provider-route GOAL`, `/provider-test ollama`, and `/queue-status`. Remote providers require `/allow-internet on` and your own API key environment variable.


## v55.3.164 scheduling control plane

- Added `/schedule-task`, `/schedule-status`, `/schedule-confirm`, `/schedule-cancel`, `/task-decompose`, and `/scheduling-audit`.
- Added `winlocalassistant/scheduler_foundation.py` with safe SQLite schedule records, prompt-injection filtering, risk classification, DAG validation, and retry/backoff planning.
- Added GUI command-palette entries and regression tests.

### v55.3.166 LLM training lab

Nova includes a safe LLM-from-scratch inspired lab for planning and inspecting experiments without starting hidden training jobs:

- `/llm-lab plan GOAL`
- `/llm-lab dataset PATH`
- `/llm-lab estimate 13m 5m`
- `python -m winlocalassistant.llm_training_lab --root . --plan`

The lab writes evidence to `docs/NOVA_LLM_TRAINING_LAB_LATEST.md/json` and is checked by `/release-readiness --full`.

### v55.3.167 Task execution evidence and autonomy hardening

- Added `/task-contract GOAL` to preview intent, risk, allowed actions, forbidden actions, expected outputs and verification before mutation.
- Added `/task-evidence` to inspect JSON/Markdown evidence from `/write`, `/shell` and `/verify`.
- Added a repeated-failure guard so Nova stops retrying the same failing command/action after repeated identical failures.
- `/verify` can now show a lightweight summary when no command is supplied.
- `/release-readiness --full` now checks task contracts, task evidence, repeated-failure state and autonomous safety surfaces before packaging.

### v55.3.168 Project-state continuity memory

- Added `/project-state`, `/project-state --json`, and `/project-state --next`.
- Added `winlocalassistant.project_state` to connect build version, task evidence, release-readiness, package manifest, host-only checks, known limitations, and safest next action.
- Vague continuation prompts such as `again` and `continue where this left off` now use project-state evidence before suggesting a next step.
- Autonomous status now includes project-state snapshot path, last task evidence path, last release-readiness verdict, stop reason, and whether it is safe to continue automatically.
- Release-readiness now includes project-state / continue-readiness status.
