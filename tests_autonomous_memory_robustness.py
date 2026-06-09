from __future__ import annotations

import json
import tempfile
from pathlib import Path

from winlocalassistant.autonomous_failure import (
    AUTONOMOUS_FAILURE_MEMORY_SCHEMA_VERSION,
    AutonomousFailureMemory,
    AutonomousFailureRecord,
    classify_autonomous_failure,
    compact_autonomous_failure_memory,
    detect_unsafe_repair_suggestions,
    load_autonomous_failure_memory,
    make_failure_signature,
    save_autonomous_failure_memory,
    update_autonomous_failure_memory,
)


def _record(i: int = 0) -> AutonomousFailureRecord:
    sig = make_failure_signature("Improve", "tool", f"command-{i}", ".", "timeout")
    return AutonomousFailureRecord("cycle", "Improve", "tool", f"command-{i}", ".", False, "timeout", "timed out", 1.0, "now", sig, "diagnose_recent_failure")


def test_memory_save_is_schema_versioned_and_atomic_shape() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "memory.json"
        memory = update_autonomous_failure_memory(AutonomousFailureMemory(), _record())
        save_autonomous_failure_memory(path, memory)
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["schema_version"] == AUTONOMOUS_FAILURE_MEMORY_SCHEMA_VERSION
        assert data["saved_at"]
        assert path.with_name(path.name + ".tmp").exists() is False
        loaded = load_autonomous_failure_memory(path)
        assert loaded.schema_version == AUTONOMOUS_FAILURE_MEMORY_SCHEMA_VERSION


def test_corrupt_memory_is_archived_and_recovered() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "memory.json"
        path.write_text("{broken", encoding="utf-8")
        loaded = load_autonomous_failure_memory(path)
        assert loaded.recent_failures == []
        assert list(Path(tmp).glob("memory.json.corrupt_*"))


def test_compact_memory_caps_old_rows_and_cooldowns() -> None:
    memory = AutonomousFailureMemory()
    for i in range(40):
        memory = update_autonomous_failure_memory(memory, _record(i))
    compact = compact_autonomous_failure_memory(memory)
    assert len(compact.recent_failures) == 25
    assert all(key in {r.signature for r in compact.recent_failures} for key in compact.failure_counts)


def test_classifier_and_unsafe_repair_suggestions_include_extra_cases() -> None:
    assert classify_autonomous_failure("invalid input usage:") == "invalid_input"
    assert classify_autonomous_failure("Tool crashed with AttributeError") == "tool_crash"
    unsafe = detect_unsafe_repair_suggestions("full rewrite, skip tests, bypass permissions, auto-apply")
    assert "broad rewrite" in unsafe
    assert "disable tests" in unsafe
    assert "bypass permissions" in unsafe
    assert "apply source edits automatically" in unsafe


def run_all(verbose: bool = False) -> None:
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        fn()
        if verbose:
            print(f"PASS {name}")


if __name__ == "__main__":
    run_all(verbose=True)
