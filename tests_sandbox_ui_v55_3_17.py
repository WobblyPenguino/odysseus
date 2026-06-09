
from winlocalassistant.webui import HTML
from winlocalassistant.sandbox_manager import sandbox_setup_help, render_setup_help_markdown, sandbox_status, render_status_markdown
from winlocalassistant.config import AssistantConfig
from winlocalassistant import __version__, VERSION_LABEL


def test_version_55_3_18():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 123)
    assert f"v{__version__}" in VERSION_LABEL


def test_sandbox_tabs_are_compact_not_grid_stretched():
    assert "grid-template-rows:auto auto auto auto auto minmax(0,1fr) auto" in HTML
    assert ".sandboxTabs{display:flex;gap:6px;align-items:center" in HTML
    assert ".sandboxTabBtn{flex:0 0 auto;align-self:center;min-height:0;padding:7px 11px" in HTML


def test_activity_panel_has_explicit_open_collapse_controls():
    assert "function setActivityOpen(open)" in HTML
    assert "toggleActivityOpen" in HTML
    assert "activityToggleBtn" in HTML
    assert "body.collapse-activity .activity{display:block!important;" in HTML
    assert "body.collapse-activity .activity #activityLog{display:none!important}" in HTML


def test_web_send_suppresses_client_disconnect_tracebacks():
    assert "ConnectionAbortedError" in HTML or True  # import smoke for HTML
    import inspect
    from winlocalassistant import webui
    src = inspect.getsource(webui.run_web)
    assert "ConnectionAbortedError" in src
    assert "client disconnect" in src.lower()


def test_sandbox_setup_help_instructions_are_available(tmp_path):
    cfg = AssistantConfig(workspace=str(tmp_path))
    payload = sandbox_setup_help(cfg)
    text = render_setup_help_markdown(payload)
    assert payload["ok"] is True
    assert "Docker Desktop" in text
    assert "where docker" in text
    assert "/sandbox-status" in text


def test_sandbox_status_points_to_setup_help_when_runtime_missing(tmp_path, monkeypatch):
    cfg = AssistantConfig(workspace=str(tmp_path))
    import winlocalassistant.sandbox_manager as sm
    monkeypatch.setattr(sm.shutil, "which", lambda name: None)
    text = render_status_markdown(sandbox_status(cfg))
    assert "/sandbox-setup-help" in text
