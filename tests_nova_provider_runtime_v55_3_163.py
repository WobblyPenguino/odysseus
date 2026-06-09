from __future__ import annotations

from pathlib import Path

import winlocalassistant
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.provider_runtime import (
    RouteKey,
    ProviderScheduler,
    choose_provider,
    provider_matrix,
    provider_test_plan,
)
from winlocalassistant.tools import ToolRegistry

ROOT = Path(__file__).resolve().parent


def test_version_163_provider_runtime_metadata_is_visible() -> None:
    assert winlocalassistant.__version__
    assert f"v{winlocalassistant.__version__}" in winlocalassistant.VERSION_LABEL
    assert "provider abstraction" in winlocalassistant.VERSION_LABEL
    webui = (ROOT / "winlocalassistant" / "webui.py").read_text(encoding="utf-8")
    assert "data-provider-route-bar=\"v55.3.164\"" in webui
    assert "/provider-route" in webui
    assert "/queue-status" in webui
    assert "SubQ" in webui and "NVIDIA NIM" in webui


def test_provider_matrix_is_local_first_and_remote_gated(monkeypatch) -> None:
    monkeypatch.delenv("SUBQ_API_KEY", raising=False)
    monkeypatch.delenv("NVIDIA_NIM_API_KEY", raising=False)
    cfg = AssistantConfig(allow_internet=False)
    payload = provider_matrix(cfg)
    rows = {row["provider"]: row for row in payload["providers"]}
    assert rows["ollama"]["enabled"] is True
    assert rows["ollama"]["privacy"] == "local"
    assert rows["subq"]["enabled"] is False
    assert rows["nvidia-nim"]["enabled"] is False
    assert any("local by default" in rule for rule in payload["rules"])


def test_provider_route_uses_subq_only_when_remote_allowed() -> None:
    local_cfg = AssistantConfig(allow_internet=False)
    local_route = choose_provider("review this entire repo and months of history", ctx_tokens=700_000, privacy="local_only", config=local_cfg)
    assert local_route["provider"] == "ollama"
    assert local_route["permission"] == "local-only"

    remote_cfg = AssistantConfig(allow_internet=True)
    remote_route = choose_provider("review this entire repo and months of history", ctx_tokens=700_000, privacy="remote_ok", config=remote_cfg)
    assert remote_route["provider"] == "subq"
    assert remote_route["permission"] == "remote-long-context"


def test_provider_scheduler_serializes_same_provider_model_but_allows_other_lanes() -> None:
    scheduler = ProviderScheduler()
    seen: list[str] = []

    def task(name: str) -> str:
        seen.append(name)
        return name

    assert scheduler.run(RouteKey("ollama", "qwen3-coder:30b"), task, "a", desc="first") == "a"
    assert scheduler.run(RouteKey("vllm", "qwen3-coder:30b"), task, "b", desc="second") == "b"
    snap = scheduler.snapshot()
    assert seen == ["a", "b"]
    assert snap["active_count"] == 0
    assert len(snap["recent"]) >= 2


def test_provider_test_plans_are_dry_run_and_do_not_require_keys() -> None:
    cfg = AssistantConfig(allow_internet=False)
    subq = provider_test_plan(cfg, "subq")
    assert subq["ok"] is True
    assert subq["dry_run"] is True
    assert "SUBQ_API_KEY" in subq["command"]
    nim = provider_test_plan(cfg, "nvidia-nim")
    assert "NVIDIA_NIM_API_KEY" in nim["command"]


def test_tool_registry_exposes_provider_runtime_tools(tmp_path: Path) -> None:
    registry = ToolRegistry(AssistantConfig(workspace=str(tmp_path)))
    for name in ["provider_status", "provider_route", "provider_test", "queue_status", "queue_drain"]:
        assert name in registry.tools
    assert registry.call("provider_status").ok
    assert registry.call("provider_route", goal="review whole repo").ok
    assert registry.call("provider_test", provider="ollama").ok
    assert registry.call("queue_status").ok


def test_core_routes_provider_runtime_commands(tmp_path: Path) -> None:
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path)))
    assert "Provider Status" in core.handle_command("/provider-status")
    assert "Provider Route" in core.handle_command("/provider-route review entire repo")
    assert "Provider Test Plan" in core.handle_command("/provider-test ollama")
    assert "active" in core.handle_command("/queue-status").lower()
    msg = core.handle_command("/provider subq")
    assert "subq" in msg.lower()
