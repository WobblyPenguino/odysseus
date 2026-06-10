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
    assert "nova_improvement_lab\\text_tools.py" in text
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
    assert "winlocalassistant\\model_context.py" in text
    assert "tests_model_context_pack.py" in text
    assert "_prompt_named_files" in text
    assert "test_model_context_pack_includes_prompt_named_python_file_preview" in text
    assert "RequiredChangedFiles" in text
    assert "RequiredDiffContains" in text


def test_task_loop_rejects_invalid_loopback_url_typo():
    text = _runner_text()
    assert "Rejected invalid loopback URL typo 127.0.0-1" in text
    assert "127.0.0.1" in text


def test_task_loop_includes_real_model_context_named_file_cache_task():
    text = _runner_text()
    assert "real-model-context-named-file-cache-freshness-v1" in text
    assert "winlocalassistant\\model_context.py" in text
    assert "tests_model_context_pack.py" in text
    assert "_prompt_named_file_signature" in text
    assert "test_model_context_pack_refreshes_prompt_named_file_preview_after_file_change" in text
    assert "RequiredChangedFiles" in text
    assert "RequiredDiffContains" in text


def test_task_loop_includes_research_only_repo_inspiration_task():
    text = _runner_text()
    assert "research-only-agent-repo-inspiration-v1" in text
    assert "Research-only planning task" in text
    assert "Do not clone repos or copy external code" in text
    assert "docs\\research\\NOVA_AGENT_REPO_INSPIRATION_LATEST.md" in text
    assert "No source code copied" in text
    assert "RequiredChangedFiles" in text
    assert "RequiredFinalFileContains" in text


def test_task_loop_rejects_double_dot_loopback_url_typo():
    text = _runner_text()
    assert "Rejected invalid loopback URL typo 127.0.0..11434" in text
    assert "127.0.0.1:11434" in text


def test_research_only_planning_language_is_narrowly_allowed():
    text = _runner_text()
    assert "function Test-ResearchOnlyPlanningDiff" in text
    assert 'StartsWith("research-only-")' in text
    assert 'StartsWith("docs\\research\\")' in text or 'StartsWith("docs\research\")' in text
    assert "Research-only planning fallback: allowed planning language" in text
    assert "Rejected placeholder/speculative patch language." in text


def test_task_loop_enforces_required_final_file_contains():
    text = _runner_text()
    assert "function Assert-TaskRequiredFinalFileContains" in text
    assert "Rejected required-final-file contract breach" in text
    assert "Assert-TaskRequiredFinalFileContains -Task $task" in text
    assert "$hasResearchOnlyPlanningDiff" in text
    assert "Research-only executable fallback: accepted docs/research planning diff" in text



def test_task_loop_writes_task_localization_report():
    text = _runner_text()
    assert "function Write-TaskLocalizationReport" in text
    assert "NOVA_TASK_LOCALIZATION_LATEST.md" in text
    assert "Task ID:" in text
    assert "Editable files:" in text
    assert "Targeted tests:" in text
    assert "Required changed files:" in text
    assert "Required diff markers:" in text
    assert "Required final-file markers:" in text
    assert "Files that must not be edited:" in text
    assert "Write-TaskLocalizationReport -Task $task" in text


def test_task_loop_writes_localization_report_during_preflight():
    text = _runner_text()
    preflight_start = text.find("if ($PreflightOnly)")
    assert preflight_start != -1
    preflight_end = text.find("Clean-GeneratedNoise", preflight_start)
    assert preflight_end != -1
    preflight_section = text[preflight_start:preflight_end]
    assert "Write-TaskLocalizationReport -Task $task" in preflight_section
    assert "NOVA_TASK_LOCALIZATION_LATEST.md" in preflight_section


def test_task_loop_defines_localization_helper_before_preflight():
    text = _runner_text()
    helper_pos = text.find("function Write-TaskLocalizationReport")
    preflight_pos = text.find("if ($PreflightOnly)")
    assert helper_pos != -1
    assert preflight_pos != -1
    assert helper_pos < preflight_pos


def test_task_loop_includes_model_context_prompt_file_path_safety_task():
    text = _runner_text()
    normalised = text.replace("/", "\\")
    assert "real-model-context-prompt-file-path-safety-v1" in text
    assert "_resolve_prompt_named_file" in text
    assert "test_model_context_pack_rejects_prompt_named_file_outside_workspace" in text
    assert "winlocalassistant\\model_context.py" in normalised
    assert "RequiredChangedFiles" in text
    assert "RequiredDiffContains" in text


def test_task_loop_writes_static_tool_status_report():
    text = _runner_text()
    assert "function Write-StaticToolStatusReport" in text
    assert "NOVA_STATIC_TOOL_STATUS_LATEST.md" in text
    assert "ruff" in text
    assert "mypy" in text
    assert "semgrep" in text
    assert "bandit" in text
    assert "pip-audit" in text
    assert "detect-secrets" in text
    assert "Write-StaticToolStatusReport -Path" in text


def test_task_loop_defines_static_tool_status_helper_before_use():
    text = _runner_text()
    helper_pos = text.find("function Write-StaticToolStatusReport")
    call_pos = text.find("Write-StaticToolStatusReport -Path")
    assert helper_pos != -1
    assert call_pos != -1
    assert helper_pos < call_pos


def test_task_loop_writes_patch_review_report():
    text = _runner_text()
    assert "function Write-PatchReviewReport" in text
    assert "NOVA_PATCH_REVIEW_LATEST.md" in text
    assert "Reviewer verdict:" in text
    assert "Risk level:" in text
    assert "Changed files:" in text
    assert "Unexpected changed files:" in text
    assert "Security and correctness review checklist:" in text
    assert "Write-PatchReviewReport -Task $task" in text


def test_task_loop_patch_review_helper_defined_before_use():
    text = _runner_text()
    helper_pos = text.find("function Write-PatchReviewReport")
    call_pos = text.find("Write-PatchReviewReport -Task $task")
    assert helper_pos != -1
    assert call_pos != -1
    assert helper_pos < call_pos


def test_task_loop_includes_tiny_autodev_sandbox_task():
    text = _runner_text()
    normalised = text.replace("/", "\\")
    assert "tiny-autodev-sandbox-priority-v1" in text
    assert "priority_score" in text
    assert "test_autodev_sandbox_prioritises_blockers_before_polish" in text
    assert "nova_improvement_lab\\autodev_sandbox.py" in normalised
    assert "tests_autodev_sandbox.py" in text
    assert "RequiredChangedFiles" in text
    assert "RequiredDiffContains" in text


def test_task_loop_includes_tiny_autodev_sandbox_priority_v2_task():
    text = _runner_text()
    normalised = text.replace("/", "\\")
    assert "tiny-autodev-sandbox-priority-v2" in text
    assert "priority_score" in text
    assert "test_autodev_sandbox_prioritises_blockers_before_completed_work" in text
    assert "nova_improvement_lab\\autodev_sandbox.py" in normalised
    assert "tests_autodev_sandbox.py" in text
    assert "RequiredChangedFiles" in text
    assert "RequiredDiffContains" in text


def test_task_loop_has_placeholder_false_positive_contract_override():
    text = _runner_text()
    assert "Placeholder/speculative rejection override" in text
    assert "$canOverridePlaceholderFalsePositive" in text
    assert "$missingRequiredFiles.Count -eq 0" in text
    assert "$missingDiffMarkers.Count -eq 0" in text
    assert "$sourceChanges.Count -gt 0" in text
    assert "$testChanges.Count -gt 0" in text
    assert "validation-gate-after-placeholder-override" in text
    assert "Placeholder/speculative rejection override validation gates passed." in text




def test_task_loop_placeholder_override_has_uncorrupted_nested_test_patterns():
    text = _runner_text()
    assert "$sourceChanges = @(" in text
    assert "$testChanges = @(" in text
    assert '$pathForKind = ([string]$_).Replace("\\", "/")' in text
    assert '($pathForKind -notlike "tests_*.py")' in text
    assert '($pathForKind -notlike "*/tests/*")' in text
    assert '($pathForKind -like "tests_*.py")' in text
    assert '($pathForKind -like "*/tests/*")' in text
    assert "Placeholder/speculative rejection override" in text
    assert "*     ests" not in text
    assert "*        ests" not in text
    assert '-notmatch "\\tests\\"' not in text
    assert '-match "\\tests\\"' not in text

def test_task_loop_writes_subagent_review_report():
    text = _runner_text()
    assert "function Write-SubagentReviewReport" in text
    assert "NOVA_SUBAGENT_REVIEW_LATEST.md" in text
    assert "Planner verdict:" in text
    assert "Localizer verdict:" in text
    assert "Editor verdict:" in text
    assert "Reviewer verdict:" in text
    assert "Tester verdict:" in text
    assert "Risk verdict:" in text
    assert "Memory verdict:" in text
    assert "Overall recommendation:" in text
    assert "Write-SubagentReviewReport -Task $task" in text


def test_task_loop_subagent_review_helper_defined_before_use():
    text = _runner_text()
    helper_pos = text.find("function Write-SubagentReviewReport")
    call_pos = text.find("Write-SubagentReviewReport -Task $task")
    assert helper_pos != -1
    assert call_pos != -1
    assert helper_pos < call_pos
