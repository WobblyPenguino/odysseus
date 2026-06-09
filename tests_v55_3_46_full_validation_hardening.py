from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.feature_audit import build_feature_audit, feature_audit, run_feature_audit
from winlocalassistant.wla_doctor import run_wla_release_gate


def test_current_version_metadata_is_consistent():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 123)
    assert f"v{__version__}" in VERSION_LABEL
    readme = Path("README.md").read_text(encoding="utf-8")
    webui = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert f"Nova v{__version__}" in readme
    assert f"Nova v{__version__}" in webui


def test_no_stale_current_version_assertions_left_in_tests():
    release_tests = [Path("tests_release_hygiene.py"), Path("tests_report_hygiene.py"), Path("winlocalassistant/webui.py"), Path("README.md")]
    stale = []
    for path in release_tests:
        text = path.read_text(encoding="utf-8")
        if 'Nova v55.3.47' in text or '== \"55.3.47\"' in text or 'Nova v55.3.46' in text or '== \"55.3.46\"' in text:
            stale.append(path.name)
    assert not stale


def test_feature_audit_has_direct_aliases_and_passes():
    a = build_feature_audit(Path.cwd())
    b = feature_audit(Path.cwd())
    c = run_feature_audit(Path.cwd())
    assert a["ok"] is True
    assert b["ok"] is True
    assert c["ok"] is True
    assert a["implemented"] >= 10


def test_release_gate_defaults_include_latest_validation_test():
    src = Path("winlocalassistant/wla_doctor.py").read_text(encoding="utf-8")
    assert "tests_v55_3_48_sandbox_project_hardening.py" in src
    assert "tests_v55_3_47_dependency_system_test.py" in src


def test_release_gate_smoke_with_current_tests():
    payload = run_wla_release_gate(
        Path.cwd(),
        f"v{__version__} smoke",
        "python -m pytest -q tests_release_hygiene.py tests_report_hygiene.py",
    )
    assert payload["ok"] is True
    names = [row["name"] for row in payload["commands"]]
    assert "compileall" in names
    assert "custom_tests" in names
