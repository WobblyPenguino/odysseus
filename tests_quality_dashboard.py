from pathlib import Path

from winlocalassistant.quality_dashboard import build_quality_dashboard, render_quality_dashboard_markdown, write_quality_dashboard_report


def test_quality_dashboard_reports_version_and_workspace(tmp_path):
    (tmp_path / "index.html").write_text("<button>Run</button><script src='app.js'></script>", encoding="utf-8")
    (tmp_path / "app.js").write_text("let score=0; function update(){score++;} requestAnimationFrame(update);", encoding="utf-8")
    dash = build_quality_dashboard(tmp_path, "make a simple game")
    assert dash.version
    assert str(tmp_path) == dash.workspace
    assert any(item.name == "runtime probe" for item in dash.items)
    text = render_quality_dashboard_markdown(dash)
    assert "Nova Quality Dashboard" in text
    assert "Recommended next actions" in text


def test_quality_dashboard_writer_creates_markdown_and_json(tmp_path):
    md, js, dash = write_quality_dashboard_report(tmp_path, "generic project")
    assert md.exists()
    assert js.exists()
    assert dash.score >= 0
    assert "Nova Quality Dashboard" in md.read_text(encoding="utf-8")


def run_all() -> None:
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as d:
        test_quality_dashboard_reports_version_and_workspace(Path(d))
    with tempfile.TemporaryDirectory() as d:
        test_quality_dashboard_writer_creates_markdown_and_json(Path(d))
