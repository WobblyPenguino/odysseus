from pathlib import Path

from winlocalassistant import VERSION_LABEL, __version__
from winlocalassistant.webui import HTML


def test_v55_3_140_historical_dock_and_current_metadata_are_current():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 141)
    assert "v55.3.141" in VERSION_LABEL
    assert "voice cue" in VERSION_LABEL.lower()
    assert "v55.3.141" in Path("CHANGELOG.md").read_text(encoding="utf-8")
    assert "Nova_v55_3_141_voice_resize_coding_flow_20260602.zip" in Path("README.md").read_text(encoding="utf-8")


def test_odysseus_validation_dock_is_visible_and_review_only():
    assert "odysseusValidationDock" in HTML
    assert "Odysseus-style validation command dock" in HTML
    assert "/release-hygiene" in HTML
    assert "/architecture-audit" in HTML
    assert "/nova-eval-packs core" in HTML
    assert "/patch-impact-plan winlocalassistant/webui.py winlocalassistant/nova_odysseus_suite.py" in HTML
    assert "fillDatasetCommand(this)" in HTML
    dock_fragment = HTML.split('class="odysseusValidationDock"', 1)[1].split('</div>\n    </div>', 1)[0]
    assert "runDatasetCommand(this)" not in dock_fragment


def test_odysseus_launcher_uses_safe_binary_append_helper():
    suite = Path("winlocalassistant/nova_odysseus_suite.py").read_text(encoding="utf-8")
    safe_io = Path("winlocalassistant/safe_io.py").read_text(encoding="utf-8")
    assert "open_binary_append_handle(log_path)" in suite
    assert 'log_path.open("ab")' not in suite
    assert "def open_binary_append_handle" in safe_io
