from __future__ import annotations

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.nova_eval_packs import build_nova_eval_plan, run_nova_eval_pack, select_eval_cases


def test_nova_eval_pack_plan_lists_safe_upgrade_checks() -> None:
    payload = build_nova_eval_plan("core")
    assert payload["ok"] is True
    assert payload["pack"] == "core"
    commands = [case["command"] for case in payload["cases"]]
    assert "/version" in commands
    assert "/help" in commands
    assert payload["validation_hint"] == "/nova-eval-packs run all"


def test_nova_eval_pack_unknown_pack_is_reported_without_exception() -> None:
    pack, cases, available = select_eval_cases("missing-pack")
    assert pack == "missing-pack"
    assert cases == []
    assert "core" in available


def test_nova_eval_runner_detects_missing_markers() -> None:
    report = run_nova_eval_pack(lambda command: "not the expected output", "core")
    assert report["ok"] is False
    assert report["failed"] == report["total_cases"]
    assert all(item["missing_markers"] for item in report["results"])


def test_core_routes_nova_eval_pack_commands() -> None:
    core = AssistantCore(AssistantConfig())
    plan = core.handle_command("/nova-eval-packs plan core")
    assert "# Nova Eval Packs" in plan
    assert "Planned checks" in plan
    run = core.handle_command("/nova-eval-packs run core")
    assert "Result: **PASS**" in run
    assert "Passed: 3/3" in run
