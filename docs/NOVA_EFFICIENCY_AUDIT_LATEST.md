# Nova Efficiency and UX Audit

Decision: **PASS**
Generated: 2026-06-09 23:39:35
Python files scanned: 420

## Research-backed signals
- **Ollama API**: Ollama exposes keep_alive, stream=false, JSON/structured outputs and final timing fields such as eval_count/eval_duration. Action: Keep queueing same-model calls, use stream=false for tool JSON, and record token/s for model benchmark history.
- **llama.cpp/local inference patterns**: Quantization, partial GPU offload, KV-cache choices and speculative decoding are core local-inference efficiency levers. Action: Keep high-spec and fallback model profiles separate; add future GGUF/llama.cpp profile export rather than hard-coding only Ollama.
- **Playwright visual comparisons**: Screenshot baselines catch GUI regressions that unit tests miss. Action: Keep optional Playwright visual tests and add a calm-layout screenshot smoke test for the chat/drawers/popups.
- **OpenTelemetry-style instrumentation**: Spans and structured events make failures visible across agent, tool, model and GUI layers. Action: Continue replacing silent exceptions with structured events that self-repair can consume.

## Findings
- **MEDIUM / maintainability** — Large modules need extraction seams (.)
  - Large Python modules are harder for local models to reason over and slower to test in focused slices: winlocalassistant\core.py, winlocalassistant\tools.py, winlocalassistant\webui.py
  - Fix: Prefer additive extraction around stable seams: routing tables, GUI command metadata, media planning, and audits should live in smaller modules with focused tests.
- **MEDIUM / observability** — Broad exceptions still hide repair evidence (.)
  - Found 321 broad exception handlers without structured logging. Examples: scripts\run_gui_runtime_test.py:31, scripts\run_gui_runtime_test.py:197, scripts\run_gui_runtime_test.py:200, scripts\run_gui_runtime_test.py:205, winlocalassistant\action_watcher.py:120, winlocalassistant\adaptive_backlog.py:31, winlocalassistant\analytics_engine.py:113, winlocalassistant\analytics_engine.py:140, winlocalassistant\analytics_engine.py:165, winlocalassistant\analytics_engine.py:235
  - Fix: Replace bare `except Exception: pass` with structured warning records so mistake-learning and self-repair can learn the root cause.
- **MEDIUM / gui** — Monolithic GUI file is a regression risk (winlocalassistant/webui.py)
  - webui.py is 438,154 characters. Small CSS/JS patches become fragile and hard to visually verify.
  - Fix: Move command palette metadata, layout CSS, media widgets and voice/state panels toward separate templates/modules while preserving existing routes.

## Validation ladder
- Run python -m winlocalassistant.validate --all before release.
- Run a focused pytest slice for changed GUI/media/model files.
- Run /nova-efficiency-audit after major patches and attach the generated docs to release notes.
- Use /llm-status to ensure same-model prompts are queued, not overlapped.
- Use optional Playwright visual smoke tests before changing GUI layout again.
