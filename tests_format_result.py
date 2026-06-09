from __future__ import annotations

from winlocalassistant.core import AssistantCore
from winlocalassistant.tools import ToolResult


def _core() -> AssistantCore:
    return object.__new__(AssistantCore)


def test_format_result_summarizes_structured_verification_without_json_dump() -> None:
    result = ToolResult(
        True,
        "Final developer check passed",
        {
            "project_path": "C:/tmp/Ponggame",
            "main_file": "index.html",
            "run_url": "/project-view/index.html",
            "verification": {
                "checks": [
                    {
                        "name": "manifest_verify",
                        "ok": True,
                        "data": {
                            "returncode": 0,
                            "output": "ok\n",
                            "verification": {"passed": True, "problem_markers": [], "advice": "Passed."},
                        },
                    },
                    {"name": "node_syntax", "file": "app.js", "ok": True, "returncode": 0, "output": ""},
                    {"name": "game_runtime_sanity", "ok": True, "problems": []},
                    {"name": "static_acceptance", "ok": True, "problems": []},
                ],
                "quality_score": {
                    "syntax": 10,
                    "requirements_coverage": 10,
                    "ui_completeness": 4,
                    "runtime_confidence": 8,
                    "export_local_saving": 10,
                    "overall_percent": 88.0,
                    "threshold_percent": 70,
                    "passed_threshold": True,
                },
            },
            "human_report": (
                "I re-checked the project after the build. Syntax/build checks and requirement coverage passed."
            ),
        },
    )

    text = _core().format_result(result)

    assert "Verification: 4/4 checks passed" in text
    assert "- PASS node_syntax: app.js" in text
    assert "- PASS game_runtime_sanity" in text
    assert "Quality score: 88% passed threshold 70%" in text
    assert "Syntax 10/10, Requirements 10/10, UI completeness 4/10, Runtime 8/10" in text
    assert "I re-checked the project after the build." in text
    assert '"returncode"' not in text
    assert '"quality_score"' not in text
    assert "Technical details:" not in text


def test_format_result_failed_structured_check_shows_problem_and_fix() -> None:
    result = ToolResult(
        False,
        "JavaScript syntax check failed",
        {
            "verification": {
                "checks": [
                    {"name": "node_syntax", "file": "app.js", "ok": False, "output": "SyntaxError: Unexpected token"},
                    {"name": "static_acceptance", "ok": True, "problems": []},
                ]
            },
            "fix": ["Repair app.js syntax before retrying."],
        },
    )

    text = _core().format_result(result)

    assert "Verification: 1/2 checks passed" in text
    assert "- FAIL node_syntax: app.js - SyntaxError: Unexpected token" in text
    assert "Suggested fix:" in text
    assert "- Repair app.js syntax before retrying." in text
    assert '"output"' not in text


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
