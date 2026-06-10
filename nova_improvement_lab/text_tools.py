from __future__ import annotations

import re


def normalise_whitespace(text: str) -> str:
    """Return text with repeated whitespace collapsed."""
    return re.sub(r"\s+", " ", str(text or "")).strip()


def extract_change_keywords(text: str) -> list[str]:
    """Extract stable improvement-related keywords from free text."""
    cleaned = normalise_whitespace(text).lower()
    words = re.findall(r"[a-z][a-z0-9_-]{2,}", cleaned)
    stop = {
        "the", "and", "for", "with", "that", "this", "into", "from",
        "make", "add", "fix", "improve", "better", "nova",
    }
    out: list[str] = []
    seen: set[str] = set()
    for word in words:
        if word in stop:
            continue
        if word in seen:
            continue
        seen.add(word)
        out.append(word)
    return out[:12]


def score_candidate_improvement(
    *,
    touches_source: bool,
    has_test: bool,
    risk: str = "medium",
    user_visible: bool = False,
) -> int:
    """Score a candidate improvement so the lab can practise safe task ranking."""
    score = 0
    if touches_source:
        score += 35
    if has_test:
        score += 35
    if user_visible:
        score += 10

    risk_normalised = str(risk or "").lower()
    if risk_normalised == "low":
        score += 10
    elif risk_normalised == "high":
        score -= 30

    return max(0, min(100, score))
