from __future__ import annotations

import ast
import operator
import re
from dataclasses import dataclass
from typing import Any

SKILL_MODES = {"auto", "general", "coding", "math", "science", "communication"}

@dataclass(frozen=True)
class SkillProfile:
    mode: str
    title: str
    prompt: str
    examples: tuple[str, ...]

SKILL_PROFILES: dict[str, SkillProfile] = {
    "general": SkillProfile(
        "general",
        "General helper",
        "Answer directly, be honest about uncertainty, and choose a clear structure for the user's goal.",
        ("Explain a concept", "Summarise a file", "Brainstorm options"),
    ),
    "coding": SkillProfile(
        "coding",
        "Coding and debugging specialist",
        (
            "Prioritise runnable, maintainable code. Start from the user's exact environment and error text. "
            "When changing code, identify the likely root cause, give exact file/command steps, mention tests, "
            "and avoid vague rewrites. For Windows users, prefer PowerShell commands."
        ),
        ("/code why does this traceback happen?", "/code review this function", "/code make exact test commands"),
    ),
    "math": SkillProfile(
        "math",
        "Math reasoning specialist",
        (
            "Solve carefully. Define variables, show the key equations, keep units where relevant, verify arithmetic, "
            "and call out assumptions. For pure arithmetic, give the result and a short check. Do not invent certainty."
        ),
        ("/math solve 2x+5=17", "/math derive the formula", "/math check my calculation"),
    ),
    "science": SkillProfile(
        "science",
        "Science explanation specialist",
        (
            "Use evidence-based scientific reasoning. Separate observation, hypothesis, mechanism and limitations. "
            "Use correct units, uncertainty and assumptions. Explain like a tutor without overclaiming."
        ),
        ("/science explain diphtheria", "/science check this chemistry reasoning", "/science design a small experiment"),
    ),
    "communication": SkillProfile(
        "communication",
        "Communication and writing specialist",
        (
            "Write naturally and clearly. Match the audience and purpose. Prefer concise paragraph-form where appropriate, "
            "avoid robotic phrasing, avoid unnecessary hyphens, and preserve the user's meaning while improving flow."
        ),
        ("/communicate rewrite this naturally", "/communicate make this cover-letter answer stronger", "/communicate draft a polite email"),
    ),
}

_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("coding", ("traceback", "python", "javascript", "typescript", "powershell", "bug", "debug", "function", "class", "repo", "pytest", "compile", "api", "code", "script")),
    ("math", ("solve", "equation", "algebra", "calculus", "derivative", "integral", "matrix", "probability", "statistics", "geometry", "percent", "formula", "calculate")),
    ("science", ("chemistry", "physics", "biology", "science", "molecule", "reaction", "energy", "force", "experiment", "hypothesis", "lab", "pfas", "environmental", "disease")),
    ("communication", ("cover letter", "resume", "cv", "email", "rewrite", "make this sound", "paragraph", "interview", "application", "tone", "polish", "grammar")),
]


def normalise_skill_mode(value: str | None) -> str:
    mode = (value or "auto").strip().lower()
    aliases = {
        "chat": "general",
        "generalist": "general",
        "code": "coding",
        "programming": "coding",
        "debugging": "coding",
        "maths": "math",
        "stem": "science",
        "writing": "communication",
        "comms": "communication",
        "communicate": "communication",
    }
    mode = aliases.get(mode, mode)
    return mode if mode in SKILL_MODES else "auto"


def detect_skill_mode(text: str) -> str:
    lowered = (text or "").lower()
    best_mode = "general"
    best_score = 0
    for mode, terms in _KEYWORDS:
        score = sum(1 for term in terms if term in lowered)
        if score > best_score:
            best_mode = mode
            best_score = score
    return best_mode


def choose_skill_mode(configured_mode: str | None, text: str) -> str:
    mode = normalise_skill_mode(configured_mode)
    if mode == "auto":
        return detect_skill_mode(text)
    return mode


def skill_prompt(mode: str) -> str:
    profile = SKILL_PROFILES.get(normalise_skill_mode(mode), SKILL_PROFILES["general"])
    return f"Skill profile: {profile.title}. {profile.prompt}"


def skill_status_text(configured_mode: str | None) -> str:
    configured = normalise_skill_mode(configured_mode)
    lines = ["# Nova Skill Mode", "", f"Current mode: **{configured}**", ""]
    lines.append("Modes:")
    lines.append("- `auto`: detect coding, math, science or communication from the request")
    for mode in ["general", "coding", "math", "science", "communication"]:
        profile = SKILL_PROFILES[mode]
        lines.append(f"- `{mode}`: {profile.title}")
    lines.extend([
        "",
        "Direct commands:",
        "- `/code QUESTION` for coding/debugging help",
        "- `/math QUESTION` for maths with checked steps",
        "- `/science QUESTION` for science reasoning",
        "- `/communicate TEXT` for clear writing and rewriting",
        "",
        "Set mode with `/skill-mode auto|general|coding|math|science|communication`.",
    ])
    return "\n".join(lines)

_ALLOWED_BINOPS: dict[type[ast.operator], Any] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_ALLOWED_UNARY: dict[type[ast.unaryop], Any] = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def _eval_number_node(node: ast.AST) -> float | int:
    if isinstance(node, ast.Expression):
        return _eval_number_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
        left = _eval_number_node(node.left)
        right = _eval_number_node(node.right)
        if isinstance(node.op, ast.Pow) and abs(float(right)) > 12:
            raise ValueError("Exponent too large for safe quick calculation.")
        return _ALLOWED_BINOPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY:
        return _ALLOWED_UNARY[type(node.op)](_eval_number_node(node.operand))
    raise ValueError("Only numeric arithmetic is supported by the quick calculator.")


def try_quick_arithmetic(text: str) -> str | None:
    """Return a deterministic answer for simple arithmetic prompts, otherwise None."""
    raw = (text or "").strip()
    cleaned = raw.lower().replace("what is", "").replace("calculate", "").replace("=", "")
    cleaned = cleaned.replace("×", "*").replace("÷", "/").replace("^", "**")
    cleaned = re.sub(r"[^0-9+\-*/().%\s]", "", cleaned).strip()
    if not cleaned or not re.fullmatch(r"[0-9+\-*/().%\s]+", cleaned):
        return None
    # Avoid treating a lone number as a solved expression.
    if not any(op in cleaned for op in ["+", "-", "*", "/", "%"]):
        return None
    try:
        tree = ast.parse(cleaned, mode="eval")
        value = _eval_number_node(tree)
    except Exception:
        return None
    if isinstance(value, float) and value.is_integer():
        value_text = str(int(value))
    else:
        value_text = f"{value:.10g}"
    return f"{cleaned} = **{value_text}**"
