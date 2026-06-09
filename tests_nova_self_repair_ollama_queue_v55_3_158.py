from __future__ import annotations

import json
import threading
import time
import tempfile
from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.ollama import ollama_chat, ollama_busy_state
from winlocalassistant.self_repair_guardian import (
    build_mistake_learning_report,
    record_mistake,
    run_auto_self_repair,
    set_self_repair_enabled,
)
from winlocalassistant.tools import ToolRegistry


class _FakeResponse:
    def __init__(self, payload: str):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self) -> bytes:
        return self.payload.encode("utf-8")


def test_ollama_same_model_calls_are_queued_not_rejected(monkeypatch):
    calls: list[float] = []

    def fake_urlopen(req, timeout=None):
        calls.append(time.time())
        time.sleep(0.05)
        return _FakeResponse(json.dumps({"message": {"content": "ok"}}))

    monkeypatch.setattr("winlocalassistant.ollama.urllib.request.urlopen", fake_urlopen)
    out: list[str | None] = []

    def worker():
        out.append(ollama_chat("http://127.0.0.1:11434", "qwen3-coder:30b", [{"role": "user", "content": "hi"}], timeout=2, cooldown_sec=0, timeout_quarantine_sec=0))

    t1 = threading.Thread(target=worker)
    t2 = threading.Thread(target=worker)
    t1.start(); t2.start(); t1.join(); t2.join()

    assert out == ["ok", "ok"] or sorted(out) == ["ok", "ok"]
    assert len(calls) == 2
    assert calls[1] - calls[0] >= 0.04
    assert ollama_busy_state()["prompt_active"] is False


def test_self_repair_records_mistakes_and_reports_patterns():
    record_mistake("tool_result_failed", "Ollama timed out while model was busy", {"tool": "ai_create_project"})
    report = build_mistake_learning_report(".")
    assert report["ok"] is True
    assert report["mistakes_seen"] >= 1
    assert "model_concurrency_or_runtime" in report["buckets"]


def test_self_repair_tools_are_registered_and_permission_defaults_on():
    registry = ToolRegistry(AssistantConfig(workspace="."))
    for name in ["mistake_learning", "self_repair_status", "self_repair_permission", "self_repair_validate"]:
        assert name in registry.tools
    status = registry.call("self_repair_status")
    assert status.ok is True
    assert status.data["policy"]["enabled"] is True


def test_core_routes_self_repair_commands():
    core = AssistantCore(AssistantConfig(workspace=".", allow_mutating_tools=True))
    text = core.chat("/self-repair-status")
    assert "Nova self-repair status" in text
    text = core.chat("/mistake-learning")
    assert "Nova mistake learning report" in text


def test_auto_self_repair_runs_backup_and_validation_with_safe_commands(monkeypatch, tmp_path):
    root = tmp_path
    (root / "winlocalassistant").mkdir()
    (root / "winlocalassistant" / "__init__.py").write_text("", encoding="utf-8")
    (root / "app.py").write_text("print('ok')\n", encoding="utf-8")
    monkeypatch.setattr("winlocalassistant.self_repair_guardian.SAFE_VALIDATION_COMMANDS", [["python", "-c", "print('ok')"]])
    set_self_repair_enabled(True)
    report = run_auto_self_repair(root, "test safe self repair", apply=True)
    assert report["ok"] is True
    assert "docs/SELF_REPAIR_POLICY.md" in report["changed_files"]
    assert (root / "docs" / "SELF_REPAIR_POLICY.md").exists()
