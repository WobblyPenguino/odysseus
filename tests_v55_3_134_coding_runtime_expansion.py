from __future__ import annotations

from winlocalassistant.nova_coding_capabilities import plan_coding_execution, verifier_for_file
from winlocalassistant.project_acceptance import build_project_acceptance_contract
from winlocalassistant.project_brief import infer_project_build_brief
from winlocalassistant.project_type_registry import project_type_contract


def test_coding_plan_supports_typescript_batch_markdown_and_json_config() -> None:
    ts_plan = plan_coding_execution("write a TypeScript CLI to format names")
    assert ts_plan["artifact_type"] == "typescript_cli_tool"
    assert ts_plan["main_file"] == "src/index.ts"
    assert "tsconfig.json" in ts_plan["expected_files"]
    assert "npm install" in ts_plan["optional_verify_commands"]

    batch_plan = plan_coding_execution("make a Windows batch file that prints usage")
    assert batch_plan["artifact_type"] == "batch_script"
    assert batch_plan["main_file"] == "script.bat"
    assert "@echo off" in " ".join(batch_plan["prompt_rules"]).lower()

    md_plan = plan_coding_execution("write Markdown documentation for the backup workflow")
    assert md_plan["artifact_type"] == "markdown_document"
    assert md_plan["expected_files"] == ["README.md"]

    json_plan = plan_coding_execution("create a JSON config file for model routing")
    assert json_plan["artifact_type"] == "json_config"
    assert json_plan["main_file"] == "config.json"
    assert "json.loads" in json_plan["verify_command"]


def test_project_registry_and_acceptance_cover_new_artifact_types() -> None:
    assert project_type_contract("TypeScript CLI")["kind"] == "typescript_cli_tool"
    assert project_type_contract("Windows batch script")["kind"] == "batch_script"
    assert project_type_contract("Markdown documentation")["kind"] == "markdown_document"
    assert project_type_contract("JSON config")["kind"] == "json_config"

    assert build_project_acceptance_contract("TypeScript CLI").artifact_type == "typescript_cli_tool"
    assert build_project_acceptance_contract("batch file").artifact_type == "batch_script"
    assert build_project_acceptance_contract("Markdown documentation").artifact_type == "markdown_document"
    assert build_project_acceptance_contract("JSON config").artifact_type == "json_config"


def test_project_brief_uses_runtime_specific_files_and_checks() -> None:
    ts_brief = infer_project_build_brief("write a TypeScript CLI to format names")
    assert ts_brief.artifact_type == "typescript_cli_tool"
    assert "src/index.ts" in ts_brief.suggested_files
    assert any("typescript" in cmd.lower() or "tsconfig" in cmd.lower() for cmd in ts_brief.verification_commands)

    batch_brief = infer_project_build_brief("make a Windows batch file that prints usage")
    assert batch_brief.artifact_type == "batch_script"
    assert "script.bat" in batch_brief.suggested_files
    assert any("batch" in item.lower() or "@echo off" in item.lower() for item in batch_brief.functional_requirements)

    json_brief = infer_project_build_brief("create a JSON config file for model routing")
    assert json_brief.artifact_type == "json_config"
    assert "config.json" in json_brief.suggested_files
    assert any("secret" in item.lower() or "placeholder" in item.lower() for item in json_brief.assumptions + json_brief.functional_requirements)


def test_verifier_for_file_handles_new_file_types() -> None:
    assert "tsconfig.json" in verifier_for_file("src/index.ts")
    assert "@echo off" in verifier_for_file("script.bat")
    assert "json.loads" in verifier_for_file("config.json")
    assert "markdown ok" in verifier_for_file("README.md")


def run_all(verbose: bool = False) -> None:
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            if verbose:
                print(f"PASS {name}")


if __name__ == "__main__":
    run_all(True)
