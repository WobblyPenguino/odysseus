from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


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
