from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.feature_continuity import build_feature_continuity_audit

WEBUI = Path('winlocalassistant/webui.py')


def test_version_118_unified_voice_label():
    assert tuple(map(int, __version__.split('.'))) >= (55, 3, 118)
    assert f'v{__version__}' in VERSION_LABEL
    assert 'Hey Nova' in VERSION_LABEL
    assert 'live transcripts' in VERSION_LABEL or 'voice' in VERSION_LABEL


def test_always_listening_defaults_on_and_live_transcript_markers():
    src = WEBUI.read_text(encoding='utf-8')
    assert 'voiceMode:true' in src
    assert 'wakeWordEnabled:true' in src
    assert 'wlaWakeDefaultApplied' in src
    assert 'Always-listening is on by default' in src
    assert 'voiceLiveText' in src
    assert 'Hey Nova detected' in src
    assert "rec.interimResults=true" in src


def test_nova_orb_and_voice_wave_canvases_exist():
    src = WEBUI.read_text(encoding='utf-8')
    for marker in [
        'novaOrbPanel',
        'novaOrb',
        'setNovaOrb',
        'voiceWaveCanvas',
        'rightVoiceWaveCanvas',
        'novaSpeakWaveCanvas',
        'rightSpeakWaveCanvas',
        'startMicWave',
        'startSpeakWave',
    ]:
        assert marker in src


def test_panels_are_resizable_collapsible_and_edge_rail_is_offscreen():
    src = WEBUI.read_text(encoding='utf-8')
    assert 'edgeRailToggle' in src
    assert 'translateX(-52px)' in src
    assert 'translateX(calc(-100% - 28px))' in src
    assert 'translateX(calc(100% + 28px))' in src
    assert 'max-height:72vh' in src
    assert 'minmax(360px,1fr)' in src


def test_live_activity_has_single_bulk_delete_toolbar():
    src = WEBUI.read_text(encoding='utf-8')
    assert 'Delete selected logs' in src
    assert 'Delete selected run logs' not in src
    assert "let html=''" in src


def test_right_panel_is_integrated_not_tab_split():
    src = WEBUI.read_text(encoding='utf-8')
    assert 'integratedRight' in src
    assert 'Integrated right panel: state, output, Jarvis and editor are now one scrollable panel.' in src
    assert '.rightbar.integratedRight .inspectorTabs{display:none!important}' in src


def test_new_chat_is_easy_to_access():
    src = WEBUI.read_text(encoding='utf-8')
    assert 'New chat</button>' in src
    assert 'Starting a fresh chat view' in src
    assert "newChatSession()" in src


def test_tutorial_updated_for_voice_and_layout():
    src = WEBUI.read_text(encoding='utf-8')
    assert 'Nova voice orb' in src
    assert 'Sliding Nova rail' in src
    assert 'Unified right panel' in src
    assert 'waveforms show mic input and spoken replies' in src


def test_feature_continuity_knows_unified_voice_ux():
    payload = build_feature_continuity_audit(Path.cwd())
    names = {c['name'] for c in payload['checks']}
    assert 'webui:unified_voice_ux' in names
    assert payload['ok'], payload.get('failed')
