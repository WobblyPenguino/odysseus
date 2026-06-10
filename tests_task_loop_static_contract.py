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
