from __future__ import annotations

from pathlib import Path

import pytest

from winlocalassistant.safety import resolve_inside_workspace


def _webui() -> str:
    return Path("winlocalassistant/webui.py").read_text(encoding="utf-8", errors="replace")


def test_webui_get_reports_path_protection_as_403_before_disconnect_catch() -> None:
    src = _webui()
    do_get = src[src.index("def do_GET(self) -> None:"):src.index("def _send_file(self, target: Path, name: str) -> None:")]
    permission_pos = do_get.index("except PermissionError as exc:")
    disconnect_pos = do_get.index("except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):")
    assert permission_pos < disconnect_pos
    assert 'self._send(403, f"Path blocked:' in do_get


def test_download_and_view_routes_still_use_workspace_path_protection() -> None:
    src = _webui()
    for marker in [
        'if path == "/download":',
        'if path == "/view":',
        'if path.startswith("/project-view/"):',
    ]:
        assert marker in src
    assert src.count("resolve_inside_workspace(Path(core.config.workspace), rel)") >= 3


def test_resolve_inside_workspace_blocks_parent_traversal(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    with pytest.raises(PermissionError):
        resolve_inside_workspace(workspace, "../outside.txt")


def run_all(verbose: bool = False) -> None:
    tests = [
        test_webui_get_reports_path_protection_as_403_before_disconnect_catch,
        test_download_and_view_routes_still_use_workspace_path_protection,
    ]
    for fn in tests:
        fn()
        if verbose:
            print(f"PASS {fn.__name__}")


if __name__ == "__main__":
    run_all(True)
