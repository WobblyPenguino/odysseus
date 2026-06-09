from __future__ import annotations

from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore


def test_autonomous_release_gate_status_start_stop_routes(tmp_path: Path):
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True, local_model_timeout_sec=0, chat_model_timeout_sec=0))
    status = core.handle_command('/autonomous status')
    assert 'Autonomous' in status or 'autonomous' in status.lower()
    stop = core.handle_command('/autonomous stop')
    assert 'stop' in stop.lower() or 'autonomous' in stop.lower()
    guide = core.handle_command('/autonomous-guide')
    assert 'autonomous' in guide.lower()
