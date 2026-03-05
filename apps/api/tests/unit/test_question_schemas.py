import pytest
from pydantic import ValidationError

from src.questions.schemas import QuestionItemCreate


def test_valid_mcq_question() -> None:
    q = QuestionItemCreate(
        question_type="mcq",
        stem="What is 2+2?",
        options=[
            {"key": "A", "text": "3"},
            {"key": "B", "text": "4"},
            {"key": "C", "text": "5"},
            {"key": "D", "text": "6"},
        ],
        correct_answer={"key": "B"},
    )
    assert q.question_type == "mcq"
    assert len(q.options) == 4  # type: ignore[arg-type]


def test_mcq_requires_at_least_4_options() -> None:
    with pytest.raises(ValidationError, match="at least 4 options"):
        QuestionItemCreate(
            question_type="mcq",
            stem="What is 2+2?",
            options=[
                {"key": "A", "text": "3"},
                {"key": "B", "text": "4"},
            ],
            correct_answer={"key": "A"},
        )


def test_mcq_answer_key_must_exist_in_options() -> None:
    with pytest.raises(ValidationError, match="not found in options"):
        QuestionItemCreate(
            question_type="mcq",
            stem="What is 2+2?",
            options=[
                {"key": "A", "text": "3"},
                {"key": "B", "text": "4"},
                {"key": "C", "text": "5"},
                {"key": "D", "text": "6"},
            ],
            correct_answer={"key": "Z"},
        )


def test_valid_true_false_question() -> None:
    q = QuestionItemCreate(
        question_type="true_false",
        stem="The sky is blue.",
        correct_answer={"value": True},
    )
    assert q.question_type == "true_false"


def test_true_false_rejects_options() -> None:
    with pytest.raises(ValidationError, match="must not have options"):
        QuestionItemCreate(
            question_type="true_false",
            stem="The sky is blue.",
            options=[{"key": "A", "text": "True"}],
            correct_answer={"value": True},
        )


def test_valid_numeric_question() -> None:
    q = QuestionItemCreate(
        question_type="numeric",
        stem="What is pi to 2 decimal places?",
        correct_answer={"value": 3.14, "tolerance": 0.01},
    )
    assert q.question_type == "numeric"


def test_numeric_rejects_options() -> None:
    with pytest.raises(ValidationError, match="must not have options"):
        QuestionItemCreate(
            question_type="numeric",
            stem="What is pi?",
            options=[{"key": "A", "text": "3.14"}],
            correct_answer={"value": 3.14},
        )


def test_valid_short_answer_question() -> None:
    q = QuestionItemCreate(
        question_type="short_answer",
        stem="Name the capital of Turkey.",
        correct_answer={"keywords": ["Ankara"]},
    )
    assert q.question_type == "short_answer"


def test_valid_long_form_question() -> None:
    q = QuestionItemCreate(
        question_type="long_form",
        stem="Explain the importance of workplace safety.",
        correct_answer={},
        rubric={
            "max_score": 10.0,
            "criteria": [
                {"id": "c1", "description": "Clarity", "max_points": 5.0},
                {"id": "c2", "description": "Depth", "max_points": 5.0},
            ],
        },
    )
    assert q.question_type == "long_form"


def test_long_form_requires_rubric() -> None:
    with pytest.raises(ValidationError, match="must have a rubric"):
        QuestionItemCreate(
            question_type="long_form",
            stem="Explain the importance of workplace safety.",
            correct_answer={},
        )


def test_unknown_question_type_rejected() -> None:
    with pytest.raises(ValidationError, match="Unknown question_type"):
        QuestionItemCreate(
            question_type="essay",
            stem="Write something.",
            correct_answer={},
        )
