from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.cohesion_engine import (
    VALIDATION_LADDER,
    ITERATIVE_LOOP,
    build_cohesion_report,
    render_cohesion_report_markdown,
    render_validation_ladder_markdown,
    render_iterative_development_markdown,
)


def test_cohesion_report_contains_self_architecture_validation_layers(tmp_path):
    report = build_cohesion_report(Path.cwd(), "improve Nova reliability")
    assert report.version
    assert 0 <= report.score <= 100
    assert "identity" in report.layers
    assert "architecture" in report.layers
    assert "validation" in report.layers
    text = render_cohesion_report_markdown(report)
    assert "Nova Cohesion Report" in text
    assert "Validation Ladder" in text
    assert "Iterative Development Loop" in text


def test_validation_ladder_and_iteration_protocol_expose_patch_docker_step():
    assert any("docker-validate-patch" in item["command"] for item in VALIDATION_LADDER)
    assert any(item["phase"] == "simulate" for item in ITERATIVE_LOOP)
    ladder = render_validation_ladder_markdown("test goal")
    loop = render_iterative_development_markdown("test goal")
    assert "/docker-validate-patch PATCH.diff" in ladder
    assert "/docker-validate-patch PATCH.diff" in loop


def test_new_commands_route_without_model_or_docker(tmp_path):
    cfg = AssistantConfig(workspace=str(Path.cwd()))
    core = AssistantCore(cfg)
    out = core.handle_command("/validation-ladder improve cohesion")
    assert "Nova Validation Ladder" in out
    out = core.handle_command("/iteration-plan improve cohesion")
    assert "Nova Iterative Development Protocol" in out
    out = core.handle_command("/cohesion-report improve cohesion")
    assert "Nova Cohesion Report" in out


def test_self_awareness_and_architecture_know_cohesion_module():
    self_src = Path("winlocalassistant/self_awareness.py").read_text(encoding="utf-8")
    arch_src = Path("winlocalassistant/architecture_audit.py").read_text(encoding="utf-8")
    core_src = Path("winlocalassistant/core.py").read_text(encoding="utf-8")
    assert "cohesion_engine.py" in self_src
    assert "cohesion_engine.py" in arch_src
    assert "/cohesion-report" in core_src
