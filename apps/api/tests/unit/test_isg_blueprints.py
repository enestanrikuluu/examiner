"""Tests for ISG blueprints and topic taxonomy."""

from src.isg.blueprints import (
    BLUEPRINTS,
    ISG_TOPICS,
    TOPICS_BY_ID,
    get_blueprint,
    list_blueprints,
)


def test_all_classes_present() -> None:
    assert set(BLUEPRINTS.keys()) == {"A", "B", "C"}


def test_list_blueprints_returns_all() -> None:
    bps = list_blueprints()
    assert len(bps) == 3
    classes = {bp.exam_class for bp in bps}
    assert classes == {"A", "B", "C"}


def test_get_blueprint_valid() -> None:
    bp = get_blueprint("A")
    assert bp is not None
    assert bp.exam_class == "A"
    assert bp.total_questions == 50


def test_get_blueprint_case_insensitive() -> None:
    bp = get_blueprint("b")
    assert bp is not None
    assert bp.exam_class == "B"


def test_get_blueprint_invalid() -> None:
    assert get_blueprint("D") is None
    assert get_blueprint("") is None


def test_topic_weights_sum_to_one() -> None:
    for bp in list_blueprints():
        total_weight = sum(tw.weight for tw in bp.topic_weights)
        assert abs(total_weight - 1.0) < 0.01, (
            f"Blueprint {bp.exam_class} weights sum to {total_weight}"
        )


def test_topic_question_counts_match_total() -> None:
    for bp in list_blueprints():
        total_questions = sum(tw.question_count for tw in bp.topic_weights)
        assert total_questions == bp.total_questions, (
            f"Blueprint {bp.exam_class}: question counts {total_questions} "
            f"!= total {bp.total_questions}"
        )


def test_all_topic_ids_exist_in_taxonomy() -> None:
    for bp in list_blueprints():
        for tw in bp.topic_weights:
            assert tw.topic_id in TOPICS_BY_ID, (
                f"Blueprint {bp.exam_class} references unknown topic '{tw.topic_id}'"
            )


def test_topics_have_subtopics() -> None:
    for topic in ISG_TOPICS:
        assert len(topic.subtopics) > 0, f"Topic '{topic.id}' has no subtopics"


def test_topic_ids_unique() -> None:
    ids = [t.id for t in ISG_TOPICS]
    assert len(ids) == len(set(ids))


def test_subtopic_ids_unique() -> None:
    all_sub_ids: list[str] = []
    for t in ISG_TOPICS:
        all_sub_ids.extend(s.id for s in t.subtopics)
    assert len(all_sub_ids) == len(set(all_sub_ids))


def test_blueprint_pass_scores() -> None:
    a = get_blueprint("A")
    b = get_blueprint("B")
    c = get_blueprint("C")
    assert a is not None and b is not None and c is not None
    assert a.pass_score == 70.0
    assert b.pass_score == 70.0
    assert c.pass_score == 60.0


def test_blueprint_time_limits() -> None:
    for bp in list_blueprints():
        assert bp.time_limit_minutes == 75


def test_blueprint_allowed_question_types() -> None:
    for bp in list_blueprints():
        assert "mcq" in bp.allowed_question_types
        assert "long_form" in bp.allowed_question_types
