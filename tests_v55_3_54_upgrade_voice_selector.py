from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.upgrade_planner import build_upgrade_radar, render_upgrade_radar


def test_v55_3_56_version_label_keeps_legacy_words():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 123)
    low = VERSION_LABEL.lower()
    assert f"v{__version__}" in VERSION_LABEL
    assert "voice" in low


def test_upgrade_radar_is_renderable_and_lists_optional_downloads():
    report = build_upgrade_radar(Path.cwd())
    text = render_upgrade_radar(report)
    assert report["ok"] is True
    assert "Playwright GUI smoke tests" in text
    assert "Ruff lint/format gate" in text
    assert "download" in text.lower()


def test_webui_has_voice_device_selector_and_refresh_controls():
    src = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "voiceDeviceSelect" in src
    assert "refreshVoiceDeviceSelect" in src
    assert "voiceAudioConstraint" in src
    assert "OverconstrainedError" in src
    assert "/upgrade-radar" in src


def test_optional_dev_tooling_scaffold_present():
    assert Path("pyproject.toml").exists()
    assert Path(".pre-commit-config.yaml").exists()
    assert Path("requirements-dev.txt").exists()
