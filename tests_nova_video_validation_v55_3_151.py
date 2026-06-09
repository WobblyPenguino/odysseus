from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.nova_video import (
    build_video_execution_plan,
    plan_video_manifest,
    render_video_validation_markdown,
    validate_video_manifest,
    video_user_test_scenarios,
)
from winlocalassistant.tools import ToolRegistry


def test_video_manifest_validation_and_execution_plan():
    manifest = plan_video_manifest("Rainy alley. Robot builds a browser game.", project_id="video-test")
    validation = validate_video_manifest(manifest)
    execution = build_video_execution_plan(manifest)
    text = render_video_validation_markdown(validation, execution)
    assert validation["ok"] is True
    assert validation["shot_count"] >= 1
    assert execution["step_count"] >= len(manifest.shots) * 2
    assert "Execution plan" in text


def test_video_user_test_scenarios_cover_missing_backend():
    scenarios = video_user_test_scenarios()
    assert any(s["name"] == "backend_missing" for s in scenarios)
    assert any("manifest" in " ".join(s.get("expect", [])) for s in scenarios)


def test_video_tools_are_registered(tmp_path):
    reg = ToolRegistry(AssistantConfig(workspace=str(tmp_path)))
    plan = reg.call("video_plan", prompt="10 second Nova trailer", output_dir=str(tmp_path / "video_job"))
    assert plan.ok is True
    assert (tmp_path / "video_job" / "preview.avi").exists()
    assert (tmp_path / "video_job" / "preview.html").exists()
    assert reg.call("video_validate", prompt="10 second Nova trailer").ok is True
    assert reg.call("video_user_tests").ok is True


def test_video_commands_route_through_core(tmp_path):
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path)))
    assert "Nova Video Validation" in core.handle_command("/video-validate a tiny trailer")
    assert "Nova Video User Test" in core.handle_command("/video-user-test")
