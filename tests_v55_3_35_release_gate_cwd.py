from pathlib import Path

from winlocalassistant.wla_doctor import _run_gate_command


def test_release_gate_command_honours_cwd(tmp_path):
    marker = tmp_path / "marker.txt"
    cmd = ["python", "-c", "from pathlib import Path; Path('marker.txt').write_text('ok')"]
    result = _run_gate_command("cwd_test", cmd, timeout=30, cwd=tmp_path)
    assert result["ok"] is True
    assert marker.read_text() == "ok"
    assert result["cwd"] == str(tmp_path)
