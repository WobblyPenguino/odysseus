from __future__ import annotations

from winlocalassistant.task_decomposition import decompose_user_request, normalize_request_text


def test_normalize_request_text_fixes_common_typos() -> None:
    text = normalize_request_text("mkae a calcualtor gaem")
    assert "make" in text.lower()
    assert "calculator" in text.lower()
    assert "game" in text.lower()


def test_decompose_multi_task_request_orders_subtasks_and_flags_verification() -> None:
    plan = decompose_user_request("fix the calculator, make it look better, add tests")
    assert plan.task_count >= 3
    assert plan.plan_level >= 4
    assert plan.needs_clarification is True
    assert any(s.needs_verification for s in plan.subtasks)
    assert "multiple tasks without explicit order" in plan.ambiguity


def test_decompose_specific_creation_has_high_confidence() -> None:
    plan = decompose_user_request("make a calculator with clear backspace and result display")
    assert plan.intent_confidence >= 0.85
    assert plan.plan_level == 2
    assert any("calculator" in item for item in plan.success_criteria)


def test_decompose_autonomous_high_risk_sets_level_five() -> None:
    plan = decompose_user_request("improve Nova autonomous self improvement with auto apply")
    assert plan.plan_level == 5
    assert any(s.risk_level == "high" for s in plan.subtasks)


def run_all(verbose: bool = False) -> None:
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        fn()
        if verbose:
            print(f"PASS {name}")


if __name__ == "__main__":
    run_all(verbose=True)
