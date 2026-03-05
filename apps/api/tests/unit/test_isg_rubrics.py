"""Tests for ISG default rubrics."""

from src.isg.rubrics import (
    DEFAULT_RUBRICS,
    TOPIC_RUBRIC_MAP,
    get_rubric,
    get_rubric_for_topic,
    list_rubrics,
)


def test_all_rubrics_present() -> None:
    assert len(DEFAULT_RUBRICS) == 5
    expected_ids = {
        "isg_risk_assessment",
        "isg_workplace_inspection",
        "isg_accident_analysis",
        "isg_emergency_plan",
        "isg_legislation",
    }
    assert set(DEFAULT_RUBRICS.keys()) == expected_ids


def test_list_rubrics() -> None:
    rubrics = list_rubrics()
    assert len(rubrics) == 5


def test_get_rubric_valid() -> None:
    rubric = get_rubric("isg_risk_assessment")
    assert rubric is not None
    assert rubric.name == "Risk Değerlendirme Sorusu"
    assert rubric.max_score == 20.0


def test_get_rubric_invalid() -> None:
    assert get_rubric("nonexistent") is None


def test_rubric_criteria_scores_sum_to_max() -> None:
    for rubric in list_rubrics():
        criteria_total = sum(c.max_points for c in rubric.criteria)
        assert criteria_total == rubric.max_score, (
            f"Rubric '{rubric.rubric_id}' criteria sum {criteria_total} "
            f"!= max_score {rubric.max_score}"
        )


def test_rubric_to_dict() -> None:
    rubric = get_rubric("isg_risk_assessment")
    assert rubric is not None
    d = rubric.to_dict()
    assert d["max_score"] == 20.0
    assert isinstance(d["criteria"], list)
    assert len(d["criteria"]) == 5
    assert d["criteria"][0]["id"] == "tehlike_tanimlama"
    assert d["criteria"][0]["max_points"] == 5.0


def test_rubric_criteria_have_descriptions() -> None:
    for rubric in list_rubrics():
        for c in rubric.criteria:
            assert c.description, f"Criterion '{c.id}' in '{rubric.rubric_id}' has no description"
            assert c.max_points > 0


def test_topic_rubric_map() -> None:
    assert "risk_degerlendirme" in TOPIC_RUBRIC_MAP
    assert "mevzuat" in TOPIC_RUBRIC_MAP


def test_get_rubric_for_topic() -> None:
    rubric = get_rubric_for_topic("risk_degerlendirme")
    assert rubric is not None
    assert rubric.rubric_id == "isg_risk_assessment"


def test_get_rubric_for_topic_no_mapping() -> None:
    rubric = get_rubric_for_topic("nonexistent_topic")
    assert rubric is None


def test_get_rubric_for_topic_legislation() -> None:
    rubric = get_rubric_for_topic("mevzuat")
    assert rubric is not None
    assert rubric.rubric_id == "isg_legislation"
