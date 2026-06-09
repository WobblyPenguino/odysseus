from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.config import AssistantConfig
from winlocalassistant.development_governor import build_strategy_decision, build_validation_evidence
from winlocalassistant.tools import ToolRegistry


def test_version_55_3_105_markers_are_current():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 113)
    assert f"v{__version__}" in VERSION_LABEL
    src = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert __version__ in src


def test_strategy_governor_switches_after_repeated_failure():
    attempts = [
        {"attempt": 1, "status": "validation_failed", "reason": "game_missing_collision"},
        {"attempt": 2, "status": "validation_failed", "reason": "game_missing_collision"},
    ]
    decision = build_strategy_decision("make a game about hair", last_failure="game_missing_collision", attempts=attempts)
    assert decision["route"] in {"switch_strategy", "template_or_recipe_fallback"}
    assert decision["repeated_failure"] is True
    assert any("deterministic" in x or "surgical" in x for x in decision["next_actions"])


def test_validation_evidence_checks_game_behaviour(tmp_path):
    (tmp_path / "index.html").write_text('<canvas id="game"></canvas><script src="app.js"></script>', encoding="utf-8")
    (tmp_path / "README.md").write_text("# Test game\n", encoding="utf-8")
    (tmp_path / "app.js").write_text(
        """
const canvas=document.getElementById('game');
let score=0; let gameOver=false; const player={x:0,y:0,w:10,h:10}; const target={x:5,y:5,w:10,h:10};
function rectsOverlap(a,b){return a.x<b.x+b.w && a.x+a.w>b.x && a.y<b.y+b.h && a.y+a.h>b.y;}
function update(){ if(rectsOverlap(player,target)){ score += 1; } requestAnimationFrame(update); }
document.addEventListener('keydown',()=>{});
function restart(){ score=0; gameOver=false; }
update();
""",
        encoding="utf-8",
    )
    evidence = build_validation_evidence(tmp_path, goal="make a game")
    assert evidence["ok"], evidence
    names = {c["name"] for c in evidence["checks"]}
    assert "game_collision" in names
    assert "game_loop" in names


def test_tool_registry_exposes_strategy_and_evidence_tools(tmp_path):
    registry = ToolRegistry(AssistantConfig(workspace=str(tmp_path)))
    assert "development_strategy" in registry.tools
    assert "validation_evidence" in registry.tools
    result = registry.call("development_strategy", goal="fix game", last_failure="game_missing_collision")
    assert result.ok
    assert "surgical_recipe_first" in str(result.data) or "switch_strategy" in str(result.data)
    evidence = registry.call("validation_evidence", path=".", goal="current project")
    assert "evidence" in evidence.data


def test_local_model_context_includes_strategy_and_validation_evidence(tmp_path):
    registry = ToolRegistry(AssistantConfig(workspace=str(tmp_path)))
    text = registry._local_model_implementation_context(tmp_path, goal="make a game about hair", last_reason="game_missing_collision")
    assert "development_strategy" in text
    assert "validation_evidence" in text
    assert "patch" in text.lower()
