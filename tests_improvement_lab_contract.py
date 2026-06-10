from nova_improvement_lab.text_tools import (
    extract_change_keywords,
    normalise_whitespace,
    score_candidate_improvement,
)


def test_normalise_whitespace_collapses_spaces_tabs_and_newlines():
    assert normalise_whitespace("  improve\tNova\n\n safely  ") == "improve Nova safely"


def test_extract_change_keywords_removes_duplicates_and_common_words():
    assert extract_change_keywords("Improve Nova validation validation workflow safely") == [
        "validation",
        "workflow",
        "safely",
    ]


def test_score_candidate_improvement_rewards_source_and_tests():
    assert score_candidate_improvement(touches_source=True, has_test=True, risk="low") >= 80


def test_score_candidate_improvement_penalises_high_risk_without_tests():
    assert score_candidate_improvement(touches_source=True, has_test=False, risk="high") < 35
