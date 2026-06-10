
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
