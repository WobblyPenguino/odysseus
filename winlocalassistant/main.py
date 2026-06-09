from __future__ import annotations

import argparse
import sys
from pathlib import Path
from .core import AssistantCore
from .webui import run_web


def _configure_console_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if not callable(reconfigure):
            continue
        try:
            reconfigure(errors="replace")
        except (OSError, ValueError):
            pass


def main() -> None:
    _configure_console_output()
    parser = argparse.ArgumentParser(description="Nova: local Windows assistant with planning, tools and self-verification.")
    parser.add_argument("--web", action="store_true", help="Run browser UI on localhost.")
    parser.add_argument("--api", action="store_true", help="Run optional FastAPI bridge on localhost.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Optional one-shot Nova command, e.g. /nova-mega-test --confirm")
    args = parser.parse_args()

    core = AssistantCore.load()
    cwd = Path.cwd().resolve()
    if (cwd / "app.py").exists() and (cwd / "winlocalassistant").is_dir():
        core.config.workspace = str(cwd)
        core.tools.config = core.config
    if args.web:
        run_web(core, host=args.host, port=args.port)
        return
    if args.api:
        from .nova_api import run_api
        run_api(core, host=args.host, port=args.port)
        return
    if args.command:
        command = " ".join(args.command).strip()
        if command:
            timer = getattr(core, "_run_with_thinking_timer", None)
            if command.startswith("/"):
                fn = core.handle_command
            else:
                fn = core.chat
            if callable(timer):
                print(timer(fn, command))
            elif command.startswith("/"):
                print(core.handle_command(command))
            else:
                print(core.chat(command))
            return
    core.run_cli()
