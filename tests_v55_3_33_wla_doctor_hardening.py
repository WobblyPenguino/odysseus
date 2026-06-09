from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.wla_doctor import _version_from_init, run_wla_doctor


def test_wla_doctor_runs_and_writes_reports():
    payload = run_wla_doctor(Path('.'), 'release user testing')
    assert 'checks' in payload
    assert any(item['name'] == 'python_syntax' for item in payload['checks'])
    assert any(item['name'] == 'webui_inline_js_safety' for item in payload['checks'])
    assert Path(payload['markdown_path']).exists()
    assert Path(payload['json_path']).exists()


def test_wla_doctor_command_routes(tmp_path):
    cfg = AssistantConfig(workspace=str(tmp_path))
    core = AssistantCore(cfg)
    reply = core.handle_command('/nova-doctor release hardening')
    assert 'Nova Doctor Report' in reply
    assert 'Recommended next improvements' in reply


def test_webui_uses_dataset_for_attach_file_example():
    html = Path('winlocalassistant/webui.py').read_text(encoding='utf-8')
    assert 'data-command="/attach-file C:' in html
    assert "fillCommand('/attach-file C:" not in html


def test_readme_visible_label_matches_release():
    readme = Path('README.md').read_text(encoding='utf-8')
    assert f'# Nova v{__version__}' in readme
    assert f'v{__version__}' in VERSION_LABEL


def test_wla_doctor_version_reader_does_not_execute_init_code(tmp_path):
    package = tmp_path / 'winlocalassistant'
    package.mkdir()
    (package / '__init__.py').write_text("__version__ = '1.2.3'\nraise RuntimeError('should not execute')\n", encoding='utf-8')
    assert _version_from_init(tmp_path) == '1.2.3'
    assert "exec(" not in Path('winlocalassistant/wla_doctor.py').read_text(encoding='utf-8')
