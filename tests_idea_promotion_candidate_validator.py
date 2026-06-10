
from tools.validate_idea_promotion_candidates import validate_candidates


def _valid_candidate(candidate_id="safe-task-v1"):
    return {
        "Id": candidate_id,
        "Goal": "Add a tiny safe source and test improvement.",
        "Editable": ["nova_improvement_lab\\autodev_sandbox.py", "tests_autodev_sandbox.py"],
        "RequiredChangedFiles": ["nova_improvement_lab\\autodev_sandbox.py", "tests_autodev_sandbox.py"],
        "RequiredDiffContains": ["safe_marker", "test_safe_marker"],
        "Tests": ["tests_autodev_sandbox.py"],
    }


def test_candidate_validator_accepts_safe_candidate():
    accepted, rejected = validate_candidates([_valid_candidate()])
    assert [r.candidate_id for r in accepted] == ["safe-task-v1"]
    assert rejected == []


def test_candidate_validator_rejects_id_with_spaces():
    accepted, rejected = validate_candidates([_valid_candidate("bad id")])
    assert accepted == []
    assert any("Id must be one token with no whitespace" in e for e in rejected[0].errors)


def test_candidate_validator_rejects_duplicate_ids():
    accepted, rejected = validate_candidates([_valid_candidate("dupe-v1"), _valid_candidate("dupe-v1")])
    assert [r.candidate_id for r in accepted] == ["dupe-v1"]
    assert any("duplicate Id" in e for e in rejected[0].errors)


def test_candidate_validator_rejects_unsafe_paths():
    candidate = _valid_candidate("unsafe-v1")
    candidate["Editable"] = ["..\\secrets.txt"]
    accepted, rejected = validate_candidates([candidate])
    assert accepted == []
    assert any("unsafe Editable path" in e for e in rejected[0].errors)


def test_candidate_validator_rejects_required_file_not_editable():
    candidate = _valid_candidate("missing-editable-v1")
    candidate["Editable"] = ["nova_improvement_lab\\autodev_sandbox.py"]
    accepted, rejected = validate_candidates([candidate])
    assert accepted == []
    assert any("required changed file not listed as editable" in e for e in rejected[0].errors)
