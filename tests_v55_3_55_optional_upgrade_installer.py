from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.optional_upgrade_installer import (
    build_optional_upgrade_status,
    install_optional_upgrade,
    render_optional_upgrade_status,
)


def test_v55_3_56_version_label_keeps_legacy_words_and_new_upgrade_words():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 123)
    label = VERSION_LABEL.lower()
    assert f"v{__version__}" in VERSION_LABEL
    assert "voice" in label


def test_optional_upgrade_status_lists_allowlisted_downloads():
    report = build_optional_upgrade_status(Path.cwd())
    text = render_optional_upgrade_status(report)
    keys = {item["key"] for item in report["items"]}
    assert {"ruff", "precommit", "playwright"}.issubset(keys)
    assert "/upgrade-install ruff --confirm" in text
    assert "explicit `--confirm`" in text


def test_upgrade_install_dry_run_does_not_install():
    result = install_optional_upgrade("ruff", Path.cwd(), confirm=False)
    assert result["ok"] is True
    assert result["dry_run"] is True
    assert "pip" in result["install_command_text"]
    assert "ruff" in result["install_command_text"]


def test_upgrade_install_unknown_is_rejected():
    result = install_optional_upgrade("unknown-heavy-thing", Path.cwd(), confirm=False)
    assert result["ok"] is False
    assert "available" in result


def test_webui_voice_setup_wizard_is_present():
    src = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "showVoiceSetupWizard" in src
    assert "Voice setup wizard" in src
    assert "WH-1000" in src
    assert "microphonePermission" in src


def test_core_exposes_optional_upgrade_commands():
    src = Path("winlocalassistant/core.py").read_text(encoding="utf-8")
    assert '"/optional-upgrades"' in src
    assert '"/upgrade-install"' in src
    assert "render_optional_upgrade_status" in src
