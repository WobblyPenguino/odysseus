from __future__ import annotations

from winlocalassistant.core import AssistantCore
from winlocalassistant.nova_coding_capabilities import (
    build_coding_capability_audit,
    build_local_model_performance_plan,
    plan_coding_execution,
)
from winlocalassistant.project_acceptance import build_project_acceptance_contract
from winlocalassistant.project_brief import infer_project_build_brief
from winlocalassistant.project_type_registry import project_type_contract


def test_coding_plan_selects_runtime_specific_files() -> None:
    java_plan = plan_coding_execution("write a Java calculator CLI")
    assert java_plan["artifact_type"] == "java_cli_or_desktop_app"
    assert java_plan["main_file"] == "Main.java"
    assert "javac" in java_plan["verify_command"]

    python_plan = plan_coding_execution("make a Python script to organise CSV files")
    assert python_plan["artifact_type"] == "python_cli_script"
    assert "main.py" in python_plan["expected_files"]
    assert "py_compile" in python_plan["verify_command"]

    browser_plan = plan_coding_execution("make a browser game with score and controls")
    assert browser_plan["artifact_type"] == "html_css_js_game"
    assert browser_plan["main_file"] == "index.html"


def test_project_brief_and_acceptance_do_not_force_html_for_code_prompts() -> None:
    brief = infer_project_build_brief("write a Java calculator CLI")
    assert brief.artifact_type == "java_cli_or_desktop_app"
    assert brief.suggested_files == ["Main.java", "README.md"]
    assert any("javac" in cmd for cmd in brief.verification_commands)

    contract = build_project_acceptance_contract("python todo script")
    assert contract.artifact_type == "python_cli_script"
    assert "main.py" in contract.expected_files


def test_project_type_registry_includes_non_browser_types() -> None:
    assert project_type_contract("java app")["kind"] == "java_cli_app"
    assert project_type_contract("powershell script")["kind"] == "powershell_script"
    assert project_type_contract("node command line tool")["kind"] == "node_cli_tool"


def test_local_model_performance_plan_is_task_specific() -> None:
    payload = build_local_model_performance_plan("fix code in a project", hardware_hint="GTX 1650 4GB VRAM")
    assert payload["profile"]["task_kind"] == "coding"
    assert payload["profile"]["suggested_ollama_options"]["num_ctx"] <= 4096
    assert any("deterministic verify" in item for item in payload["strategies"])


def test_registry_and_core_routes_new_coding_commands() -> None:
    core = AssistantCore.load()
    checks = {
        "coding_plan": (dict(goal="write a Java calculator CLI"), "Nova Coding Execution Plan"),
        "coding_capability_audit": (dict(goal="write Python script"), "Nova Coding Capability Audit"),
        "local_model_performance_plan": (dict(goal="fix code", hardware="GTX 1650 4GB VRAM"), "Nova Local Model Performance Plan"),
    }
    for command, (kwargs, marker) in checks.items():
        result = core.tools.call(command, **kwargs)
        assert result.ok, f"{command} failed: {result.summary}"
        assert marker in str((result.data or {}).get("message", ""))

    assert "Main.java" in core.chat("/coding-plan write a Java calculator CLI")
    assert "Nova Coding Capability Audit" in core.chat("/coding-audit write Python script")
    assert "Nova Local Model Performance Plan" in core.chat("/local-model-performance fix code => GTX 1650 4GB VRAM")


def test_coding_capability_audit_detects_new_support() -> None:
    payload = build_coding_capability_audit(".")
    names = {check["name"]: check["ok"] for check in payload["checks"]}
    assert names["coding_plan_module"] is True
    assert names["dynamic_project_brief"] is True
    assert names["project_types_multi_language"] is True


def run_all(verbose: bool = False) -> None:
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            if verbose:
                print(f"PASS {name}")


if __name__ == "__main__":
    run_all(True)
