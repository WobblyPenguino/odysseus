from __future__ import annotations

import json
import tempfile
from pathlib import Path

import winlocalassistant.self_awareness as sa
from winlocalassistant.self_awareness import build_self_awareness_report, render_self_awareness_markdown, write_self_awareness_report
from winlocalassistant.core import AssistantCore
from winlocalassistant.config import AssistantConfig


def test_self_awareness_report_contains_core_capabilities() -> None:
    report = build_self_awareness_report(Path('.'), 'improve autonomous behaviour')
    names = {cap.name for cap in report.capabilities if cap.status == 'present'}
    assert 'autonomous failure memory' in names
    assert 'action watcher' in names
    assert 'planning dashboard' in names
    assert 'plain-English command router' in names
    assert 'iterative coding loop' in names
    assert 'manifest-first video planning' in names
    assert any('self-improve' in item.lower() for item in report.safety_boundaries)
    assert report.recommended_next_actions


def test_self_awareness_markdown_has_expected_sections() -> None:
    md = render_self_awareness_markdown(build_self_awareness_report(Path('.')))
    for heading in ['# Nova Self-Awareness Report', '## Identity', '## Capability Inventory', '## Safety Boundaries', '## Known Limitations', '## Recommended Next Actions']:
        assert heading in md
    assert 'Nova' in md


def test_write_self_awareness_report_creates_markdown_and_json() -> None:
    with tempfile.TemporaryDirectory(prefix='wla_self_awareness_') as tmp:
        old_app_dir = sa.APP_DIR
        try:
            sa.APP_DIR = Path(tmp)
            md, js, report = write_self_awareness_report(Path('.'), 'check capabilities')
            assert md.exists()
            assert js.exists()
            data = json.loads(js.read_text(encoding='utf-8'))
            assert data['version'] == report.version
            assert data['capabilities']
            assert 'Safety Boundaries' in md.read_text(encoding='utf-8')
        finally:
            sa.APP_DIR = old_app_dir


def test_self_awareness_command_returns_report_text() -> None:
    with tempfile.TemporaryDirectory(prefix='wla_self_awareness_cmd_') as tmp:
        old_app_dir = sa.APP_DIR
        try:
            sa.APP_DIR = Path(tmp)
            cfg = AssistantConfig(workspace=str(Path(tmp)))
            core = AssistantCore(cfg)
            text = core.chat('/self-awareness improve autonomous planning')
            assert 'Nova Self-Awareness Report' in text
            assert 'Capability Inventory' in text
            assert 'Report written' in text
        finally:
            sa.APP_DIR = old_app_dir


def test_help_and_webui_expose_self_awareness() -> None:
    core_text = Path('winlocalassistant/core.py').read_text(encoding='utf-8')
    webui_text = Path('winlocalassistant/webui.py').read_text(encoding='utf-8')
    assert '/self-awareness' in core_text
    assert 'Self-awareness' in webui_text


def run_all(verbose: bool = False) -> None:
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith('test_') and callable(fn)]
    for name, fn in tests:
        fn()
        if verbose:
            print(f'PASS {name}')
