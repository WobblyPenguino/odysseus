from __future__ import annotations

from pathlib import Path

from winlocalassistant import __version__


def test_self_awareness_reports_do_not_overwrite_when_requested_quickly(tmp_path, monkeypatch):
    import winlocalassistant.self_awareness as sa

    monkeypatch.setattr(sa, "APP_DIR", tmp_path)
    # Force identical time source; filename must still differ via suffix.
    monkeypatch.setattr(sa.time, "time", lambda: 12345.0)

    md1, js1, _ = sa.write_self_awareness_report(tmp_path, "first")
    md2, js2, _ = sa.write_self_awareness_report(tmp_path, "second")

    assert md1 != md2
    assert js1 != js2
    assert md1.exists() and md2.exists()
    assert js1.exists() and js2.exists()
    assert len(list((tmp_path / "self_awareness").glob("self_awareness_*.md"))) == 2


def test_quality_dashboard_reports_do_not_overwrite_when_requested_quickly(tmp_path, monkeypatch):
    import winlocalassistant.quality_dashboard as qd

    monkeypatch.setattr(qd, "APP_DIR", tmp_path)
    monkeypatch.setattr(qd.time, "time", lambda: 12345.0)

    md1, js1, _ = qd.write_quality_dashboard_report(tmp_path, "first")
    md2, js2, _ = qd.write_quality_dashboard_report(tmp_path, "second")

    assert md1 != md2
    assert js1 != js2
    assert md1.exists() and md2.exists()
    assert js1.exists() and js2.exists()
    assert len(list((tmp_path / "quality_dashboards").glob("quality_dashboard_*.md"))) == 2


def test_webui_top_quick_actions_do_not_duplicate_self_awareness_button():
    html = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert html.count("quick('/self-awareness')") == 1
    assert f"Nova v{__version__}" in html
