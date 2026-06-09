# Nova FastAPI API Bridge

Nova now includes an optional FastAPI sidecar instead of a risky backend rewrite. The existing CLI and browser UI remain the source of truth; the API bridge exposes safe HTTP routes for dashboards, evals, workbench launchers and guarded command execution.

## Start

```bash
python app.py --api --host 127.0.0.1 --port 8767
```

Or run `start_nova_fastapi_api.bat` on Windows.

Optional dependencies:

```bash
pip install -r requirements-api.txt
```

## Key routes

- `GET /api/v1/health`
- `GET /api/v1/status`
- `GET /api/v1/workbench`
- `GET /api/v1/odysseus/coverage`
- `GET /api/v1/eval-packs/{pack}`
- `POST /api/v1/eval-packs/{pack}/run`
- `GET /api/v1/events`
- `POST /api/v1/command`

## Safety rule

`POST /api/v1/command` is read-only by default. Commands classified as mutating or privileged are blocked unless the caller sets `allow_mutation=true`. This keeps the API useful for GUI panels and automation dashboards without silently giving a remote page full write/apply power.
