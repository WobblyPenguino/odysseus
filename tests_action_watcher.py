from __future__ import annotations

import json
import tempfile
from pathlib import Path

from winlocalassistant.action_watcher import evaluate_action_risk, record_action_outcome, requires_user_approval, should_block_repeated_action


def test_watcher_allows_read_only_status_action() -> None:
    decision = evaluate_action_risk({"name": "quality_dashboard", "category": "report"})
    assert decision.allowed is True
    assert decision.risk == "low"
    assert decision.requires_approval is False


def test_watcher_blocks_protected_self_improve_action() -> None:
    decision = evaluate_action_risk({"name": "self-improve", "command": "/self-improve rewrite core.py", "target": "winlocalassistant/core.py"})
    assert decision.allowed is False
    assert decision.risk == "high"
    assert any("protected" in r or "self" in r for r in decision.reasons)


def test_watcher_requires_approval_for_shell_or_network() -> None:
    assert requires_user_approval({"name": "run_shell", "command": "pip install example"}) is True


def test_watcher_blocks_repeated_cooldown_signature() -> None:
    memory = {"cooldowns": {"sig123": 2}}
    assert should_block_repeated_action({"signature": "sig123"}, memory) is True


def test_watcher_appends_jsonl_outcome() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_watcher_") as tmp:
        path = Path(tmp) / "watcher.jsonl"
        record_action_outcome({"name": "status"}, {"ok": True}, path)
        lines = path.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["decision"]["status"] in {"allow", "review-required", "blocked"}


def run_all(verbose: bool = False) -> None:
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            if verbose:
                print(f"PASS {name}")


if __name__ == "__main__":
    run_all(True)


def test_watcher_log_redacts_sensitive_values() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_watcher_secret_") as tmp:
        path = Path(tmp) / "watcher.jsonl"
        record_action_outcome({"name": "status", "api_key": "sk-test-secret", "headers": {"Authorization": "Bearer abc"}}, {"token": "secret-token"}, path)
        text = path.read_text(encoding="utf-8")
        assert "sk-test-secret" not in text
        assert "secret-token" not in text
        assert "Bearer abc" not in text
        assert "[redacted]" in text
