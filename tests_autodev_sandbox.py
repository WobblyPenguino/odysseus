from nova_improvement_lab.autodev_sandbox import WorkItem, normalise_status, suggest_next_action, summarise_items


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
