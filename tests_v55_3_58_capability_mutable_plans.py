from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.autonomy_capabilities import build_mutable_mission_plan, render_capability_markdown, select_capabilities_for_goal
from winlocalassistant.autonomous_sequence import build_autonomous_tool_sequence, render_autonomous_sequence_markdown
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore


def test_version_label_keeps_required_words_and_new_focus():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 123)
    low = VERSION_LABEL.lower()
    assert f"v{__version__}" in VERSION_LABEL
    assert "codebase" in low


def test_capability_selection_matches_validation_and_sandbox_goal():
    matches = select_capabilities_for_goal("use linux sandbox to validate generated code without touching live files")
    names = [m.capability.name for m in matches]
    assert "sandbox_dev_copy" in names
    assert "candidate_validation" in names


def test_mutable_plan_has_prompt_specific_validation_contract():
    plan = build_mutable_mission_plan("make notes app with localStorage and JSON export")
    joined = "\n".join(plan.validation_contract).lower()
    assert "localstorage" in joined
    assert "export" in joined
    assert any("unrelated default" in x.lower() for x in plan.validation_contract)
    assert any(("switch" in ";".join(stage.adapt_if).lower()) or ("fails" in ";".join(stage.adapt_if).lower()) or ("low" in ";".join(stage.adapt_if).lower()) for stage in plan.stages)


def test_autonomous_sequence_exposes_capabilities_and_mutable_plan():
    plan = build_autonomous_tool_sequence("fix Nova validation and surgical repair")
    data = plan.to_dict()
    assert data["capability_matches"]
    assert data["mutable_plan"]["stages"]
    rendered = render_autonomous_sequence_markdown(plan)
    assert "Capability choices" in rendered
    assert "Mutable plan" in rendered
    assert "surgical_repair" in rendered or "surgical" in rendered.lower()


def test_core_commands_render_capability_and_mutable_plan(tmp_path):
    app = AssistantCore(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True))
    cap = app.handle_command("/autonomy-capabilities improve idle autonomous tools and plans")
    mut = app.handle_command("/mutable-plan make notes app with JSON export")
    assert "Capability Map" in cap
    assert "Selected capabilities" in cap
    assert "Mutable Nova Plan" in mut
    assert "Validation contract" in mut
