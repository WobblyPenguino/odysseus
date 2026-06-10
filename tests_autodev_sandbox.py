from nova_improvement_lab.autodev_sandbox import WorkItem, normalise_status, suggest_next_action, summarise_items, priority_score, sort_work_items_by_priority, select_next_work_item


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


def test_autodev_sandbox_sorts_items_by_priority_stably():
    items = [
        WorkItem("a", status="todo"),
        WorkItem("b", status="blocked"),
        WorkItem("c", status="review"),
        WorkItem("d", status="todo"),
        WorkItem("e", status="blocked"),
    ]

    sorted_items = sort_work_items_by_priority(items)
    # Expected order: blocked items first in original order (b, e), then review (c),
    # then todo items in original order (a, d)
    expected_titles = ["b", "e", "c", "a", "d"]
    assert [i.title for i in sorted_items] == expected_titles


def test_autodev_sandbox_selects_highest_priority_item():
    items = [
        WorkItem("a", status="todo"),
        WorkItem("b", status="blocked"),
        WorkItem("c", status="review"),
        WorkItem("d", status="done"),   # should be ignored
        WorkItem("e", status="blocked"),
    ]

    next_item = select_next_work_item(items)
    assert next_item is not None
    assert next_item.title == "b"

    # Ensure that if only completed work remains, we get None
    done_only = [
        WorkItem("x", status="done"),
        WorkItem("y", status="passed"),
    ]
    assert select_next_work_item(done_only) is None
