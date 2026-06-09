from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.feature_audit import build_feature_audit
from winlocalassistant.projects import register_project


def test_version_55_3_44_current():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 123)
    assert f"v{__version__}" in VERSION_LABEL


def test_feature_audit_passes_and_writes_reports(tmp_path):
    payload = build_feature_audit(Path.cwd())
    assert payload["ok"] is True
    names = {row["name"] for row in payload["checks"]}
    assert "spoken_audio_and_controls" in names
    assert "custom_quick_commands" in names
    assert "backend_conversations" in names
    assert "security_defensive_watch" in names
    assert Path(payload["markdown_path"]).exists()
    assert Path(payload["json_path"]).exists()


def test_feature_audit_command_route(tmp_path):
    cfg = AssistantConfig(workspace=str(tmp_path))
    core = AssistantCore(cfg)
    reply = core.handle_command("/feature-audit")
    assert "Requested Feature Audit" in reply
    assert "spoken_audio_and_controls" in reply


def test_release_gate_default_uses_current_regression_tests():
    src = Path("winlocalassistant/wla_doctor.py").read_text(encoding="utf-8")
    assert "tests_v55_3_44_validation_feature_audit.py" in src
    assert "tests_v55_3_31_autonomous_patch_promotion.py" not in src.split("default_tests =", 1)[1].split("]", 1)[0]


def test_project_target_ignores_transient_pytest_workspace(tmp_path, monkeypatch):
    real_project = tmp_path / "RealProject"
    real_project.mkdir()
    (real_project / "PROJECT_MANIFEST.json").write_text('{"goal":"real project"}', encoding="utf-8")
    register_project("RealProject", str(real_project), make_current=True)
    temp_workspace = tmp_path / "pytest-of-Daniel" / "pytest-999" / "test_case0"
    temp_workspace.mkdir(parents=True)
    cfg = AssistantConfig(workspace=str(temp_workspace))
    core = AssistantCore(cfg)
    reply = core._project_target_diagnostic("make a tiny useful app")
    assert "RealProject" in reply
    assert "pytest-999" in reply  # mentioned only as ignored transient path
    assert "ignored transient" in reply
