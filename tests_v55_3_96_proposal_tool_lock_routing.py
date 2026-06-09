from pathlib import Path

from winlocalassistant import __version__
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.custom_tools import list_custom_tools
from winlocalassistant.improvement_roadmap import complete_next_improvements


def test_version_bumped_for_v96_root_cause_hardening():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 113)


def test_prompt_lock_classification_allows_project_commands(tmp_path):
    cfg = AssistantConfig(workspace=str(tmp_path))
    app = AssistantCore(cfg)
    assert app._can_run_without_chat_lock('/project-open Filescript') is True
    assert app._can_run_without_chat_lock('/project-delete Test --confirm') is True
    assert app._can_run_without_chat_lock('/tool-run html_reference_checker => {}') is True
    assert app._can_run_without_chat_lock('write me a normal chat reply') is False


def test_tool_create_refresh_round_trip(tmp_path, monkeypatch):
    import winlocalassistant.custom_tools as ct
    tool_dir = tmp_path / 'custom_tools'
    monkeypatch.setattr(ct, 'CUSTOM_TOOLS_DIR', tool_dir)
    monkeypatch.setattr(ct, 'CUSTOM_TOOLS_MANIFEST', tool_dir / 'manifest.json')
    monkeypatch.setattr(ct, 'CUSTOM_TOOL_PROPOSALS', tool_dir / 'proposals.json')
    import winlocalassistant.tools as tools_mod
    monkeypatch.setattr(tools_mod, 'list_custom_tools', ct.list_custom_tools)
    monkeypatch.setattr(tools_mod, 'run_custom_tool', ct.run_custom_tool)
    monkeypatch.setattr(tools_mod, 'save_custom_tool', ct.save_custom_tool)
    monkeypatch.setattr(tools_mod, 'refresh_custom_tool_registry', ct.refresh_custom_tool_registry)
    monkeypatch.setattr(tools_mod, 'mark_custom_tool_tested', ct.mark_custom_tool_tested)
    cfg = AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True)
    app = AssistantCore(cfg)
    res = app.tools.call('tool_create', goal='think of a new custom tool that would be useful to yourself and then create using your commands')
    assert res.ok, res.data
    name = res.data['name']
    refreshed = app.tools.call('custom_tools')
    assert any(t['name'] == name for t in refreshed.data['tools'])
    assert app.tools.call('tool_test', name=name).ok
    assert app.tools.call('tool_run', name=name, args={'subdir': '.'}).ok


def test_codebase_audit_default_target_is_wla_source(tmp_path):
    cfg = AssistantConfig(workspace=str(tmp_path))
    app = AssistantCore(cfg)
    res = app.tools.call('codebase_integrity_audit', path='__wla_source__')
    assert res.data['target']['target_type'] == 'wla_source'
    assert 'winlocalassistant' in res.data['markdown_path'] or res.data['target']['target_type'] == 'wla_source'


def test_implement_improvements_requires_real_changes_and_validation(tmp_path):
    (tmp_path / 'winlocalassistant').mkdir()
    (tmp_path / 'winlocalassistant' / '__init__.py').write_text('__version__="x"\n', encoding='utf-8')
    (tmp_path / 'app.py').write_text('print("ok")\n', encoding='utf-8')
    payload = complete_next_improvements(tmp_path, 'improve Nova reliability', confirm=True)
    assert payload['status'] in {'implemented', 'no_verified_change'}
    if payload['status'] == 'implemented':
        assert payload['changed_files']
        assert payload['validation_output']
    else:
        assert not payload.get('completed') or payload['completed'][0]['status'] != 'implemented'


def test_autonomous_create_tool_acceptance_rejects_no_new_tool(tmp_path):
    cfg = AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True)
    app = AssistantCore(cfg)
    before = {t.get('name') for t in list_custom_tools() if t.get('exists')}
    ok, evidence = app._autonomous_create_tool_acceptance(before, 'create a useful tool')
    assert ok is False
    assert 'No new enabled custom tool' in evidence.get('reason', '')
