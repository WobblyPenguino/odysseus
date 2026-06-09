from __future__ import annotations

import contextlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from winlocalassistant.config import AssistantConfig, CONFIG_PATH, APP_DIR
from winlocalassistant.core import AssistantCore
from winlocalassistant.projects import PROJECTS_PATH
import winlocalassistant.tools as tools_module


ROOT = Path(__file__).resolve().parent
TOPIC_WATCHERS_PATH = APP_DIR / "TOPIC_WATCHERS.json"


@contextlib.contextmanager
def restore_profile_files():
    paths = [CONFIG_PATH, PROJECTS_PATH, TOPIC_WATCHERS_PATH]
    snapshots: dict[Path, bytes | None] = {}
    for path in paths:
        snapshots[path] = path.read_bytes() if path.exists() else None
    try:
        cfg = AssistantConfig.load()
        cfg.allow_internet = False
        cfg.save()
        yield
    finally:
        for path, data in snapshots.items():
            if data is None:
                try:
                    path.unlink()
                except FileNotFoundError:
                    _missing_test_snapshot = path
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)


def run_process(args: list[str], stdin_text: str, timeout: int = 90) -> str:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    cp = subprocess.run(
        args,
        input=stdin_text,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        env=env,
    )
    output = (cp.stdout or "") + "\n" + (cp.stderr or "")
    assert cp.returncode == 0, output[-6000:]
    return output


def test_cli_command_flow() -> None:
    commands = "\n".join(
        [
            "/version",
            "/status",
            "/help",
            "/avatar",
            "/llm-status",
            "/reasoning",
            "/tool-help",
            "/tool-run caesar_decrypter => {khoor}",
            "/tool-run big_bold_reply => {hey}",
            '/tool-pipeline [{"tool":"tool_run","args":{"name":"big_bold_reply","args":"{pipeline works}"}}]',
            "/safe-script-demo something interesting",
            "/watch-topic local AI => https://hnrss.org/newest",
            "/topic-check local AI",
            "/exit",
            "",
        ]
    )
    with restore_profile_files():
        output = run_process([sys.executable, "app.py"], commands)
    assert "Nova CLI" in output
    from winlocalassistant import __version__
    assert f"Nova {__version__}" in output
    assert "Custom tool help" in output
    assert "Reasoning diagnostic" in output
    assert "Ran safe local script demo" in output
    assert "Topic watcher saved" in output
    assert "Internet access is disabled" in output
    assert "Expecting property name enclosed in double quotes" not in output
    assert "Extra data: line" not in output


def test_legacy_batch_delegates_to_start_here_without_interactive_choice() -> None:
    legacy = (ROOT / "start_windows_assistant.bat").read_text(encoding="utf-8", errors="replace")
    start = (ROOT / "START_NOVA_HERE.bat").read_text(encoding="utf-8", errors="replace")

    assert "START_NOVA_HERE.bat" in legacy
    assert "NOVA_START_CHOICE" in legacy
    assert "Choose 1, 2 or 3" not in legacy
    assert "start_nova_best_models.ps1" in start
    assert "-Mode web" in start


def test_cli_make_explicit_dodge_game_recovery_path() -> None:
    with tempfile.TemporaryDirectory(prefix="wla48_cli_game_") as tmp, restore_profile_files():
        library = Path(tmp) / "NovaProjects"
        library.mkdir(parents=True, exist_ok=True)
        cfg = AssistantConfig(workspace=str(library), allow_mutating_tools=True)
        core = AssistantCore(cfg)
        old_model_chat = tools_module.model_chat
        try:
            tools_module.model_chat = lambda *args, **kwargs: None
            reply = core.chat("make a dodge game")
        finally:
            tools_module.model_chat = old_model_chat

        assert "no files were written" not in reply.lower()
        assert "Created and verified project" in reply
        assert "Final file: index.html" in reply
        game_dirs = [p for p in library.iterdir() if p.is_dir()]
        assert game_dirs, reply
        game_root = game_dirs[0]
        assert (game_root / "index.html").exists()
        assert (game_root / "app.js").exists()
        node = shutil_which("node")
        if node:
            cp = subprocess.run([node, "--check", str(game_root / "app.js")], capture_output=True, text=True, timeout=30)
            assert cp.returncode == 0, (cp.stdout or "") + (cp.stderr or "")
        final_text = (game_root / "FINAL_OUTPUT.md").read_text(encoding="utf-8", errors="replace")
        assert "Main file: index.html" in final_text


def shutil_which(command: str) -> str | None:
    from shutil import which

    return which(command)


if __name__ == "__main__":
    test_cli_command_flow()
    test_legacy_batch_delegates_to_start_here_without_interactive_choice()
    test_cli_make_explicit_dodge_game_recovery_path()
    print("tests_cli_user_mode.py: PASS")
