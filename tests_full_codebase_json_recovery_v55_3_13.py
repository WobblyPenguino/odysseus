from pathlib import Path

from winlocalassistant.safe_io import atomic_append_text, read_json_file
from winlocalassistant.assistant_box import read_assistant_box
import winlocalassistant.assistant_box as assistant_box_module
from winlocalassistant.projects import load_projects
import winlocalassistant.projects as projects_module


def test_read_json_file_quarantines_corrupt_state(tmp_path: Path) -> None:
    state = tmp_path / "state.json"
    state.write_text("{not valid json", encoding="utf-8")
    data = read_json_file(state, {"ok": False}, expected_type=dict, quarantine=True)
    assert data == {"ok": False}
    backups = list(tmp_path.glob("state.json.invalid_json.corrupt_*.bak"))
    assert backups and backups[0].read_text(encoding="utf-8") == "{not valid json"


def test_atomic_append_text_preserves_multiple_appends(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.md"
    atomic_append_text(ledger, "one\n")
    atomic_append_text(ledger, "two\n")
    assert ledger.read_text(encoding="utf-8") == "one\ntwo\n"


def test_projects_corrupt_json_recovers_and_quarantines(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "projects.json"
    path.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(projects_module, "PROJECTS_PATH", path)
    assert load_projects() == {"current": "", "projects": {}}
    assert list(tmp_path.glob("projects.json.invalid_json.corrupt_*.bak"))


def test_assistant_box_corrupt_json_recovers_and_quarantines(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "assistant_message_box.json"
    path.write_text("{broken", encoding="utf-8")
    monkeypatch.setattr(assistant_box_module, "BOX_PATH", path)
    state = read_assistant_box()
    assert state["ok"] is True
    assert state["message"] == ""
    assert list(tmp_path.glob("assistant_message_box.json.invalid_json.corrupt_*.bak"))
