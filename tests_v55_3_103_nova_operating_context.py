from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.nova_operating_context import build_nova_operating_context, render_nova_operating_context, write_action_receipt
from winlocalassistant.tools import ToolRegistry


def test_nova_operating_context_contains_verification_strategy_and_files(tmp_path):
    (tmp_path / "app.js").write_text("requestAnimationFrame(()=>{}); // collision score restart", encoding="utf-8")
    ctx = build_nova_operating_context(tmp_path, goal="make a game about hair", last_failure="game_missing_collision")
    assert ctx["schema_version"] >= 1
    joined = "\n".join(ctx["verification_conditions"] + ctx["strategy_rules"])
    assert "collision" in joined.lower()
    assert "switch strategy" in joined.lower()
    assert ctx["recent_relevant_files"][0]["path"] == "app.js"
    rendered = render_nova_operating_context(ctx)
    assert "Nova Operating Context" in rendered
    assert "Verification conditions" in rendered


def test_tool_registry_exposes_nova_context(tmp_path):
    cfg = AssistantConfig(workspace=str(tmp_path))
    tools = ToolRegistry(cfg)
    result = tools.call("nova_context", goal="implement a safer retry loop", mode="preview")
    assert result.ok
    assert "Nova Operating Context" in result.data["message"]
    assert "verification_conditions" in result.data["context"]


def test_local_model_context_includes_operating_context(tmp_path):
    cfg = AssistantConfig(workspace=str(tmp_path))
    tools = ToolRegistry(cfg)
    text = tools._local_model_implementation_context(tmp_path, goal="fix looping game generation", last_reason="same rejection")
    assert "nova_operating_context" in text
    assert "action_receipt_contract" in text
    assert "same rejection" in text
    assert "switch strategy" in text.lower()


def test_action_receipt_writes_project_receipt(tmp_path):
    path, receipt = write_action_receipt(
        tmp_path,
        action="unit_test",
        goal="verify receipts",
        changed_files=["app.js"],
        validation=[{"name": "compile", "ok": True}],
        ok=True,
        notes="done",
    )
    assert path.exists()
    md = (tmp_path / "ACTION_RECEIPT.md").read_text(encoding="utf-8")
    assert "Action Receipt" in md
    assert "app.js" in md
    assert receipt["ok"] is True


def test_version_and_feature_continuity_markers_present():
    import winlocalassistant as wla
    webui = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    tools = Path("winlocalassistant/tools.py").read_text(encoding="utf-8")
    assert tuple(map(int, wla.__version__.split("."))) >= (55, 3, 113)
    assert "nova_context" in tools
    assert "loadAssistantBox" in webui
    assert "bulkDeleteSelectedProjects" in webui
    assert "deleteSelectedRuns" in webui
