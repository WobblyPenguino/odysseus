from __future__ import annotations

from winlocalassistant.nova_coding_capabilities import build_local_model_performance_plan


def _kind(goal: str) -> str:
    return str(build_local_model_performance_plan(goal)["profile"]["task_kind"])


def test_local_model_classifier_recognizes_expanded_coding_runtimes() -> None:
    examples = [
        "write a TypeScript CLI to format names",
        "build a Node command line tool for CSV cleanup",
        "make a Windows batch file that prints usage",
        "create a JSON config schema for model routing",
        "write a PowerShell automation script",
    ]
    for goal in examples:
        assert _kind(goal) == "coding", goal


def test_local_model_classifier_prioritizes_vision_and_document_context() -> None:
    assert _kind("summarize this screenshot and identify the controls") == "vision"
    assert _kind("write Markdown documentation for the backup workflow") == "long_context"


def run_all(verbose: bool = False) -> None:
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            if verbose:
                print(f"PASS {name}")


if __name__ == "__main__":
    run_all(True)
