from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.core import AssistantCore
from winlocalassistant.config import AssistantConfig
from winlocalassistant.feature_audit import build_feature_audit
from winlocalassistant.regression_sweep import build_regression_sweep


def test_version_75_preserves_compatibility_words():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 123)
    label = VERSION_LABEL.lower()
    for word in ["voice", "codebase", "no-regression"]:
        assert word in label


def test_feature_audit_status_values_count_as_pass_in_chat_formatter():
    app = AssistantCore(AssistantConfig(workspace=str(Path.cwd())))
    payload = build_feature_audit(Path.cwd())
    checks = payload.get("checks", [])
    assert checks
    lines = []
    app._append_project_verification_summary(lines, {"checks": checks})
    joined = "\n".join(lines)
    assert "Verification: 0/" not in joined
    assert "FAIL spoken_audio_and_controls" not in joined


def test_regression_sweep_checks_command_and_tool_coverage():
    app = AssistantCore(AssistantConfig(workspace=str(Path.cwd())))
    payload = build_regression_sweep(Path.cwd(), app=app)
    names = {c["name"] for c in payload["checks"]}
    assert "autonomy_tool_registry" in names
    assert "core_command_visibility" in names
    assert "feature_audit_chat_formatter" in names


def test_autonomy_catalog_knows_regression_sweep():
    from winlocalassistant.autonomy_capabilities import select_capabilities_for_goal

    matches = select_capabilities_for_goal("check no functionality regressed and run a whole codebase regression sweep", limit=8)
    names = {m.capability.name for m in matches}
    assert "regression_sweep" in names
