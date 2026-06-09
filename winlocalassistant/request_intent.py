from __future__ import annotations

import re
from dataclasses import asdict, dataclass


@dataclass
class RequestIntent:
    raw_text: str
    category: str
    explicit_command: bool
    wants_build: bool
    wants_edit: bool
    target_is_wla_source: bool
    self_improvement_requested: bool
    forbids_auto_apply: bool
    explicit_manual_self_improve: bool
    safe_for_automatic_mutation: bool
    reasons: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def analyze_request_intent(text: str) -> RequestIntent:
    raw = (text or "").strip()
    low = _normalise(_fix_common_request_typos(raw))
    words = set(re.findall(r"[a-z][a-z0-9]*", low))
    explicit_command = low.startswith("/")
    failure_feedback = _is_failure_feedback_request(low)

    wants_build = (not failure_feedback) and _contains_any(low, [
        "make ",
        "build ",
        "create ",
        "generate ",
        "scaffold ",
        "new app",
        "new project",
        "write code",
        "scaffold ",
    ])
    wants_edit = (not failure_feedback) and bool(
        re.match(r"^(continue|edit|fix|improve|update|change|add|patch|modify|expand|repair)\b", low)
        or _contains_any(low, [
            " add ",
            " fix ",
            " improve ",
            " update ",
            " change ",
            " repair ",
            "implement ",
            "integrate ",
            "better at ",
            "voice mode",
            "talk to it",
            "talk back",
        ])
    )

    explicit_manual_self_improve = low.startswith("/self-improve") or _contains_any(low, [
        "manual self-improve",
        "manual guarded self-improvement",
        "run self-improve manually",
        "use self-improve manually",
    ])
    self_improvement_requested = explicit_manual_self_improve or _contains_any(low, [
        "self-improve",
        "self improve",
        "self-improvement",
        "self improvement",
        "improve yourself",
        "improve itself",
        "edit yourself",
        "your own source",
        "your own code",
        "your own files",
        "your files",
        "own files",
        "review your code",
        "review your own code",
        "coding capabilities",
        "validation capabilities",
        "your coding",
        "your validation",
        "assistant source",
        "assistant code",
        "nova source",
        "nova code",
        "nova's code",
        "nova's source",
        "nova coding capability",
        "nova coding capabilities",
        "nova validation capability",
        "nova validation capabilities",
    ])
    target_is_wla_source = self_improvement_requested or _has_word(words, "wla") or _has_word(words, "nova") and _contains_any(low, ["improve", "update", "edit", "refactor", "rebrand", "source", "code", "capability"]) or _contains_any(low, [
        "winlocalassistant",
        "win local assistant",
        "this assistant",
        "nova source",
        "nova code",
        "wla source",
        "wla code",
        "core.py",
        "tools.py",
        "idle_engine.py",
        "autonomous failure memory",
        "request intent checks",
        "determine what the human is asking",
        "what the human is asking",
        "intent router",
        "intent detection",
        "voice mode",
    ])
    forbids_auto_apply = _contains_any(low, [
        "do not auto-apply",
        "dont auto-apply",
        "don't auto-apply",
        "do not auto apply",
        "dont auto apply",
        "don't auto apply",
        "no auto-apply",
        "no auto apply",
        "do not apply edits automatically",
        "don't apply edits automatically",
        "dont apply edits automatically",
        "do not automatically edit",
        "proposal only",
        "proposal-only",
        "dry run",
        "dry-run",
    ])

    reasons: list[str] = []
    if failure_feedback:
        reasons.append("request is feedback about the previous run, not a new artifact request")
    if target_is_wla_source:
        reasons.append("request targets Nova/self-improvement source")
    if self_improvement_requested and not explicit_manual_self_improve:
        reasons.append("self-improvement was requested outside the manual /self-improve command")
    if forbids_auto_apply:
        reasons.append("request forbids automatic edit application")

    category = "chat"
    if failure_feedback:
        category = "diagnostic_repair"
    elif target_is_wla_source or self_improvement_requested:
        category = "self_improvement"
    elif wants_build:
        category = "project_build"
    elif wants_edit:
        category = "project_edit"

    safe_for_automatic_mutation = not (
        (target_is_wla_source or self_improvement_requested or forbids_auto_apply)
        and not explicit_manual_self_improve
    )
    return RequestIntent(
        raw_text=raw,
        category=category,
        explicit_command=explicit_command,
        wants_build=wants_build,
        wants_edit=wants_edit,
        target_is_wla_source=target_is_wla_source,
        self_improvement_requested=self_improvement_requested,
        forbids_auto_apply=forbids_auto_apply,
        explicit_manual_self_improve=explicit_manual_self_improve,
        safe_for_automatic_mutation=safe_for_automatic_mutation,
        reasons=reasons,
    )


def should_block_automatic_mutation(intent: RequestIntent) -> bool:
    return not bool(intent.safe_for_automatic_mutation)


def _is_failure_feedback_request(text: str) -> bool:
    low = _normalise(_fix_common_request_typos(text))
    complaint_markers = [
        "you didnt", "you didn't", "you did not", "didnt actually", "didn't actually",
        "did not actually", "didnt make", "didn't make", "did not make",
        "didnt give", "didn't give", "did not give", "nothing happened",
        "not actually make", "it made nothing", "it didn't make", "it didnt make",
        "keeps repeating", "keeps looping", "candidate_refine", "model output did not",
    ]
    if any(marker in low for marker in complaint_markers):
        return True
    if "why" in low and "fix" in low and any(x in low for x in ["anything", "nothing", "actual", "actually", "loop", "repeat", "failed"]):
        return True
    return False


def _contains_any(text: str, needles: list[str]) -> bool:
    return any(needle in text for needle in needles)


def _has_word(words: set[str], word: str) -> bool:
    return word in words


def _fix_common_request_typos(text: str) -> str:
    replacements = {
        r"\bmkae\b": "make",
        r"\bmaek\b": "make",
        r"\bimp,?lemen\s*t\b": "implement",
        r"\bimplemnt\b": "implement",
        r"\bdetermineing\b": "determining",
        r"\bhuma\b": "human",
        r"\bbvopice\b": "voice",
        r"\bvoicemode\b": "voice mode",
        r"\btalkl\b": "talk",
        r"\buit\b": "it",
        r"\bdidntn\b": "didnt",
        r"\bactuall\b": "actually",
    }
    out = text or ""
    for pat, repl in replacements.items():
        out = re.sub(pat, repl, out, flags=re.I)
    return out


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())
