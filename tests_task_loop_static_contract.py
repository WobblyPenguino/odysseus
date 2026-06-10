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


def test_task_loop_includes_tiny_autodev_sort_priority_task():
    text = _runner_text()
    normalised = text.replace("/", "\\")
    assert "tiny-autodev-sandbox-sort-priority-v1" in text
    assert "sort_work_items_by_priority" in text
    assert "test_autodev_sandbox_sorts_items_by_priority_stably" in text
    assert "nova_improvement_lab\\autodev_sandbox.py" in normalised
    assert "tests_autodev_sandbox.py" in text
    assert "RequiredChangedFiles" in text
    assert "RequiredDiffContains" in text


def test_task_loop_writes_task_idea_pool_report():
    text = _runner_text()
    assert "function Write-TaskIdeaPoolReport" in text
    assert "NOVA_TASK_IDEA_POOL_LATEST.md" in text
    assert "Candidate ideas:" in text
    assert "select_next_work_item" in text
    assert "actionable_work_items" in text
    assert "explain_next_action" in text
    assert "summarise_action_plan" in text
    assert "Promotion rule:" in text
    assert "Write-TaskIdeaPoolReport -Path" in text


def test_task_loop_idea_pool_helper_defined_before_use():
    text = _runner_text()
    helper_pos = text.find("function Write-TaskIdeaPoolReport")
    call_pos = text.find("Write-TaskIdeaPoolReport -Path")
    assert helper_pos != -1
    assert call_pos != -1
    assert helper_pos < call_pos


def test_task_loop_writes_idea_pool_during_preflight():
    text = _runner_text()
    preflight_pos = text.find("if ($PreflightOnly) {")
    call_pos = text.find("Write-TaskIdeaPoolReport -Path", preflight_pos)
    pick_pos = text.find("$task = Pick-Task", preflight_pos)
    assert preflight_pos != -1
    assert call_pos != -1
    assert pick_pos != -1
    assert preflight_pos < call_pos < pick_pos


def test_task_loop_approved_recovery_tasks_include_select_next_work_item_task():
    text = _runner_text()
    approved_start = text.find("$ApprovedRecoveryTasks = @(")
    assert approved_start != -1
    approved_text = text[approved_start:approved_start + 20000]
    normalised = approved_text.replace("/", "\\")
    assert 'Id = "tiny-autodev-sandbox-select-next-work-item-v1"' in approved_text
    assert "select_next_work_item" in approved_text
    assert "test_autodev_sandbox_selects_highest_priority_item" in approved_text
    assert "sort_work_items_by_priority" in approved_text
    assert "nova_improvement_lab\\autodev_sandbox.py" in normalised
    assert "tests_autodev_sandbox.py" in approved_text
    assert "RequiredChangedFiles" in approved_text
    assert "RequiredDiffContains" in approved_text


def test_task_loop_approved_recovery_tasks_include_actionable_work_items_task():
    text = _runner_text()
    approved_start = text.find("$ApprovedRecoveryTasks = @(")
    assert approved_start != -1
    approved_text = text[approved_start:approved_start + 22000]
    normalised = approved_text.replace("/", "\\")
    assert 'Id = "tiny-autodev-sandbox-actionable-work-items-v1"' in approved_text
    assert "actionable_work_items" in approved_text
    assert "test_autodev_sandbox_filters_done_items_from_actionable_work" in approved_text
    assert "nova_improvement_lab\\autodev_sandbox.py" in normalised
    assert "tests_autodev_sandbox.py" in approved_text
    assert "RequiredChangedFiles" in approved_text
    assert "RequiredDiffContains" in approved_text


def test_task_loop_writes_idea_promotion_candidate_report():
    text = _runner_text()
    assert "function Write-IdeaPromotionCandidateReport" in text
    assert "NOVA_IDEA_PROMOTION_CANDIDATE_LATEST.md" in text
    assert "Selected idea: idea-3: explain-next-action" in text
    assert "tiny-autodev-sandbox-explain-next-action-v1" in text
    assert "explain_next_action" in text
    assert "test_autodev_sandbox_explains_next_action_with_evidence" in text
    assert "Promotion gate:" in text
    assert "The idea-promotion report alone must never trigger Aider." in text


def test_task_loop_idea_promotion_candidate_runs_after_idea_pool():
    text = _runner_text()
    idea_call = text.find("Write-TaskIdeaPoolReport -Path")
    candidate_call = text.find("Write-IdeaPromotionCandidateReport -IdeaPoolPath")
    assert idea_call != -1
    assert candidate_call != -1
    assert idea_call < candidate_call


def test_task_loop_idea_promotion_helper_defined_before_use():
    text = _runner_text()
    helper_pos = text.find("function Write-IdeaPromotionCandidateReport")
    call_pos = text.find("Write-IdeaPromotionCandidateReport -IdeaPoolPath")
    assert helper_pos != -1
    assert call_pos != -1
    assert helper_pos < call_pos


def test_task_loop_approved_recovery_tasks_include_explain_next_action_task():
    text = _runner_text()
    approved_start = text.find("$ApprovedRecoveryTasks = @(")
    assert approved_start != -1
    approved_text = text[approved_start:approved_start + 24000]
    normalised = approved_text.replace("/", "\\")
    assert 'Id = "tiny-autodev-sandbox-explain-next-action-v1"' in approved_text
    assert "explain_next_action" in approved_text
    assert "test_autodev_sandbox_explains_next_action_with_evidence" in approved_text
    assert "select_next_work_item" in approved_text
    assert "priority_score" in approved_text
    assert "nova_improvement_lab\\autodev_sandbox.py" in normalised
    assert "tests_autodev_sandbox.py" in approved_text
    assert "RequiredChangedFiles" in approved_text
    assert "RequiredDiffContains" in approved_text


def test_task_loop_writes_idea_promotion_task_draft():
    text = _runner_text()
    assert "function Write-IdeaPromotionTaskDraft" in text
    assert "NOVA_IDEA_PROMOTION_TASK_DRAFT_LATEST.md" in text
    assert "tiny-autodev-sandbox-action-plan-summary-v1" in text
    assert "summarise_action_plan" in text
    assert "test_autodev_sandbox_summarises_action_plan_with_next_item" in text
    assert "This is dry-run only." in text
    assert "The idea-promotion task draft alone must never trigger Aider." in text


def test_task_loop_idea_promotion_task_draft_runs_after_candidate_report():
    text = _runner_text()
    candidate_call = text.find("Write-IdeaPromotionCandidateReport -IdeaPoolPath")
    draft_call = text.find("Write-IdeaPromotionTaskDraft -CandidatePath")
    assert candidate_call != -1
    assert draft_call != -1
    assert candidate_call < draft_call


def test_task_loop_idea_promotion_task_draft_helper_defined_before_use():
    text = _runner_text()
    helper_pos = text.find("function Write-IdeaPromotionTaskDraft")
    call_pos = text.find("Write-IdeaPromotionTaskDraft -CandidatePath")
    assert helper_pos != -1
    assert call_pos != -1
    assert helper_pos < call_pos


def test_task_loop_registers_idea_promotion_task_draft():
    text = _runner_text()
    assert "function Register-IdeaPromotionTaskDraft" in text
    assert "Idea promotion task registered at runtime" in text
    assert "tiny-autodev-sandbox-action-plan-summary-v1" in text
    assert "summarise_action_plan" in text
    assert "test_autodev_sandbox_summarises_action_plan_with_next_item" in text
    assert "RequiredChangedFiles" in text
    assert "RequiredDiffContains" in text
    assert "$script:ApprovedRecoveryTasks" in text


def test_task_loop_registers_draft_after_draft_report_is_written():
    text = _runner_text()
    draft_call = text.find("Write-IdeaPromotionTaskDraft -CandidatePath")
    register_call = text.find("Register-IdeaPromotionTaskDraft -DraftPath")
    assert draft_call != -1
    assert register_call != -1
    assert draft_call < register_call


def test_task_loop_register_draft_helper_defined_before_use():
    text = _runner_text()
    helper_pos = text.find("function Register-IdeaPromotionTaskDraft")
    call_pos = text.find("Register-IdeaPromotionTaskDraft -DraftPath")
    assert helper_pos != -1
    assert call_pos != -1
    assert helper_pos < call_pos


def test_task_loop_runtime_registration_updates_parent_task_scope():
    text = _runner_text()
    assert "Set-Variable -Name ApprovedRecoveryTasks -Value $currentTasks -Scope 1" in text
    assert "$script:ApprovedRecoveryTasks = $currentTasks" in text
    assert "Idea promotion task runtime registration count" in text
    assert "$currentTasks = @($ApprovedRecoveryTasks)" in text


def test_task_loop_picker_explicitly_merges_runtime_promoted_tasks():
    text = _runner_text()
    assert "$script:RuntimeApprovedRecoveryTasks = @()" in text
    assert "$script:RuntimeApprovedRecoveryTasks = @($script:RuntimeApprovedRecoveryTasks) + @($task)" in text
    assert "Runtime promoted task candidates visible to picker" in text
    assert "$ApprovedRecoveryTasks = @($script:RuntimeApprovedRecoveryTasks) + @($ApprovedRecoveryTasks)" in text


def test_task_loop_picker_merges_runtime_promoted_tasks_into_active_tasks():
    text = _runner_text()
    assert "$Tasks = @($script:RuntimeApprovedRecoveryTasks) + @($Tasks)" in text
    assert "Runtime promoted task candidates merged into active task list" in text
    assert "$ApprovedRecoveryTasks = @($script:RuntimeApprovedRecoveryTasks) + @($ApprovedRecoveryTasks)" in text


def test_task_loop_registers_idea_promotion_task_from_json_draft():
    text = _runner_text()
    assert "NOVA_IDEA_PROMOTION_TASK_DRAFT_LATEST.json" in text
    assert "ConvertTo-Json -Depth 6" in text
    assert "ConvertFrom-Json" in text
    assert "Idea promotion task registered from JSON draft" in text
    assert "$taskId = [string]$draft.Id" in text
    assert "Editable = @($draft.Editable" in text
    register_start = text.find("function Register-IdeaPromotionTaskDraft")
    preflight_start = text.find("if ($PreflightOnly) {", register_start)
    assert register_start != -1
    assert preflight_start != -1
    register_text = text[register_start:preflight_start]
    assert 'Id = "tiny-autodev-sandbox-group-work-items-by-status-v1"' not in register_text


def test_task_loop_json_draft_uses_fresh_action_plan_summary_task():
    text = _runner_text()
    assert "tiny-autodev-sandbox-action-plan-summary-v1" in text
    assert "summarise_action_plan" in text
    assert "test_autodev_sandbox_summarises_action_plan_with_next_item" in text
    assert "tiny-autodev-sandbox-group-work-items-by-status-v1" not in text[text.find("function Write-IdeaPromotionTaskDraft"):text.find("function Register-IdeaPromotionTaskDraft")]


def test_task_loop_json_draft_skips_recent_completed_candidates():
    text = _runner_text()
    assert "git --no-pager log --oneline -80" in text
    assert "$draftCandidates = @(" in text
    assert "Idea promotion task draft freshness selected" in text
    assert "Idea promotion task draft skipped recent completed candidate" in text
    assert "tiny-autodev-sandbox-format-action-plan-summary-v1" in text
    assert "format_action_plan_summary" in text
    assert "test_autodev_sandbox_formats_action_plan_summary" in text


def test_task_loop_loads_external_idea_promotion_candidate_config():
    text = _runner_text()
    assert "CandidateConfigPath" in text
    assert "NOVA_IDEA_PROMOTION_CANDIDATES.json" in text
    assert "Get-Content -Path $CandidateConfigPath -Raw | ConvertFrom-Json" in text
    assert "Idea promotion task draft loaded candidate config" in text


def test_task_loop_external_idea_promotion_candidate_config_has_fresh_task():
    config = Path("local_ai_cycles/config/NOVA_IDEA_PROMOTION_CANDIDATES.json")
    assert config.exists()
    text = config.read_text(encoding="utf-8")
    assert "tiny-autodev-sandbox-render-action-plan-markdown-v1" in text
    assert "render_action_plan_markdown" in text
    assert "test_autodev_sandbox_renders_action_plan_markdown" in text


def test_task_loop_external_candidate_loader_flattens_json_array():
    text = _runner_text()
    assert "$rawCandidates = Get-Content -Path $CandidateConfigPath -Raw | ConvertFrom-Json" in text
    assert "foreach ($candidateGroup in @($rawCandidates))" in text
    assert "foreach ($candidate in @($candidateGroup))" in text
    assert "Idea promotion task draft loaded candidate count" in text
    assert "$validatedCandidates += $validation.Task" in text
    assert "$draftCandidates = @($validatedCandidates)" in text


def test_task_loop_validates_external_idea_candidate_schema():
    text = _runner_text()
    assert "function Test-IdeaPromotionTaskCandidate" in text
    assert "function Test-SafeIdeaCandidatePath" in text
    assert "Id must be one token with no whitespace" in text
    assert "duplicate Id" in text
    assert "unsafe Editable path" in text
    assert "required changed file not listed as editable" in text
    assert "Idea promotion task draft candidate validation accepted" in text
    assert "Idea promotion task draft rejected invalid candidate" in text


def test_task_loop_external_config_contains_fresh_validated_status_line_candidate():
    config = Path("local_ai_cycles/config/NOVA_IDEA_PROMOTION_CANDIDATES.json")
    assert config.exists()
    text = config.read_text(encoding="utf-8")
    assert "tiny-autodev-sandbox-action-plan-status-line-v1" in text
    assert "render_action_plan_status_line" in text
    assert "test_autodev_sandbox_renders_action_plan_status_line" in text
