from __future__ import annotations

"""Safe browser-worker planning primitives.

This is a bounded, testable planning layer only. It does not drive a real
browser unless a future worker explicitly implements the generated plan.
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

BrowserAction = Literal["navigate", "read", "screenshot", "click", "type", "submit", "download"]

_WRITE_ACTIONS = {"click", "type", "submit", "download"}
_HIGH_RISK_WORDS = {"login", "password", "purchase", "buy", "checkout", "submit", "download", "account", "email"}


@dataclass(slots=True)
class BrowserStep:
    action: BrowserAction
    target: str
    value: str = ""
    requires_approval: bool = False
    evidence: list[str] = field(default_factory=list)
    reason: str = ""


def classify_browser_request(goal: str) -> dict[str, Any]:
    low = (goal or "").lower()
    wants_write = any(word in low for word in _HIGH_RISK_WORDS)
    read_only = not wants_write and not any(x in low for x in ["click", "fill", "type", "submit", "download"])
    return {
        "read_only": read_only,
        "risk": "medium" if wants_write else "low",
        "requires_approval": wants_write,
        "reason": "contains form/account/download/purchase-like wording" if wants_write else "read-only research/screenshot plan",
    }


def build_browser_task_plan(goal: str, *, start_url: str = "", allow_write: bool = False) -> dict[str, Any]:
    classification = classify_browser_request(goal)
    steps: list[BrowserStep] = []
    if start_url:
        steps.append(BrowserStep("navigate", start_url, evidence=["url"], reason="open the requested page"))
    else:
        steps.append(BrowserStep("read", "current page", evidence=["dom_snapshot"], reason="inspect current page before acting"))
    steps.append(BrowserStep("screenshot", "page", evidence=["screenshot_before"], reason="capture visible evidence"))
    steps.append(BrowserStep("read", "page text and accessible DOM", evidence=["dom_snapshot", "text_excerpt"], reason="extract answerable information"))
    if classification["requires_approval"]:
        steps.append(BrowserStep("click", "pending user-approved target", requires_approval=not allow_write, evidence=["screenshot_after"], reason="write action blocked until approval"))
    return {
        "goal": goal,
        "start_url": start_url,
        "ok": True,
        "mode": "dry_run_plan",
        "classification": classification,
        "steps": [asdict(step) for step in steps],
        "safety_rules": [
            "read-only by default",
            "approval before login/form submission/purchase/download/account changes",
            "screenshots before and after important actions",
            "record source URL and timestamp in the final report",
        ],
    }


def render_browser_task_plan(plan: dict[str, Any]) -> str:
    c = plan.get("classification", {})
    lines = ["# Nova Browser Worker Plan", "", f"Goal: {plan.get('goal')}", f"Mode: `{plan.get('mode')}`", f"Risk: **{c.get('risk')}** — {c.get('reason')}", "", "## Steps"]
    for i, step in enumerate(plan.get("steps", []), start=1):
        gate = " requires approval" if step.get("requires_approval") else ""
        lines.append(f"{i}. `{step.get('action')}` {step.get('target')}{gate} — {step.get('reason')}")
    lines += ["", "## Safety rules", *[f"- {rule}" for rule in plan.get("safety_rules", [])]]
    return "\n".join(lines)
