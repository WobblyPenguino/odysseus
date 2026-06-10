from nova_improvement_lab.autodev_sandbox import WorkItem, normalise_status, suggest_next_action, summarise_items, priority_score, sort_work_items_by_priority, select_next_work_item, actionable_work_items, explain_next_action, group_work_items_by_status, summarise_action_plan, format_action_plan_summary, render_action_plan_markdown, render_action_plan_status_line, build_action_plan_debug_dict


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


def test_autodev_sandbox_filters_done_items_from_actionable_work():
    items = [
        WorkItem("a", status="todo"),
        WorkItem("b", status="passed"),   # alias for done
        WorkItem("c", status="done"),
        WorkItem("d", status="blocked"),
    ]

    actionable = actionable_work_items(items)
    assert [i.title for i in actionable] == ["a", "d"]


def test_autodev_sandbox_explains_next_action_with_evidence():
    items = [
        WorkItem("blocker_task", status="blocked"),
        WorkItem("todo_task", status="todo"),
    ]

    explanation = explain_next_action(items)
    # The explanation should contain evidence about the selected item
    assert "blocker_task" in explanation
    assert "blocked" in explanation
    assert str(priority_score(WorkItem("blocker_task", status="blocked"))) in explanation

    # When no actionable items remain, it should return 'idle'
    idle_explanation = explain_next_action([WorkItem("done_item", status="done")])
    assert idle_explanation == "idle"


def test_autodev_sandbox_groups_items_by_status():
    items = [
        WorkItem("todo1", status="todo"),
        WorkItem("blocked1", status="blocked"),
        WorkItem("review1", status="review"),
        WorkItem("done1", status="done"),
        WorkItem("pass_alias", status="passed"),  # alias for done
        WorkItem("open1", status="open"),       # normalises to todo
    ]

    grouped = group_work_items_by_status(items)

    # Expected keys and order of items within each key
    assert set(grouped.keys()) == {"todo", "blocked", "review", "done"}
    assert [i.title for i in grouped["todo"]] == ["todo1", "open1"]
    assert [i.title for i in grouped["blocked"]] == ["blocked1"]
    assert [i.title for i in grouped["review"]] == ["review1"]
    assert [i.title for i in grouped["done"]] == ["done1", "pass_alias"]


def test_autodev_sandbox_summarises_action_plan_with_next_item():
    items = [
        WorkItem("a", status="todo"),
        WorkItem("b", status="blocked"),
        WorkItem("c", status="review"),
        WorkItem("d", status="done"),
    ]

    summary = summarise_action_plan(items)
    assert summary["total"] == 4
    # actionable items: a, b, c => 3
    assert summary["actionable"] == 3
    # next selected item should be "b" (blocked highest priority)
    assert summary["next_title"] == "b"
    assert summary["next_status"] == "blocked"
    assert summary["next_score"] == priority_score(WorkItem("b", status="blocked"))


def test_autodev_sandbox_formats_action_plan_summary():
    items = [
        WorkItem("a", status="todo"),
        WorkItem("b", status="blocked"),
        WorkItem("c", status="review"),
        WorkItem("d", status="done"),
    ]

    summary = summarise_action_plan(items)
    formatted = format_action_plan_summary(summary)

    # The formatted string should contain the key values from the summary
    assert f"Total: {summary['total']}" in formatted
    assert f"Actionable: {summary['actionable']}" in formatted
    if summary["next_title"] is not None:
        assert summary["next_title"] in formatted
        assert summary["next_status"] in formatted
        assert str(summary["next_score"]) in formatted
    else:
        assert "idle" in formatted


def test_autodev_sandbox_renders_action_plan_markdown():
    items = [
        WorkItem("a", status="todo"),
        WorkItem("b", status="blocked"),
        WorkItem("c", status="review"),
        WorkItem("d", status="done"),
    ]

    markdown = render_action_plan_markdown(items)
    # The Markdown should start with the heading
    assert markdown.startswith("## Action Plan")
    # It should contain bullet lines for total, actionable, next title, next status and next score
    assert "- Total: 4" in markdown
    assert "- Actionable: 3" in markdown
    assert "- Next title: b" in markdown
    assert "- Next status: blocked" in markdown
    assert f"- Next score: {priority_score(WorkItem('b', status='blocked'))}" in markdown

    # When there are no actionable items, the next lines should indicate idle
    idle_markdown = render_action_plan_markdown([WorkItem("done_item", status="done")])
    assert "- Next title: idle" in idle_markdown
    assert "- Next status:" in idle_markdown
    assert "- Next score:" in idle_markdown


def test_autodev_sandbox_renders_action_plan_status_line():
    items = [
        WorkItem("a", status="todo"),
        WorkItem("b", status="blocked"),
        WorkItem("c", status="review"),
        WorkItem("d", status="done"),
    ]

    line = render_action_plan_status_line(items)
    # The line should contain the total, actionable count and next item details
    assert "Total: 4" in line
    assert "Actionable: 3" in line
    assert "- Next title:" not in line  # single line format
    assert "Next item: b (status=blocked, score=" in line

    # When there are no actionable items, the next part should be idle
    idle_line = render_action_plan_status_line([WorkItem("done_item", status="done")])
    assert "Total: 1" in idle_line
    assert "Actionable: 0" in idle_line
    assert "Next item: idle" in idle_line


def test_autodev_sandbox_builds_action_plan_debug_dict():
    items = [
        WorkItem("a", status="todo"),
        WorkItem("b", status="blocked"),
        WorkItem("c", status="review"),
        WorkItem("d", status="done"),
    ]

    debug_dict = build_action_plan_debug_dict(items)
    summary = summarise_action_plan(items)

    # Basic fields match the summary
    assert debug_dict["total"] == summary["total"]
    assert debug_dict["actionable"] == summary["actionable"]
    assert debug_dict["next_title"] == summary["next_title"]
    assert debug_dict["next_status"] == summary["next_status"]
    assert debug_dict["next_score"] == summary["next_score"]

    # has_next reflects presence of a next item
    expected_has_next = summary["next_title"] is not None
    assert debug_dict["has_next"] == expected_has_next

    # status_line should match the rendered single‑line status
    assert debug_dict["status_line"] == render_action_plan_status_line(items)

    # Test when no actionable items remain
    idle_items = [WorkItem("done_item", status="done")]
    idle_debug = build_action_plan_debug_dict(idle_items)
    assert idle_debug["next_title"] is None
    assert idle_debug["has_next"] is False
    assert "idle" in idle_debug["status_line"]
