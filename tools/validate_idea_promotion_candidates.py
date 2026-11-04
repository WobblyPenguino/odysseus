
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")


@dataclass
class ValidationResult:
    valid: bool
    candidate_id: str
    errors: list[str]


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _clean_list(value: Any) -> list[str]:
    return [str(v).strip() for v in _as_list(value) if str(v).strip()]


def is_safe_candidate_path(path: str, *, test_only: bool = False) -> bool:
    normal = str(path).strip().replace("/", "\\")
    if not normal:
        return False

    p = Path(normal)
    if p.is_absolute():
        return False

    parts = [part.lower() for part in p.parts]
    if ".." in parts or ".git" in parts:
        return False

    if test_only:
        return normal.startswith("tests\\") or (normal.startswith("tests_") and normal.endswith(".py"))

    allowed_runtime_files = {
        "winlocalassistant\\model_context.py",
        "winlocalassistant\\agent_browser_safety.py",
    }

    return (
        normal in allowed_runtime_files
    ) or (
        normal.startswith("nova_improvement_lab\\") and normal.endswith(".py")
    ) or normal.startswith("tests\\") or (
        normal.startswith("tests_") and normal.endswith(".py")
    )


def validate_candidate(candidate: dict[str, Any], seen_ids: set[str]) -> ValidationResult:
    errors: list[str] = []

    candidate_id = str(candidate.get("Id", "")).strip()
    if not candidate_id:
        errors.append("missing Id")
    elif any(ch.isspace() for ch in candidate_id):
        errors.append("Id must be one token with no whitespace")
    elif not ID_RE.match(candidate_id):
        errors.append("Id contains unsupported characters")
    elif candidate_id in seen_ids:
        errors.append("duplicate Id")

    goal = str(candidate.get("Goal", "")).strip()
    if not goal:
        errors.append("missing Goal")

    editable = _clean_list(candidate.get("Editable"))
    required_files = _clean_list(candidate.get("RequiredChangedFiles"))
    required_diff = _clean_list(candidate.get("RequiredDiffContains"))
    tests = _clean_list(candidate.get("Tests"))

    if not editable:
        errors.append("missing Editable")
    if not required_files:
        errors.append("missing RequiredChangedFiles")
    if not required_diff:
        errors.append("missing RequiredDiffContains")
    if not tests:
        errors.append("missing Tests")

    for file in editable:
        if not is_safe_candidate_path(file):
            errors.append(f"unsafe Editable path: {file}")

    for file in required_files:
        if not is_safe_candidate_path(file):
            errors.append(f"unsafe RequiredChangedFiles path: {file}")
        if file not in editable:
            errors.append(f"required changed file not listed as editable: {file}")

    for marker in required_diff:
        if len(marker) > 120:
            errors.append(f"RequiredDiffContains marker too long: {marker}")

    for test in tests:
        if not is_safe_candidate_path(test, test_only=True):
            errors.append(f"unsafe Tests path: {test}")

    return ValidationResult(valid=not errors, candidate_id=candidate_id, errors=errors)


def load_candidates(path: Path) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        raw = [raw]
    if not isinstance(raw, list):
        raise ValueError("candidate config must be a JSON object or array")

    candidates: list[dict[str, Any]] = []
    for item in raw:
        if isinstance(item, list):
            candidates.extend(x for x in item if isinstance(x, dict))
        elif isinstance(item, dict):
            candidates.append(item)
    return candidates


def validate_candidates(candidates: list[dict[str, Any]]) -> tuple[list[ValidationResult], list[ValidationResult]]:
    seen: set[str] = set()
    accepted: list[ValidationResult] = []
    rejected: list[ValidationResult] = []

    for candidate in candidates:
        result = validate_candidate(candidate, seen)
        if result.valid:
            accepted.append(result)
            seen.add(result.candidate_id)
        else:
            rejected.append(result)

    return accepted, rejected


def run_probe() -> int:
    valid = {
        "Id": "probe-valid-task-v1",
        "Goal": "Add a tiny safe source and test improvement.",
        "Editable": ["nova_improvement_lab\\autodev_sandbox.py", "tests_autodev_sandbox.py"],
        "RequiredChangedFiles": ["nova_improvement_lab\\autodev_sandbox.py", "tests_autodev_sandbox.py"],
        "RequiredDiffContains": ["probe_marker", "test_probe_marker"],
        "Tests": ["tests_autodev_sandbox.py"],
    }

    bad_id = dict(valid, Id="bad id with spaces")
    unsafe_path = dict(valid, Id="probe-unsafe-path-v1", Editable=["..\\secrets.txt"])
    duplicate = dict(valid, Id="probe-valid-task-v1")

    accepted, rejected = validate_candidates([valid, bad_id, unsafe_path, duplicate])

    expected_rejections = {
        "bad id with spaces": "Id must be one token with no whitespace",
        "probe-unsafe-path-v1": "unsafe Editable path",
        "probe-valid-task-v1": "duplicate Id",
    }

    if len(accepted) != 1 or accepted[0].candidate_id != "probe-valid-task-v1":
        print("probe: FAIL - valid candidate was not accepted correctly")
        return 1

    for candidate_id, expected in expected_rejections.items():
        matching = [r for r in rejected if r.candidate_id == candidate_id and any(expected in e for e in r.errors)]
        if not matching:
            print(f"probe: FAIL - expected rejection missing for {candidate_id}: {expected}")
            return 1

    print("probe: PASS")
    print(f"probe accepted={len(accepted)} rejected={len(rejected)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path)
    parser.add_argument("--probe", action="store_true")
    args = parser.parse_args()

    exit_code = 0

    if args.config:
        candidates = load_candidates(args.config)
        accepted, rejected = validate_candidates(candidates)
        print(f"candidate validation accepted: {len(accepted)}; rejected: {len(rejected)}")
        for result in rejected:
            print(f"rejected {result.candidate_id}: {'; '.join(result.errors)}")
        if rejected:
            exit_code = 1

    if args.probe:
        probe_exit = run_probe()
        exit_code = max(exit_code, probe_exit)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
