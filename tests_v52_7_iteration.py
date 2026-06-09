from __future__ import annotations

import tempfile
from pathlib import Path

import winlocalassistant.tools as tools_module
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.tools import ToolRegistry
from tests_cli_user_mode import restore_profile_files


def test_explicit_dodge_recovery_still_passes_with_iteration_reports() -> None:
    with tempfile.TemporaryDirectory(prefix="wla527_dodge_") as tmp, restore_profile_files():
        library = Path(tmp) / "NovaProjects"
        library.mkdir(parents=True, exist_ok=True)
        cfg = AssistantConfig(workspace=str(library), allow_mutating_tools=True)
        core = AssistantCore(cfg)
        old_model_chat = tools_module.model_chat
        try:
            tools_module.model_chat = lambda *args, **kwargs: None
            reply = core.chat("make a dodge game")
        finally:
            tools_module.model_chat = old_model_chat
        project = library / "Canvasdodgegame"
        assert "Created and verified project" in reply
        assert (project / "PROJECT_ITERATION_LOG.jsonl").exists()
        assert (project / "PROJECT_VERIFICATION_REPORT.md").exists()
        assert "readme_claim_not_implemented" not in reply


def test_readme_progress_claim_is_satisfied_by_score_code() -> None:
    with tempfile.TemporaryDirectory(prefix="wla527_progress_claim_") as tmp:
        root = Path(tmp)
        (root / "index.html").write_text('<p id="instructions">Use arrows to dodge blocks and build score.</p><canvas id="gameCanvas"></canvas><button id="startBtn">Start</button><script src="app.js"></script>', encoding="utf-8")
        (root / "app.js").write_text("""
const canvas=document.getElementById('gameCanvas');
let score=0, player={x:1,y:1,w:10,h:10}, targets=[], hazards=[], blocks=[];
document.addEventListener('keydown', e => { player.x += 1; });
function collision(a,b){ return true; }
function update(){ score += 1; requestAnimationFrame(loop); }
function draw(){ canvas.getContext('2d').fillRect(player.x, player.y, player.w, player.h); }
function resetGame(){ score = 0; }
function loop(){ update(); draw(); }
function startGame(){ resetGame(); loop(); }
""", encoding="utf-8")
        (root / "README.md").write_text("# Game\nIncludes score/progress and restart instructions.", encoding="utf-8")
        registry = ToolRegistry(AssistantConfig(workspace=str(root), allow_mutating_tools=True))
        ok, problems = registry._static_acceptance_check(root, "make a dodge game")
        assert ok, problems


def test_created_artifact_summary_reads_absolute_written_paths_under_project() -> None:
    with tempfile.TemporaryDirectory(prefix="wla527_summary_abs_") as tmp:
        root = Path(tmp) / "Project"
        root.mkdir()
        app = root / "app.js"
        app.write_text("const score = 0; function loop(){ requestAnimationFrame(loop); }", encoding="utf-8")
        registry = ToolRegistry(AssistantConfig(workspace=str(root.parent), allow_mutating_tools=True))
        summary = registry._created_artifact_request_summary(root, "Project", {"goal": "make a game"}, [{"path": str(app)}])
    assert "requestAnimationFrame" in summary
    assert "app.js" in summary


def test_write_one_does_not_crash_when_target_is_outside_current_workspace() -> None:
    with tempfile.TemporaryDirectory(prefix="wla527_write_one_") as tmp:
        workspace = Path(tmp) / "workspace"
        target = Path(tmp) / "Project" / "index.html"
        target.parent.mkdir(parents=True)
        target.write_text("old", encoding="utf-8")
        registry = ToolRegistry(AssistantConfig(workspace=str(workspace), allow_mutating_tools=True))
        info = registry._write_one(target, "new", append=False)
    assert info["bytes"] == 3
