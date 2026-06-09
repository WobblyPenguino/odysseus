from __future__ import annotations

from pathlib import Path

import pytest

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.nova_api import (
    build_api_bridge_status,
    classify_api_command,
    create_fastapi_app,
    fastapi_available,
)


def test_api_status_payload_lists_guarded_routes(tmp_path: Path) -> None:
    payload = build_api_bridge_status(tmp_path)
    assert payload["architecture"] == "hybrid_fastapi_sidecar"
    assert payload["read_only_by_default"] is True
    assert "POST /api/v1/command" in payload["routes"]
    assert "GET /api/v1/odysseus/workspace" in payload["routes"]
    assert "POST /api/v1/odysseus/workspace/action" in payload["routes"]
    assert "GET /api/v1/odysseus/runtime" in payload["routes"]
    assert "POST /api/v1/odysseus/runtime/action" in payload["routes"]
    assert "/nova-eval-packs run core" in payload["safe_commands"]


def test_api_command_classifier_blocks_mutating_self_apply() -> None:
    safe = classify_api_command("/nova-api-status")
    risky = classify_api_command("/nova-self-apply apply verified-self-change-flow --confirm")
    chat = classify_api_command("explain Nova status")

    assert safe["risk"] == "low"
    assert safe["mutating"] is False
    assert risky["risk"] == "high"
    assert risky["mutating"] is True
    assert chat["risk"] == "chat"


def test_core_routes_nova_api_status(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "winlocalassistant").mkdir()
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path)))
    out = core.handle_command("/nova-api-status")
    assert "Nova FastAPI Bridge Status" in out
    assert "POST /api/v1/command" in out
    assert "python app.py --api" in out


@pytest.mark.skipif(not fastapi_available(), reason="FastAPI optional dependency is not installed")
def test_fastapi_routes_health_eval_and_guarded_command(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi.testclient import TestClient

    # Keep this compatibility test hermetic when the developer machine has
    # NOVA_API_TOKEN configured for real remote use. Token-required API
    # behaviour is covered by the remote-access tests.
    monkeypatch.delenv("NOVA_API_TOKEN", raising=False)

    core = AssistantCore(AssistantConfig(workspace=str(tmp_path)))
    app = create_fastapi_app(core)
    client = TestClient(app)

    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["product"] == "Nova"

    status = client.get("/api/v1/status")
    assert status.status_code == 200
    assert "POST /api/v1/command" in status.json()["routes"]

    eval_plan = client.get("/api/v1/eval-packs/core")
    assert eval_plan.status_code == 200
    assert eval_plan.json()["pack"] == "core"

    workspace = client.get("/api/v1/odysseus/workspace")
    assert workspace.status_code == 200
    assert any(item["id"] == "code" for item in workspace.json()["windows"])
    assert any(item["id"] == "runtime" for item in workspace.json()["windows"])

    workbench_action = client.post(
        "/api/v1/odysseus/workspace/action",
        json={"surface": "notes", "action": "add", "payload": {"text": "api note"}},
    )
    assert workbench_action.status_code == 200
    assert workbench_action.json()["snapshot"]["notes"][0]["text"] == "api note"

    runtime = client.get("/api/v1/odysseus/runtime")
    assert runtime.status_code == 200
    assert runtime.json()["status"] in {"missing", "configured", "running"}

    runtime_blocked = client.post("/api/v1/odysseus/runtime/action", json={"action": "start", "payload": {}})
    assert runtime_blocked.status_code == 400

    safe = client.post("/api/v1/command", json={"command": "/version"})
    assert safe.status_code == 200
    assert "Nova" in safe.json()["output"]

    blocked = client.post("/api/v1/command", json={"command": "/nova-self-apply apply verified-self-change-flow --confirm"})
    assert blocked.status_code == 403
