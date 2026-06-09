from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.maintenance_validation import build_maintenance_validation, render_maintenance_validation
from winlocalassistant.tools import ToolRegistry


def test_maintenance_validation_detects_python310_incompatibility(tmp_path):
    package = tmp_path / "winlocalassistant"
    package.mkdir()
    (package / "bad.py").write_text("def identity[T](value):\n    return value\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("print('ok')\n", encoding="utf-8")

    payload = build_maintenance_validation(tmp_path, tool_names=["maintenance_validate", "validate_maintenance", "self_validate", "validation_ladder"])

    py310 = next(check for check in payload["checks"] if check["name"] == "python_310_compat")
    assert not py310["ok"]
    assert payload["blockers"]
    assert "Python 3.10 compatibility" in py310["summary"]


def test_maintenance_validation_current_repo_has_ladder_and_model_prompt(monkeypatch):
    monkeypatch.setenv("NOVA_ALLOW_DIFFUSERS_DOWNLOAD", "0")
    monkeypatch.delenv("NOVA_DIFFUSERS_MODEL", raising=False)

    payload = build_maintenance_validation(Path("."), tool_names=["maintenance_validate", "validate_maintenance", "self_validate", "validation_ladder"])
    markdown = render_maintenance_validation(payload)

    assert "python_310_compat" in markdown
    assert "Stable Validation Ladder" in markdown
    assert "python -m pytest" in markdown
    assert payload["local_model_validation"]["review_prompt"]


def test_maintenance_validate_is_registered_and_routed():
    registry = ToolRegistry(AssistantConfig())
    assert "maintenance_validate" in registry.tools
    assert "validate_maintenance" in registry.tools
    assert "self_validate" in registry.tools
    assert "validation_ladder" in registry.tools

    core = AssistantCore(AssistantConfig())
    out = core.handle_command("/maintenance-validate")
    assert "Nova Maintenance Validation" in out
    assert "Stable Validation Ladder" in out
    assert "Nova Validation Ladder" in core.handle_command("/validation-ladder improve Nova")
