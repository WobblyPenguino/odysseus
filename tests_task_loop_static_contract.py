from pathlib import Path

RUNNER = Path(__file__).resolve().parent / "run_nova_task_queue_loop.ps1"


def _runner_text() -> str:
    return RUNNER.read_text(encoding="utf-8")


def test_task_loop_has_large_file_snippet_context_and_cleanup():
    text = _runner_text()
    assert "$MaxAiderEditableFileBytes = 120000" in text
    assert "function Write-TaskLargeFileSnippetContext" in text
    assert "task_large_file_snippets_*.md" in text
    assert "Large editable file(s) skipped and excerpted for context" in text


def test_task_loop_denies_aider_file_prompts_with_valid_no_answers():
    text = _runner_text()
    assert '$denyInput = ((1..900 | ForEach-Object { "no" }) -join "`n") + "`n"' in text
    assert '$denyInput = "D`n"' not in text
    assert "don't`n" not in text


def test_task_loop_has_productivity_floor_for_live_and_preflight():
    text = _runner_text()
    assert "$MinProductiveTaskScore = 35" in text
    assert "function Resolve-TaskScore" in text
    assert "function Write-TaskPoolExhaustedReport" in text
    assert "No sufficiently productive task remained" in text

    live_idx = text.index("$snippetContext = Write-TaskLargeFileSnippetContext")
    assert text.rfind("Resolve-TaskScore -Task $task", 0, live_idx) != -1

    preflight_block_idx = text.index("if ($PreflightOnly)")
    assert text.index("$MinProductiveTaskScore = 35") < preflight_block_idx
    assert text.index("function Resolve-TaskScore") < preflight_block_idx
    assert text.index("function Write-TaskPoolExhaustedReport") < preflight_block_idx

    preflight_idx = text.index("Preflight selected task:")
    assert text.rfind('-Phase "preflight"', 0, preflight_idx) != -1
    assert "No Aider invocation, commit, or source edit was attempted because the task pool is exhausted." in text
    assert "exit 0" in text[text.rfind('-Phase "preflight"', 0, preflight_idx):preflight_idx]


def test_task_loop_runs_static_contract_before_live_cycles():
    text = _runner_text()
    assert "tests_task_loop_static_contract.py" in text


def test_task_loop_includes_improvement_lab_task():
    text = _runner_text()
    assert "lab-small-source-test-improvement" in text
    assert "nova_improvement_lab\\text_tools.py" in text
    assert "tests_improvement_lab_contract.py" in text


def test_validation_helper_checks_external_command_exit_codes():
    helper = Path(__file__).resolve().parent / "tools" / "validate_task_loop_patch.ps1"
    text = helper.read_text(encoding="utf-8")
    assert "$LASTEXITCODE" in text
    assert "throw" in text
    assert "tests_improvement_lab_contract.py" in text
    assert "Validation passed." in text


def test_diff_classifier_accepts_control_flow_and_assertions():
    text = _runner_text()
    assert "function Test-DiffLineLooksExecutable" in text
    assert "^(if|elif|else|for|while|try|except|finally|with|match|case)" in text
    assert "return|raise|yield|assert|break|continue|pass" in text
    assert "Test-DiffLineLooksExecutable -Line" in text


def test_task_loop_includes_strict_lab_source_test_task():
    text = _runner_text()
    assert "lab-source-test-improvement-v2" in text
    assert "You must modify BOTH" in text
    assert "Do not make a test-only patch" in text
    assert "nova_improvement_lab\\text_tools.py" in text or "nova_improvement_lab\text_tools.py" in text
    assert "tests_improvement_lab_contract.py" in text


def test_task_loop_enforces_required_changed_files():
    text = _runner_text()
    assert "RequiredChangedFiles" in text
    assert "function Assert-TaskRequiredChangedFiles" in text
    assert "Rejected required-file contract breach" in text
    assert "Assert-TaskRequiredChangedFiles -Task $task" in text


def test_task_loop_enforces_required_diff_markers():
    text = _runner_text()
    assert "lab-risk-contract-source-test-v3" in text
    assert "RequiredDiffContains" in text
    assert "function Assert-TaskRequiredDiffContains" in text
    assert "Rejected required-diff contract breach" in text
    assert "Assert-TaskRequiredDiffContains -Task $task -DiffText $bad" in text


def test_required_diff_contract_can_override_generic_executable_classifier():
    text = _runner_text()
    assert "$hasRequiredDiffContract" in text
    assert "$hasExecutableChange" in text
    assert "Executable classifier fallback: accepted required diff contract" in text
    assert "Rejected documentation/comment-only patch with no executable code change." in text


def test_task_loop_includes_real_model_context_named_file_task():
    text = _runner_text()
    assert "real-model-context-named-file-preview-v1" in text
    assert "winlocalassistant\\model_context.py" in text or "winlocalassistant\model_context.py" in text
    assert "tests_model_context_pack.py" in text
    assert "_prompt_named_files" in text
    assert "test_model_context_pack_includes_prompt_named_python_file_preview" in text
    assert "RequiredChangedFiles" in text
    assert "RequiredDiffContains" in text
