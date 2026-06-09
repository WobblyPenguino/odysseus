from __future__ import annotations

"""Nova Arcade registry and local game metadata.

This module intentionally contains metadata and command renderers only. The
actual browser game runtime is injected by ``webui_arcade.py`` so future games
can be added by extending the registry without rewriting the core GUI shell.
"""

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import json


@dataclass(frozen=True)
class NovaArcadeGame:
    game_id: str
    name: str
    description: str
    icon: str
    launch_component: str
    status: str
    controls: str
    storage_key: str


GAMES: tuple[NovaArcadeGame, ...] = (
    NovaArcadeGame(
        game_id="system-runner",
        name="Nova: System Runner",
        description="Cyberpunk runner: steer the Nova core, dodge bugs/corruption, collect upgrade shards and save a local high score.",
        icon="◈",
        launch_component="window.NovaArcade.launch('system-runner')",
        status="playable-local",
        controls="Arrow keys or WASD to move. Collect yellow upgrades. Avoid magenta corruption blocks. P pauses/resumes.",
        storage_key="novaArcade.systemRunner.highScore",
    ),
)


def arcade_registry() -> dict[str, Any]:
    return {
        "ok": True,
        "framework": "Nova Arcade",
        "version": "v55.3.164-arcade-v1",
        "local_only": True,
        "games": [asdict(game) for game in GAMES],
        "extension_contract": {
            "required_fields": ["game_id", "name", "description", "icon", "launch_component", "status"],
            "where_to_add": "winlocalassistant/nova_arcade.py registry + winlocalassistant/webui_arcade.py component runtime",
            "safety": "Games must be local-only, no network calls, no arbitrary script injection, no project-file mutation.",
        },
    }


def render_arcade_registry(payload: dict[str, Any] | None = None) -> str:
    payload = payload or arcade_registry()
    lines = [
        "# Nova Arcade",
        "",
        "A local-only modular mini-game shelf embedded in Nova. Future games are added through the registry instead of rewriting the GUI.",
        "",
        f"Framework version: `{payload.get('version')}`",
        f"Local only: `{payload.get('local_only')}`",
        "",
        "## Games",
    ]
    for game in payload.get("games", []):
        lines += [
            f"### {game.get('icon', '•')} {game.get('name')}",
            f"- ID: `{game.get('game_id')}`",
            f"- Status: `{game.get('status')}`",
            f"- Description: {game.get('description')}",
            f"- Launch component: `{game.get('launch_component')}`",
            f"- Controls: {game.get('controls')}",
            "",
        ]
    lines += [
        "## GUI usage",
        "Click the `arcade` header button, or run `/arcade-launch system-runner` and then use the GUI launcher button.",
        "High score is stored in browser `localStorage`, not in backend project files.",
    ]
    return "\n".join(lines)


def render_arcade_launch(game_id: str = "system-runner") -> str:
    game_id = (game_id or "system-runner").strip().lower()
    game = next((g for g in GAMES if g.game_id == game_id or g.name.lower() == game_id), None)
    if not game:
        return render_arcade_registry() + f"\n\nUnknown game `{game_id}`."
    return (
        f"# Launch {game.name}\n\n"
        f"Status: `{game.status}`\n\n"
        f"Use the GUI header button `arcade`, then click **Launch {game.name}**.\n\n"
        f"Controls: {game.controls}\n\n"
        "This is a local browser mini-game. It does not modify Nova project files and does not call external services."
    )


def write_arcade_manifest(root: str | Path = ".") -> Path:
    root = Path(root)
    out = root / "docs" / "NOVA_ARCADE_MANIFEST.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(arcade_registry(), indent=2), encoding="utf-8")
    return out
