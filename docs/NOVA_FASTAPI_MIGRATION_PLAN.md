# Nova FastAPI Architecture Plan

Decision: **Yes, Nova would benefit from FastAPI for the GUI/API/event layer, but not from a risky one-shot rewrite.**
Recommendation: `hybrid_fastapi_sidecar`
Generated: 2026-06-01 18:53:49

## Keep
- NovaCore / AssistantCore command router
- CLI commands
- verified self-apply engine
- eval packs
- voice launcher

## Change
- replace ThreadingHTTPServer web shell with optional FastAPI app
- move UI calls to typed JSON routes
- stream activity through WebSocket/SSE
- serve static GUI assets separately from backend logic

## Do not do
- copy Odysseus app.py wholesale
- rename all modules at once
- put email/calendar/webhooks behind unauthenticated localhost bypass
- run heavy jobs inside request handlers

## Staged migration
### 1. Keep NovaCore stable and add optional FastAPI sidecar
Avoid breaking the working CLI, tests and voice launcher while giving the GUI real API endpoints.
Routes: `GET /api/health`, `POST /api/command`, `GET /api/activity`, `GET /api/files`
Validation: existing CLI tests still pass, TestClient route smoke, web UI still opens from start script

### 2. Add streaming/events layer
Nova's autonomous, voice and validation loops need live progress without polling-heavy UI code.
Routes: `WebSocket /ws/events or SSE /api/events`, `POST /api/command/{id}/stop`, `GET /api/runs/{id}`
Validation: fake long command streams progress, stop button cancels safe worker, event log remains durable

### 3. Turn Odysseus-translated commands into panels
Cookbook, compare, docs, notes/tasks, skills and memory-vault should be clickable app surfaces, not only slash commands.
Routes: `/api/cookbook/*`, `/api/compare/*`, `/api/docs/*`, `/api/notes/*`, `/api/tasks/*`, `/api/skills/*`
Validation: one API smoke per panel, permission gates before mutation, round-trip JSON receipts

### 4. Optional auth/integration hardening
Only needed before exposing Nova beyond localhost or adding email/calendar/webhook credentials.
Routes: `/api/auth/*`, `/api/tokens/*`, `/api/integration-gates/*`
Validation: localhost-only default, admin-only privileged routes, no secrets in logs

## Current Nova signals
- `has_http_webui`: True
- `has_core`: True
- `has_verified_self_apply`: True
- `module_count`: 140
