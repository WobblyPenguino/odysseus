from __future__ import annotations

import tempfile
from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.tools import ToolRegistry
import winlocalassistant.tools as tools_module


def _registry(tmp: str) -> ToolRegistry:
    return ToolRegistry(AssistantConfig(workspace=tmp, allow_mutating_tools=True))


def test_self_improve_empty_proposed_files_rejected() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_self_guard_") as tmp:
        registry = _registry(tmp)
        ok, reasons = registry._self_improve_validate_patch({}, "")
    assert not ok
    assert any("No proposed files" in reason for reason in reasons)


def test_self_improve_more_than_two_files_rejected() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_self_guard_") as tmp:
        registry = _registry(tmp)
        proposed = {
            "winlocalassistant/a.py": "a = 1\n",
            "winlocalassistant/b.py": "b = 1\n",
            "winlocalassistant/c.py": "c = 1\n",
        }
        diff = registry._self_improve_build_unified_diff({}, proposed)
        ok, reasons = registry._self_improve_validate_patch(proposed, diff)
    assert not ok
    assert any("more than 2 files" in reason for reason in reasons)


def test_self_improve_outside_target_rejected() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_self_guard_") as tmp:
        registry = _registry(tmp)
        proposed = {"README.md": "bad\n"}
        diff = registry._self_improve_build_unified_diff({}, proposed)
        ok, reasons = registry._self_improve_validate_patch(proposed, diff)
    assert not ok
    assert any("outside winlocalassistant/*.py" in reason for reason in reasons)


def test_self_improve_protected_rollback_removal_rejected() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_self_guard_") as tmp:
        registry = _registry(tmp)
        diff = "--- before/winlocalassistant/example.py\n+++ after/winlocalassistant/example.py\n@@\n- rollback()\n+ pass\n"
        ok, reasons = registry._self_improve_validate_patch({"winlocalassistant/example.py": "pass\n"}, diff)
    assert not ok
    assert any("rollback" in reason.lower() for reason in reasons)


def test_self_improve_command_name_removal_rejected() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_self_guard_") as tmp:
        registry = _registry(tmp)
        diff = "--- before/winlocalassistant/example.py\n+++ after/winlocalassistant/example.py\n@@\n- '/idle /self-improve /help /test-all'\n+ 'safe'\n"
        ok, reasons = registry._self_improve_validate_patch({"winlocalassistant/example.py": "safe\n"}, diff)
    assert not ok
    assert any("/idle" in reason for reason in reasons)
    assert any("/self-improve" in reason for reason in reasons)


def test_self_improve_empty_diff_rejected() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_self_guard_") as tmp:
        registry = _registry(tmp)
        ok, reasons = registry._self_improve_validate_patch({"winlocalassistant/example.py": "same\n"}, "")
    assert not ok
    assert any("diff is empty" in reason.lower() for reason in reasons)


def test_self_improve_safe_small_patch_accepted() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_self_guard_") as tmp:
        registry = _registry(tmp)
        original = {"winlocalassistant/example.py": "def answer():\n    return 1\n"}
        proposed = {"winlocalassistant/example.py": "def answer():\n    return 2\n"}
        diff = registry._self_improve_build_unified_diff(original, proposed)
        ok, reasons = registry._self_improve_validate_patch(proposed, diff)
    assert ok, reasons
    assert registry._self_improve_count_changed_lines(diff) == 2


def test_self_improve_report_writer_creates_required_headings() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_self_guard_report_") as tmp:
        profile = Path(tmp) / "profile"
        old_app_dir = tools_module.APP_DIR
        try:
            tools_module.APP_DIR = profile
            registry = _registry(tmp)
            report = registry._self_improve_write_report(
                goal="test guardrail report",
                proposed_files={"winlocalassistant/example.py": "x = 1\n"},
                diff_text="--- before/winlocalassistant/example.py\n+++ after/winlocalassistant/example.py\n@@\n+x = 1\n",
                validation_reasons=["example rejection"],
                backup_path=str(profile / "backup.zip"),
                rollback_status="not-needed-no-files-written",
                final_status="rejected-before-write",
            )
        finally:
            tools_module.APP_DIR = old_app_dir

        text = Path(report).read_text(encoding="utf-8")
    for heading in [
        "# Self Improve Attempt",
        "## Goal",
        "## Proposed Files",
        "## Diff Summary",
        "## Guardrail Decision",
        "## Verification Commands",
        "## Verification Output",
        "## Backup Path",
        "## Rollback Status",
        "## Final Status",
    ]:
        assert heading in text
    assert "rejected-before-write" in text


def run_all(verbose: bool = False) -> None:
    tests = [
        (name, fn)
        for name, fn in sorted(globals().items())
        if name.startswith("test_") and callable(fn)
    ]
    for name, fn in tests:
        fn()
        if verbose:
            print(f"PASS {name}")


if __name__ == "__main__":
    run_all(verbose=True)
