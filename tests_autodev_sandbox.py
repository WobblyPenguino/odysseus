from nova_improvement_lab.autodev_sandbox import WorkItem, normalise_status, suggest_next_action, summarise_items, priority_score


def test_autodev_sandbox_summarises_status_counts():
    items = [
        WorkItem("add tests", status="todo"),
        WorkItem("fix bug", status="blocked"),
        WorkItem("review patch", status="review"),
        WorkItem("commit", status="done"),
        WorkItem("old pass alias", status="passed"),
    ]

    assert summarise_items(items) == {
        "todo": 1,
        "blocked": 1,
        "review": 1,
        "done": 2,
    }


def test_autodev_sandbox_suggests_next_action_from_state():
    assert suggest_next_action([WorkItem("bug", status="failed")]) == "fix-blockers"
    assert suggest_next_action([WorkItem("patch", status="review")]) == "review-changes"
    assert suggest_next_action([WorkItem("feature", status="todo")]) == "continue-implementation"
    assert suggest_next_action([WorkItem("complete", status="done")]) == "idle"


def test_autodev_sandbox_normalises_unknown_status_to_todo():
    assert normalise_status("weird") == "todo"


def test_autodev_sandbox_prioritises_blockers_before_completed_work():
    blocked_item = WorkItem("blocker", status="blocked")
    done_item = WorkItem("completed", status="done")
    review_item = WorkItem("reviewed", status="review")
    todo_item = WorkItem("todo_task", status="todo")

    # Blocked items should have a higher priority score than completed work
    assert priority_score(blocked_item) > priority_score(done_item)

    # Review items should outrank todo items but be lower than blocked
    assert priority_score(review_item) > priority_score(todo_item)
    assert priority_score(blocked_item) > priority_score(review_item)
