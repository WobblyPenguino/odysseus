from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL


def test_v55_3_56_version_label_keeps_legacy_words_and_review_words():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 123)
    label = VERSION_LABEL.lower()
    assert f"v{__version__}" in VERSION_LABEL
    assert "codebase" in label
    assert "packaging" in label


def test_release_hygiene_detects_cache_artifacts_in_fixture(tmp_path):
    from winlocalassistant.release_hygiene import find_release_hygiene_findings, build_release_hygiene_report

    cache = tmp_path / "winlocalassistant" / "__pycache__"
    cache.mkdir(parents=True)
    (cache / "core.cpython-313.pyc").write_bytes(b"cache")
    findings = find_release_hygiene_findings(tmp_path)
    assert any(f.kind == "cache_directory" for f in findings)
    assert any(f.kind == "compiled_python" for f in findings)
    report = build_release_hygiene_report(tmp_path)
    assert report["ok"] is False
    assert "package artifact" in report["summary"]


def test_release_hygiene_command_is_routed():
    src = Path("winlocalassistant/core.py").read_text(encoding="utf-8")
    assert '"/release-hygiene"' in src
    assert "build_release_hygiene_report" in src


def test_webui_filters_temp_pytest_cache_file_focus_from_live_ui():
    src = Path('winlocalassistant/webui.py').read_text(encoding='utf-8')
    assert 'function isRelevantAiFocusPath' in src
    assert 'pytest-of-' in src
    assert '__pycache__' in src
    assert '.pytest_cache' in src
    assert 'No relevant project file focus yet' in src


def test_readme_references_current_release_zip_name():
    readme = Path('README.md').read_text(encoding='utf-8')
    assert f"Nova_v{__version__.replace('.', '_')}" in readme
    assert 'Nova_v55_3_12_safe_io_append_log_integrity.zip' not in readme
