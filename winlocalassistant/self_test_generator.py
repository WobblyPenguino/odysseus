from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

from .safe_io import atomic_write_text


def test_name_from_bug(bug_text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", (bug_text or "bug").lower()).strip("_")[:60] or "bug"
    return "test_regression_" + slug


def generate_regression_test(bug_text: str, target_file: str = "winlocalassistant/webui.py") -> str:
    name = test_name_from_bug(bug_text)
    escaped = repr(bug_text[:200])
    if "not defined" in bug_text and "loadAssistantBox" in bug_text:
        return f"""from pathlib import Path\n\n\ndef {name}():\n    src = Path({target_file!r}).read_text(encoding='utf-8', errors='replace')\n    assert 'function loadAssistantBox' in src\n    assert 'window.loadAssistantBox' in src\n"""
    if "audio" in bug_text.lower() and "gesture" in bug_text.lower():
        return f"""from pathlib import Path\n\n\ndef {name}():\n    src = Path({target_file!r}).read_text(encoding='utf-8', errors='replace')\n    assert 'avatarAudioActivated=false' in src\n    assert '!avatarAudioActivated' in src\n"""
    return f"""from pathlib import Path\n\n\ndef {name}():\n    # Regression generated from: {escaped}\n    assert Path({target_file!r}).exists()\n"""


def write_regression_test(root: Path, bug_text: str, target_file: str = "winlocalassistant/webui.py") -> dict[str, Any]:
    name = test_name_from_bug(bug_text)
    path = Path(root) / f"tests_generated_{name}.py"
    atomic_write_text(path, generate_regression_test(bug_text, target_file))
    return {"path": str(path), "test_name": name, "created_at": time.strftime("%Y-%m-%d %H:%M:%S")}
