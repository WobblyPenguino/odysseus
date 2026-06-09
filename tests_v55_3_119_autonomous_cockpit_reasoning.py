from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.feature_continuity import build_feature_continuity_audit

WEBUI = Path('winlocalassistant/webui.py')
CORE = Path('winlocalassistant/core.py')


def test_version_119_autonomous_cockpit_label():
    assert tuple(map(int, __version__.split('.'))) >= (55, 3, 119)
    assert f'v{__version__}' in VERSION_LABEL
    assert 'autonomous cockpit' in VERSION_LABEL
    assert 'self-validation' in VERSION_LABEL


def test_autonomous_live_panel_is_scrollable_subwindow_not_huge_list():
    src = WEBUI.read_text(encoding='utf-8')
    for marker in [
        '#autonomousLivePanel',
        'max-height:clamp(230px,38vh,560px)',
        'autonomousCockpit',
        'autoSubWindow',
        'autoScroll',
        'autoEventScroller',
        'autoPlanScroll',
        'Scrollable reasoning timeline',
        'Latest autonomous events',
    ]:
        assert marker in src


def test_autonomous_current_thought_and_reasoning_timeline_are_rendered():
    src = WEBUI.read_text(encoding='utf-8')
    for marker in [
        'autonomousThoughtFallback',
        'autonomousThoughtRows',
        'renderAutonomousThoughtItem',
        'Current autonomous thinking/status',
        'Self-validation:',
        'current_thought',
        'current_self_validation',
        'autonomous_thoughts',
    ]:
        assert marker in src


def test_backend_records_safe_visible_autonomous_thoughts():
    core = AssistantCore(AssistantConfig(workspace='.'))
    core._set_autonomous_state(current_run_id='test-run', cycle=1)
    core._autonomous_event('act_start', 'Starting: Test compile', {'tool': 'runtime_self_check', 'timeout_sec': 30})
    state = core.autonomous_status_data()
    assert state['current_thought']
    assert state['current_self_validation']
    assert state['autonomous_thoughts']
    assert 'bounded' in state['current_self_validation'] or 'verify' in state['current_self_validation'].lower()


def test_autonomous_run_alias_starts_mode_instead_of_usage_error():
    src = CORE.read_text(encoding='utf-8')
    assert '"run", "go"' in src
    assert 'start/run [goal]' in src


def test_feature_continuity_knows_autonomous_cockpit_reasoning():
    payload = build_feature_continuity_audit(Path.cwd())
    names = {c['name'] for c in payload['checks']}
    assert 'webui:autonomous_cockpit_reasoning' in names
    assert payload['ok'], payload.get('failed')
