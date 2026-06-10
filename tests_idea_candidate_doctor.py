import json

from pathlib import Path

from tools.idea_candidate_doctor import main


def test_candidate_doctor_writes_report_for_current_config(tmp_path, monkeypatch):
    out = tmp_path / "doctor.md"
    monkeypatch.setattr(
        "sys.argv",
        [
            "idea_candidate_doctor.py",
            "--config",
            "local_ai_cycles/config/NOVA_IDEA_PROMOTION_CANDIDATES.json",
            "--out",
            str(out),
        ],
    )

    assert main() == 0
    text = out.read_text(encoding="utf-8")
    assert "# Nova Idea Candidate Doctor Latest" in text
    assert "## Counts" in text
    assert "## Next fresh candidate" in text
    assert "## Accepted candidates" in text
    assert "tiny-autodev-sandbox-action-plan-status-line-v1" in text


def test_candidate_doctor_can_run_as_direct_script(tmp_path):
    import subprocess
    import sys

    out = tmp_path / "doctor-script.md"
    result = subprocess.run(
        [
            sys.executable,
            "tools/idea_candidate_doctor.py",
            "--config",
            "local_ai_cycles/config/NOVA_IDEA_PROMOTION_CANDIDATES.json",
            "--out",
            str(out),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    text = out.read_text(encoding="utf-8")
    assert "# Nova Idea Candidate Doctor Latest" in text
    assert "candidate doctor accepted=" in result.stdout


def test_candidate_doctor_writes_machine_readable_json_report(tmp_path, monkeypatch):
    out = tmp_path / "doctor.md"
    json_out = tmp_path / "doctor.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "idea_candidate_doctor.py",
            "--config",
            "local_ai_cycles/config/NOVA_IDEA_PROMOTION_CANDIDATES.json",
            "--out",
            str(out),
            "--json-out",
            str(json_out),
        ],
    )

    assert main() == 0
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["accepted_count"] >= 1
    assert payload["rejected_count"] == 0
    assert "accepted_candidates" in payload
    assert "fresh_count" in payload
    assert "next_candidate" in payload


def test_candidate_doctor_is_report_only_by_default_for_rejected_candidates(tmp_path, monkeypatch):
    bad_config = tmp_path / "bad_candidates.json"
    bad_config.write_text('[{"Id": "bad candidate with spaces"}]', encoding="utf-8")

    out = tmp_path / "doctor.md"
    json_out = tmp_path / "doctor.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "idea_candidate_doctor.py",
            "--config",
            str(bad_config),
            "--out",
            str(out),
            "--json-out",
            str(json_out),
        ],
    )

    assert main() == 0
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["accepted_count"] == 0
    assert payload["rejected_count"] >= 1
