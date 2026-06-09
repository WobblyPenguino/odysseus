from __future__ import annotations

import tempfile
from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.tools import ToolRegistry
from winlocalassistant.project_brief import infer_project_build_brief, write_project_build_brief
from winlocalassistant.safe_io import atomic_write_bytes, atomic_write_text
from winlocalassistant.watchdog import heartbeat


def test_write_one_creates_new_files_after_atomic_write_refactor() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_write_one_atomic_") as tmp:
        workspace = Path(tmp) / "workspace"
        workspace.mkdir()
        cfg = AssistantConfig(workspace=str(workspace), allow_mutating_tools=True)
        tools = ToolRegistry(cfg)
        result = tools.write_file("new_file.txt", "hello world")
        assert result.ok, result.summary
        assert (workspace / "new_file.txt").read_text(encoding="utf-8") == "hello world"


def test_project_lifecycle_files_are_always_written() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_lifecycle_atomic_") as tmp:
        root = Path(tmp) / "project"
        root.mkdir()
        cfg = AssistantConfig(workspace=str(root), allow_mutating_tools=True)
        tools = ToolRegistry(cfg)
        manifest = {"goal": "make a notes app", "build_mode": "test", "main_file": "index.html", "run_command": "start .\\index.html"}
        tools._write_lifecycle_files(root, manifest, verify_result={"checks": [{"name": "stub", "ok": True}]}, status="verified")
        assert (root / "TEST_REPORT.md").exists()
        assert (root / "FINAL_OUTPUT.md").exists()
        assert "Status: verified" in (root / "FINAL_OUTPUT.md").read_text(encoding="utf-8")


def test_atomic_bytes_and_project_brief_writers_create_expected_files() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_atomic_bytes_brief_") as tmp:
        root = Path(tmp)
        binary = root / "artifact.bin"
        atomic_write_bytes(binary, b"abc")
        assert binary.read_bytes() == b"abc"
        text = root / "artifact.txt"
        atomic_write_text(text, "safe")
        assert text.read_text(encoding="utf-8") == "safe"
        brief = infer_project_build_brief("build a calculator with add subtract clear and history")
        md, js = write_project_build_brief(root, brief)
        assert md.exists() and js.exists()
        assert "Project Build Brief" in md.read_text(encoding="utf-8")


def test_watchdog_heartbeat_uses_atomic_status_writer() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_watchdog_atomic_") as tmp:
        workspace = Path(tmp) / "workspace"
        workspace.mkdir()
        cfg = AssistantConfig(workspace=str(workspace), allow_mutating_tools=False)
        data = heartbeat(cfg, workspace)
        assert data["workspace_exists"] is True
