from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.model_download_manager import build_model_readiness, install_model, render_model_readiness
from winlocalassistant.tools import ToolRegistry
from winlocalassistant.autonomy_capabilities import get_capability_catalog, build_mutable_mission_plan


def test_version_and_label_mentions_model_downloads():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 123)
    label = VERSION_LABEL.lower()
    assert f"v{__version__}" in VERSION_LABEL
    assert "voice" in label


def test_model_readiness_generates_confirmable_download_plan(tmp_path: Path):
    report = build_model_readiness("build code and analyse a screenshot", tmp_path)
    md = render_model_readiness(report)
    assert "ollama pull" in md
    assert "qwen2.5-coder:7b" in md
    assert "llama3.2-vision" in md
    assert "--confirm" in md


def test_model_install_is_dry_run_by_default(tmp_path: Path):
    result = install_model("coder", tmp_path, confirm=False)
    assert result["dry_run"] is True
    assert result["command"] == ["ollama", "pull", "qwen2.5-coder:7b"]
    assert "Dry run" in result["summary"]


def test_unsafe_model_name_is_rejected(tmp_path: Path):
    result = install_model("qwen; rm -rf .", tmp_path, confirm=False)
    assert result["ok"] is False


def test_tool_registry_exposes_model_download_tools(tmp_path: Path):
    cfg = AssistantConfig(workspace=str(tmp_path))
    reg = ToolRegistry(cfg)
    for name in ["model_readiness", "model_requirements", "model_download_plan", "model_install"]:
        assert name in reg.tools
    result = reg.call("model_readiness", goal="coding task")
    assert "Model Requirement" in result.data.get("message", "")


def test_core_routes_model_commands_without_mega_confirm(tmp_path: Path):
    app = AssistantCore(AssistantConfig(workspace=str(tmp_path)))
    out = app.handle_command("/model-requirements build a tiny app")
    assert "Nova Model Requirement" in out
    assert "Mega Test" not in out
    dry = app.handle_command("/model-install coder")
    assert "Dry run" in dry


def test_autonomy_capability_catalog_includes_model_dependency_management():
    names = {cap.name for cap in get_capability_catalog()}
    assert "model_dependency_management" in names
    plan = build_mutable_mission_plan("download the required model for a vision repair task")
    selected = [m.capability.name for m in plan.capabilities]
    assert "model_dependency_management" in selected
