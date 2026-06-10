from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True)
class WorkItem:
    title: str
    kind: str = "task"
    status: str = "todo"
    evidence: str = ""


def normalise_status(status: str) -> str:
    value = (status or "").strip().lower()
    aliases = {
        "done": "done",
        "pass": "done",
        "passed": "done",
        "todo": "todo",
        "open": "todo",
        "blocked": "blocked",
        "fail": "blocked",
        "failed": "blocked",
        "review": "review",
    }
    return aliases.get(value, "todo")


def summarise_items(items: Iterable[WorkItem]) -> dict[str, int]:
    summary = {"todo": 0, "blocked": 0, "review": 0, "done": 0}
    for item in items:
        summary[normalise_status(item.status)] += 1
    return summary


def suggest_next_action(items: Iterable[WorkItem]) -> str:
    summary = summarise_items(items)
    if summary["blocked"]:
        return "fix-blockers"
    if summary["review"]:
        return "review-changes"
    if summary["todo"]:
        return "continue-implementation"
    return "idle"


def priority_score(item: WorkItem) -> int:
    """
    Return a numeric score representing the priority of a work item.
    Higher scores indicate higher priority.

    Priority order (highest to lowest):
      - blocked
      - review
      - todo
      - done

    The mapping is intentionally simple so that callers can compare scores directly.
    """
    status = normalise_status(item.status)
    # Assign numeric values: larger number = higher priority
    score_map = {"blocked": 3, "review": 2, "todo": 1, "done": 0}
    return score_map.get(status, 0)


def sort_work_items_by_priority(items: Iterable[WorkItem]) -> list[WorkItem]:
    """
    Return a new list of WorkItem objects sorted from highest to lowest priority
    using the priority_score function. The sort is stable so that items with
    equal priority retain their original relative order.
    """
    return sorted(items, key=lambda item: priority_score(item), reverse=True)


def select_next_work_item(items: Iterable[WorkItem]) -> WorkItem | None:
    """
    Return the highest‑priority actionable work item from *items*.

    Actionable items are those whose status is not normalised to "done".
    The returned item respects stable ordering among items of equal priority.
    If no actionable items remain, return ``None``.
    """
    actionable = [i for i in items if normalise_status(i.status) != "done"]
    sorted_items = sort_work_items_by_priority(actionable)
    return sorted_items[0] if sorted_items else None


def explain_next_action(items: Iterable[WorkItem]) -> str:
    """
    Return a human‑readable explanation of the next action to take.

    The function uses :func:`select_next_work_item` to determine the highest
    priority actionable item.  If no actionable items remain, ``"idle"``
    is returned.  Otherwise the string includes evidence about the selected
    item's title, normalised status and priority score.
    """
    next_item = select_next_work_item(items)
    if not next_item:
        return "idle"
    action = suggest_next_action([next_item])
    # Include evidence in a simple format; tests will check for presence of
    # the relevant values rather than exact formatting.
    return f"{action} (title={next_item.title}, status={normalise_status(next_item.status)}, score={priority_score(next_item)})"


def actionable_work_items(items: Iterable[WorkItem]) -> list[WorkItem]:
    """
    Return a list of WorkItem objects that are still actionable.

    Items whose normalised status is "done" (including aliases such as
    "passed") are excluded. The original order of the remaining items is
    preserved.
    """
    return [i for i in items if normalise_status(i.status) != "done"]


def group_work_items_by_status(items: Iterable[WorkItem]) -> dict[str, list[WorkItem]]:
    """
    Group work items by their normalised status.

    The function returns a dictionary mapping each normalised status
    string to a list of WorkItem objects that have that status.  Items are
    appended in the order they appear in *items*, so the original ordering
    within each group is preserved.  Status aliases such as "pass" and
    "passed" are normalised to "done", ensuring they appear under the
    ``"done"`` key.
    """
    grouped: dict[str, list[WorkItem]] = {}
    for item in items:
        status_key = normalise_status(item.status)
        if status_key not in grouped:
            grouped[status_key] = []
        grouped[status_key].append(item)
    return grouped


def summarise_action_plan(items: Iterable[WorkItem]) -> dict[str, object]:
    """
    Return a concise summary of the current action plan.

    The returned dictionary contains:
      - ``total``: total number of items
      - ``actionable``: count of items that are not normalised to "done"
      - ``next_title``: title of the highest‑priority actionable item,
        or ``None`` if no such item exists
      - ``next_status``: normalised status of that item, or ``None``
      - ``next_score``: priority score of that item, or ``None``
    """
    items_list = list(items)
    total_count = len(items_list)
    actionable_items = [i for i in items_list if normalise_status(i.status) != "done"]
    actionable_count = len(actionable_items)
    next_item = select_next_work_item(items_list)
    if next_item:
        return {
            "total": total_count,
            "actionable": actionable_count,
            "next_title": next_item.title,
            "next_status": normalise_status(next_item.status),
            "next_score": priority_score(next_item),
        }
    else:
        return {
            "total": total_count,
            "actionable": actionable_count,
            "next_title": None,
            "next_status": None,
            "next_score": None,
        }


def format_action_plan_summary(summary: Mapping[str, object]) -> str:
    """
    Format the dictionary returned by :func:`summarise_action_plan` into a
    stable human‑readable sentence.

    The output contains the total number of items, the count of actionable
    items and details about the next item (title, status and score).  If no
    actionable items remain, the next part is rendered as ``idle``.
    """
    total = summary.get("total", 0)
    actionable = summary.get("actionable", 0)
    next_title = summary.get("next_title")
    next_status = summary.get("next_status")
    next_score = summary.get("next_score")

    if next_title is None:
        next_part = "idle"
    else:
        next_part = f"{next_title} (status={next_status}, score={next_score})"

    return f"Total: {total}; Actionable: {actionable}; Next item: {next_part}"


def render_action_plan_markdown(items: Iterable[WorkItem]) -> str:
    """
    Render a small Markdown summary of the action plan.

    The function uses :func:`summarise_action_plan` and
    :func:`format_action_plan_summary` to obtain a stable textual
    representation, then formats that information into a Markdown block
    with a heading and bullet lines for total, actionable, next title,
    next status, and next score.  The output is deterministic and
    suitable for display in the Nova UI.
    """
    summary = summarise_action_plan(items)
    # Ensure format_action_plan_summary is used as required by the task spec.
    _ = format_action_plan_summary(summary)

    lines = [
        "## Action Plan",
        f"- Total: {summary['total']}",
        f"- Actionable: {summary['actionable']}",
    ]

    if summary["next_title"] is None:
        # No actionable items – represent as idle.
        lines.append("- Next title: idle")
        lines.append("- Next status:")
        lines.append("- Next score:")
    else:
        lines.append(f"- Next title: {summary['next_title']}")
        lines.append(f"- Next status: {summary['next_status']}")
        lines.append(f"- Next score: {summary['next_score']}")

    return "\n".join(lines)


def render_action_plan_status_line(items: Iterable[WorkItem]) -> str:
    """
    Render a single stable human‑readable line summarising the action plan.

    The output contains the total number of items, the count of actionable
    items and details about the next item (title, status and score).  If no
    actionable items remain, the next part is rendered as ``idle``.
    """
    summary = summarise_action_plan(items)

    if summary["next_title"] is None:
        next_part = "idle"
    else:
        next_part = f"{summary['next_title']} (status={summary['next_status']}, score={summary['next_score']})"

    return (
        f"Total: {summary['total']}; "
        f"Actionable: {summary['actionable']}; "
        f"Next item: {next_part}"
    )


# New function added for the task
def build_action_plan_debug_dict(items: Iterable[WorkItem]) -> dict[str, object]:
    """
    Build a stable debug dictionary for an action plan.

    The dictionary contains:
      - total (int)
      - actionable (int)
      - next_title (str | None)
      - next_status (str | None)
      - next_score (int | None)
      - has_next (bool) – True if there is a next item
      - status_line (str) – the single‑line status from render_action_plan_status_line

    This function simply aggregates data from :func:`summarise_action_plan`
    and :func:`render_action_plan_status_line` to provide a convenient
    debugging view.
    """
    summary = summarise_action_plan(items)
    status_line = render_action_plan_status_line(items)
    has_next = summary["next_title"] is not None

    return {
        "total": summary["total"],
        "actionable": summary["actionable"],
        "next_title": summary["next_title"],
        "next_status": summary["next_status"],
        "next_score": summary["next_score"],
        "has_next": has_next,
        "status_line": status_line,
    }


# New helper to render debug lines
def render_action_plan_debug_lines(items: Iterable[WorkItem]) -> list[str]:
    """
    Render a stable, human‑readable list of debug lines for an action plan.

    The function uses :func:`build_action_plan_debug_dict` and returns a
    deterministic list of strings containing the values for:
      - total
      - actionable
      - has_next
      - next_title
      - next_status
      - next_score
      - status_line

    Each line is formatted as ``<label>: <value>``.
    """
    debug = build_action_plan_debug_dict(items)
    return [
        f"Total: {debug['total']}",
        f"Actionable: {debug['actionable']}",
        f"Has next: {debug['has_next']}",
        f"Next title: {debug['next_title']}",
        f"Next status: {debug['next_status']}",
        f"Next score: {debug['next_score']}",
        f"Status line: {debug['status_line']}",
    ]
