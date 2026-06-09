from pathlib import Path
from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.prompt_test_compiler import build_prompt_contract, validate_contract
from winlocalassistant.candidate_tournament import build_candidate_tournament
from winlocalassistant.repair_engine_v2 import build_repair_plan
from winlocalassistant.mcp_security import inspect_mcp_security
from winlocalassistant.mission_planner_v2 import create_mission, mission_step
from winlocalassistant.model_output_coach import analyze_model_output
from winlocalassistant.env_profiles import build_env_profile
from winlocalassistant.benchmark_migration import benchmark_system
from winlocalassistant.project_state_db import append_project_state, load_project_state
from winlocalassistant.regression_memory import add_regression, load_regressions
from winlocalassistant.core import AssistantCore
from winlocalassistant.config import AssistantConfig


def test_v55_3_70_metadata_preserves_all_release_words():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 123)
    label = VERSION_LABEL.lower()
    for word in ['wake','voice','packaging','codebase','regression']:
        assert word in label


def test_prompt_contract_and_validation_detect_notes_requirements(tmp_path):
    (tmp_path/'index.html').write_text('<script src="app.js"></script><button onclick="exportNotes()">Export</button>', encoding='utf-8')
    (tmp_path/'app.js').write_text('function exportNotes(){localStorage.setItem("notes", JSON.stringify([])); const b=new Blob([JSON.stringify([])], {type:"application/json"});}', encoding='utf-8')
    (tmp_path/'README.md').write_text('notes app with export', encoding='utf-8')
    contract = build_prompt_contract('make a tiny useful local notes app with localStorage and JSON export')
    assert 'export notes as JSON' in contract['must_have']
    result = validate_contract('make a tiny useful local notes app with localStorage and JSON export', tmp_path)
    assert result['forbidden_hits'] == []


def test_candidate_tournament_recommends_a_winner():
    payload = build_candidate_tournament('make a tiny useful local notes app with localStorage and JSON export')
    assert payload['winner']
    assert len(payload['candidates']) >= 3
    assert payload['candidates'][0]['score']['overall_percent'] >= payload['candidates'][-1]['score']['overall_percent']


def test_repair_engine_classifies_wrong_domain():
    plan = build_repair_plan('.', 'Dodge Game default appeared even though the user did not request a dodge game')
    assert plan['failure_type'] == 'wrong_domain'
    assert any('template' in step or 'prompt-specific' in step for step in plan['steps'])


def test_connector_mission_model_env_project_regression_helpers(tmp_path):
    assert inspect_mcp_security()['policy']['read_only_tools'] is True
    mission = create_mission('improve file building')
    assert 'prompt-tests' in mission['tools_allowed']
    assert mission_step().get('next')
    coach = analyze_model_output('notes app', '```json\n{"files":{"index.html":"<h1>ok</h1>"}}\n```')
    assert coach['fenced'] is True
    assert build_env_profile('minimal')['profile'] == 'minimal'
    assert 'python' in benchmark_system()
    append_project_state(tmp_path, 'failure', 'example failure')
    assert load_project_state(tmp_path)['validation_failures']
    item = add_regression('test regression memory entry')
    assert any(r['id'] == item['id'] for r in load_regressions())


def test_core_routes_for_major_upgrade_commands(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    app = AssistantCore(AssistantConfig(workspace=str(tmp_path)))
    commands = [
        '/prompt-contract notes app with export',
        '/candidate-tournament notes app with export',
        '/repair-plan Dodge Game default appeared',
        '/trace-timeline',
        '/mcp-risk-report',
        '/mission-create improve file building',
        '/model-output-coach notes app',
        '/env-profile minimal',
        '/benchmark-system',
        '/project-state',
        '/regression-list',
    ]
    for command in commands:
        out = app.chat(command)
        assert isinstance(out, str) and len(out) > 20
