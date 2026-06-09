from __future__ import annotations

import os
import secrets
import time
from pathlib import Path
from typing import Any, Callable

from . import ASSISTANT_NAME, VERSION_LABEL, __version__
from .config import AssistantConfig
from .eventlog import ACTIVITY_PATH, log_activity, tail_jsonl
from .nova_eval_packs import build_nova_eval_plan, render_nova_eval_packs, run_nova_eval_pack
from .nova_odysseus_suite import build_gui_workbench_plan, build_odysseus_workspace_snapshot, build_suite_status, odysseus_dependency_status, odysseus_runtime_action, odysseus_workspace_action

try:  # Optional runtime dependency: Nova can still run in CLI/webui mode without it.
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
except Exception:  # pragma: no cover - exercised through status payloads when missing.
    FastAPI = None  # type: ignore[assignment]
    HTTPException = None  # type: ignore[assignment]
    Request = object  # type: ignore[assignment,misc]
    CORSMiddleware = None  # type: ignore[assignment]
    BaseModel = object  # type: ignore[assignment,misc]

    def Field(default: Any = None, **_: Any) -> Any:  # type: ignore[override]
        return default


READ_ONLY_PREFIXES = (
    "/version",
    "/status",
    "/help",
    "/nova-brand-audit",
    "/nova-eval-packs",
    "/eval-packs",
    "/nova-odysseus-suite",
    "/odysseus-suite",
    "/nova-tool-permissions",
    "/tool-permissions",
    "/nova-cookbook",
    "/model-cookbook",
    "/nova-integration-gates",
    "/integration-gates",
    "/nova-fastapi-plan",
    "/nova-gui-workbench-plan",
    "/nova-api-status",
    "/remote-access-status",
    "/remote-access-plan",
    "/remote-access-setup",
    "/remote-access-test",
    "/remote-access-preflight",
    "/remote-api-health",
    "/remote-health",
    "/remote-profile",
    "/remote-profiles",
    "/remote-profile-wizard",
    "/remote-wizard",
    "/remote-profile-plan",
    "/nova-api-health",
    "/command-verify",
    "/trace-observability",
    "/guardrail-memory",
    "/context-router-policy",
    "/coding-audit",
    "/verifier-ladder",
    "/patch-impact-plan",
    "/voice-pipeline-review",
    "/voice-audit",
    "/tool-catalog",
    "/command-catalog",
    "/model-context",
    "/security-status",
    "/release-checklist",
)

MUTATION_WORDS = (
    " apply",
    " promote",
    " delete",
    " remove",
    " save",
    " install",
    " write",
    " confirm",
    " --confirm",
    " --yes",
    " start",
    " stop",
    " run ",
)

MUTATING_PREFIXES = (
    "/remote-access-scripts",
    "/remote-scripts",
)

HIGH_RISK_PREFIXES = (
    "/nova-self-apply",
    "/verified-self-apply",
    "/repair-apply",
    "/patch-promote",
    "/docker-promote-patch",
    "/model-install",
    "/project-delete",
    "/project-remove",
    "/sandbox-exec",
    "/sandbox-dev-run",
    "/autonomous",
    "/workflow-run",
    "/save-file",
)

SAFE_COMMANDS: tuple[str, ...] = (
    "/version",
    "/status",
    "/help",
    "/nova-api-status",
    "/remote-access-test",
    "/remote-api-health 127.0.0.1 8767 --dry-run",
    "/remote-profile-wizard --host 127.0.0.1 --mac AA:BB:CC:DD:EE:FF",
    "/nova-eval-packs plan core",
    "/nova-eval-packs run core",
    "/nova-odysseus-suite",
    "/nova-fastapi-plan",
    "/nova-gui-workbench-plan",
    "/nova-integration-gates",
)


if FastAPI is not None:

    class CommandRequest(BaseModel):
        command: str = Field("", description="Nova slash command or user message.")
        allow_mutation: bool = Field(False, description="Required for commands classified as mutating or privileged.")

    class OdysseusWorkspaceActionRequest(BaseModel):
        surface: str = Field("", description="Odysseus workbench surface, such as docs, notes, tasks, skills or gates.")
        action: str = Field("list", description="Workbench action to run.")
        payload: dict[str, Any] = Field(default_factory=dict, description="Surface-specific action data.")
        confirmed: bool = Field(False, description="Required for safety-sensitive policy relaxations.")

else:

    class CommandRequest:  # type: ignore[no-redef]
        def __init__(self, command: str = "", allow_mutation: bool = False) -> None:
            self.command = command
            self.allow_mutation = allow_mutation

    class OdysseusWorkspaceActionRequest:  # type: ignore[no-redef]
        def __init__(self, surface: str = "", action: str = "list", payload: dict[str, Any] | None = None, confirmed: bool = False) -> None:
            self.surface = surface
            self.action = action
            self.payload = payload or {}
            self.confirmed = confirmed


def fastapi_available() -> bool:
    return FastAPI is not None


def build_api_bridge_status(root: Path | str | None = None) -> dict[str, Any]:
    root_path = Path(root or Path.cwd()).resolve()
    return {
        "ok": True,
        "product": ASSISTANT_NAME,
        "version": __version__,
        "version_label": VERSION_LABEL,
        "workspace": str(root_path),
        "fastapi_available": fastapi_available(),
        "architecture": "hybrid_fastapi_sidecar",
        "default_host": "127.0.0.1",
        "default_port": 8767,
        "read_only_by_default": True,
        "mutation_policy": "POST /api/v1/command refuses mutating/high-risk commands unless allow_mutation=true. If NOVA_API_TOKEN is set, command/action/event/status routes require Authorization: Bearer <token> or X-Nova-Token.",
        "auth_token_required": bool(os.environ.get("NOVA_API_TOKEN")),
        "safe_commands": list(SAFE_COMMANDS),
        "routes": [
            "GET /api/v1/health",
            "GET /api/v1/status",
            "GET /api/v1/workbench",
            "GET /api/v1/odysseus/workspace",
            "POST /api/v1/odysseus/workspace/action",
            "GET /api/v1/odysseus/runtime",
            "POST /api/v1/odysseus/runtime/action",
            "GET /api/v1/odysseus/coverage",
            "GET /api/v1/eval-packs/{pack}",
            "POST /api/v1/eval-packs/{pack}/run",
            "GET /api/v1/events",
            "POST /api/v1/command",
        ],
    }


def render_api_bridge_status(payload: dict[str, Any]) -> str:
    lines = [
        "# Nova FastAPI Bridge Status",
        "",
        f"Architecture: **{payload.get('architecture')}**",
        f"FastAPI available: **{payload.get('fastapi_available')}**",
        f"Default endpoint: `http://{payload.get('default_host')}:{payload.get('default_port')}`",
        f"Workspace: `{payload.get('workspace')}`",
        "",
        "## Safety policy",
        f"- Read-only by default: **{payload.get('read_only_by_default')}**",
        f"- {payload.get('mutation_policy')}",
        f"- API token required now: **{payload.get('auth_token_required')}**",
        "",
        "## Routes",
    ]
    lines.extend(f"- `{route}`" for route in payload.get("routes", []))
    lines += [
        "",
        "## Start command",
        "```bash",
        "python app.py --api --host 127.0.0.1 --port 8767",
        "```",
    ]
    return "\n".join(lines)


def _classify_remote_profile_api_command(text: str) -> dict[str, Any] | None:
    parts = text.strip().split()
    if not parts or parts[0].lower() not in {"/remote-profile", "/remote-profiles"}:
        return None
    action = parts[1].lower() if len(parts) > 1 else "list"
    aliases = {"ls": "list", "status": "list", "show": "show", "get": "show", "rm": "remove", "delete": "remove", "del": "remove", "set-default": "default", "use": "default", "test": "health", "probe": "health", "check": "validate", "verify": "validate", "wol": "wake"}
    action = aliases.get(action, action)
    if action in {"add", "remove", "default"}:
        return {"ok": True, "risk": "medium", "mutating": True, "reason": f"Remote profile `{action}` changes local profile config."}
    if action == "wake" and any(part.lower() == "--confirm" for part in parts):
        return {"ok": True, "risk": "medium", "mutating": True, "reason": "Remote profile wake with --confirm sends a Wake-on-LAN packet."}
    if action == "health" and any(part.lower() == "--allow-public" for part in parts):
        return {"ok": True, "risk": "medium", "mutating": True, "reason": "Public remote profile health probes are blocked through the API unless explicitly approved."}
    return {"ok": True, "risk": "low", "mutating": False, "reason": "Known read-only remote profile command."}


def classify_api_command(command: str) -> dict[str, Any]:
    text = (command or "").strip()
    lower = " " + text.lower() + " "
    first = text.split(maxsplit=1)[0].lower() if text else ""
    if not text:
        return {"ok": False, "risk": "empty", "mutating": False, "reason": "No command supplied."}
    if first in HIGH_RISK_PREFIXES:
        return {"ok": True, "risk": "high", "mutating": True, "reason": f"{first} is a privileged Nova command."}
    remote_profile_classification = _classify_remote_profile_api_command(text)
    if remote_profile_classification is not None:
        return remote_profile_classification
    if first in MUTATING_PREFIXES:
        return {"ok": True, "risk": "medium", "mutating": True, "reason": f"{first} writes Nova setup files and requires explicit mutation approval."}
    if first in {"/remote-api-health", "/remote-health", "/nova-api-health"} and " --allow-public " in lower:
        return {"ok": True, "risk": "medium", "mutating": True, "reason": "Public remote API probes are blocked through the API unless explicitly approved."}
    if first.startswith("/") and any(first == prefix or first.startswith(prefix + " ") for prefix in READ_ONLY_PREFIXES):
        return {"ok": True, "risk": "low", "mutating": False, "reason": "Known read-only API command."}
    if any(word in lower for word in MUTATION_WORDS):
        return {"ok": True, "risk": "medium", "mutating": True, "reason": "Command text contains mutation-like wording."}
    if first.startswith("/"):
        return {"ok": True, "risk": "medium", "mutating": False, "reason": "Slash command is not in the API read-only allowlist."}
    return {"ok": True, "risk": "chat", "mutating": False, "reason": "Plain chat message."}


def _run_command_or_message(core: Any, text: str) -> str:
    if text.strip().startswith("/"):
        return str(core.handle_command(text.strip()))
    return str(core.handle_user_message(text.strip()))


def create_fastapi_app(core: Any | None = None) -> Any:
    if FastAPI is None:
        raise RuntimeError("FastAPI is not installed. Install optional API dependencies with: pip install fastapi uvicorn")
    if core is None:
        from .core import AssistantCore

        core = AssistantCore.load()
    app = FastAPI(title="Nova API Bridge", version=__version__, description="Optional guarded HTTP API for Nova.")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1", "http://localhost"],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    def run_command(command: str) -> str:
        return _run_command_or_message(core, command)

    def require_remote_token(request: Any) -> None:
        expected = os.environ.get("NOVA_API_TOKEN", "")
        if not expected:
            return
        auth = str(request.headers.get("authorization", "")) if hasattr(request, "headers") else ""
        supplied = ""
        if auth.lower().startswith("bearer "):
            supplied = auth.split(" ", 1)[1].strip()
        if not supplied and hasattr(request, "headers"):
            supplied = str(request.headers.get("x-nova-token", ""))
        if not supplied or not secrets.compare_digest(str(supplied), str(expected)):
            raise HTTPException(status_code=401, detail="NOVA_API_TOKEN is required for this Nova API route.")

    @app.get("/api/v1/health")
    def health() -> dict[str, Any]:
        return {
            "ok": True,
            "product": ASSISTANT_NAME,
            "version": __version__,
            "workspace": getattr(getattr(core, "config", None), "workspace", str(Path.cwd())),
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    @app.get("/api/v1/status")
    def status(request: Request) -> dict[str, Any]:
        require_remote_token(request)
        root = getattr(getattr(core, "config", None), "workspace", str(Path.cwd()))
        return build_api_bridge_status(root)

    @app.get("/api/v1/workbench")
    def workbench(request: Request) -> dict[str, Any]:
        require_remote_token(request)
        root = Path(getattr(getattr(core, "config", None), "workspace", Path.cwd()))
        return build_gui_workbench_plan(root)

    @app.get("/api/v1/odysseus/workspace")
    def odysseus_workspace(request: Request) -> dict[str, Any]:
        require_remote_token(request)
        root = Path(getattr(getattr(core, "config", None), "workspace", Path.cwd()))
        return build_odysseus_workspace_snapshot(root)

    @app.post("/api/v1/odysseus/workspace/action")
    def odysseus_workspace_action_route(payload: OdysseusWorkspaceActionRequest, request: Request) -> dict[str, Any]:
        require_remote_token(request)
        root = Path(getattr(getattr(core, "config", None), "workspace", Path.cwd()))
        if hasattr(payload, "model_dump"):
            raw = payload.model_dump()
        else:
            raw = dict(getattr(payload, "__dict__", {}))
        result = odysseus_workspace_action(root, raw)
        if not result.get("ok"):
            raise HTTPException(status_code=400, detail=result.get("summary") or result.get("result", {}).get("error", "Workbench action failed"))
        return result

    @app.get("/api/v1/odysseus/runtime")
    def odysseus_runtime(request: Request) -> dict[str, Any]:
        require_remote_token(request)
        root = Path(getattr(getattr(core, "config", None), "workspace", Path.cwd()))
        return odysseus_dependency_status(root)

    @app.post("/api/v1/odysseus/runtime/action")
    def odysseus_runtime_action_route(payload: OdysseusWorkspaceActionRequest, request: Request) -> dict[str, Any]:
        require_remote_token(request)
        root = Path(getattr(getattr(core, "config", None), "workspace", Path.cwd()))
        if hasattr(payload, "model_dump"):
            raw = payload.model_dump()
        else:
            raw = dict(getattr(payload, "__dict__", {}))
        result = odysseus_runtime_action(root, raw)
        if not result.get("ok"):
            raise HTTPException(status_code=400, detail=result.get("error") or "Odysseus runtime action failed")
        return result

    @app.get("/api/v1/odysseus/coverage")
    def odysseus_coverage(request: Request) -> dict[str, Any]:
        require_remote_token(request)
        root = Path(getattr(getattr(core, "config", None), "workspace", Path.cwd()))
        return build_suite_status(root)

    @app.get("/api/v1/eval-packs/{pack}")
    def eval_pack_plan(pack: str = "core", request: Request = None) -> dict[str, Any]:
        require_remote_token(request)
        return build_nova_eval_plan(pack)

    @app.post("/api/v1/eval-packs/{pack}/run")
    def eval_pack_run(pack: str = "core", request: Request = None) -> dict[str, Any]:
        require_remote_token(request)
        return run_nova_eval_pack(lambda command: run_command(command), pack)

    @app.get("/api/v1/events")
    def events(request: Request, limit: int = 50) -> dict[str, Any]:
        require_remote_token(request)
        limit = max(1, min(200, int(limit or 50)))
        return {"ok": True, "limit": limit, "events": tail_jsonl(ACTIVITY_PATH, limit=limit)}

    @app.post("/api/v1/command")
    def command(payload: CommandRequest, request: Request) -> dict[str, Any]:
        require_remote_token(request)
        text = (payload.command or "").strip()
        risk = classify_api_command(text)
        if not risk.get("ok"):
            raise HTTPException(status_code=400, detail=risk.get("reason", "Invalid command"))
        if risk.get("mutating") and not payload.allow_mutation:
            raise HTTPException(
                status_code=403,
                detail={
                    "blocked": True,
                    "reason": risk.get("reason"),
                    "required": "Set allow_mutation=true only after reviewing the command.",
                },
            )
        output = run_command(text)
        log_activity("api_command", "Nova API command executed", {"command": text[:200], "risk": risk})
        return {"ok": True, "command": text, "classification": risk, "output": output}

    @app.get("/")
    def root() -> dict[str, Any]:
        return {"ok": True, "name": "Nova API Bridge", "health": "/api/v1/health", "docs": "/docs"}

    return app


def run_api(core: Any, host: str = "127.0.0.1", port: int = 8767) -> None:
    if FastAPI is None:
        raise RuntimeError("FastAPI is not installed. Install optional API dependencies with: pip install fastapi uvicorn")
    import uvicorn

    uvicorn.run(create_fastapi_app(core), host=host, port=port, log_level="info")
