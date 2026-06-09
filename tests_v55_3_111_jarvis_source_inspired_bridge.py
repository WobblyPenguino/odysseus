from __future__ import annotations

from winlocalassistant.config import AssistantConfig
from winlocalassistant.tools import ToolRegistry
from winlocalassistant.jarvis_bridge import (
    build_jarvis_setup_doctor,
    build_sidecar_preflight,
    build_authority_decision,
    build_workflow_blueprint,
    inspect_ollama_for_jarvis,
)
from winlocalassistant.feature_continuity import build_feature_continuity_audit
from winlocalassistant.validation_matrix import build_validation_matrix


def test_jarvis_setup_doctor_exposes_docker_ollama_guidance():
    payload = build_jarvis_setup_doctor(url="http://127.0.0.1:1")
    assert "daemon" in payload
    assert "docker" in payload
    assert "ollama" in payload
    assert payload["jarvis_ollama_fields"]["ollama_base_url_inside_docker"] == "http://host.docker.internal:11434"
    assert "127.0.0.1:3142" in payload["safe_jarvis_docker_run"]


def test_sidecar_preflight_blocks_risky_capabilities_by_default():
    payload = build_sidecar_preflight("terminal filesystem browser screenshot")
    by_name = {item["capability"]: item for item in payload["capabilities"]}
    assert by_name["terminal"]["allowed_by_policy"] is False
    assert by_name["filesystem"]["allowed_by_policy"] is False
    assert by_name["browser"]["allowed_by_policy"] is False
    assert by_name["screenshot"]["allowed_by_policy"] is False


def test_authority_decision_records_receipt_not_execution():
    record = build_authority_decision("browser", "open credentialed site", risk="high")
    assert record["status"] in {"blocked", "suggested", "queued_for_review"}
    assert "executed" not in record["status"]
    assert record["capability"] == "browser"


def test_workflow_blueprint_contains_validate_and_receipt_nodes():
    payload = build_workflow_blueprint("monitor generated app and propose repair")
    node_ids = {node["id"] for node in payload["nodes"]}
    assert {"context", "authority", "validate", "receipt"} <= node_ids


def test_tool_registry_exposes_deeper_jarvis_tools():
    registry = ToolRegistry(AssistantConfig(workspace="."))
    for name in ["jarvis_doctor", "sidecar_preflight", "bridge_authority", "workflow_blueprint"]:
        assert name in registry.tools
    res = registry.call("workflow_blueprint", goal="safe supervised automation")
    assert res.ok
    assert "Supervised workflow blueprint" in res.data["message"]


def test_continuity_and_validation_matrix_include_deeper_jarvis_markers():
    registry = ToolRegistry(AssistantConfig(workspace="."))
    cont = build_feature_continuity_audit(__import__('pathlib').Path.cwd(), tool_names=sorted(registry.tools))
    assert cont["ok"], cont.get("failed")
    matrix = build_validation_matrix(__import__('pathlib').Path.cwd(), goal="jarvis bridge validation")
    names = {c["name"] for c in matrix["checks"]}
    assert "jarvis_bridge_contract" in names


def test_ollama_inspector_has_docker_url_even_without_ollama():
    payload = inspect_ollama_for_jarvis()
    assert payload["jarvis_docker_base_url"] == "http://host.docker.internal:11434"
    assert payload["wrong_docker_base_url"] == "http://localhost:11434"
