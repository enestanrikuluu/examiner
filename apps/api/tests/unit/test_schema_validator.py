from src.ai.verification.schema_validator import validate_generated_questions


def test_valid_mcq_passes() -> None:
    raw = [
        {
            "question_type": "mcq",
            "stem": "2+2 kaçtır?",
            "options": [
                {"key": "A", "text": "3"},
                {"key": "B", "text": "4"},
                {"key": "C", "text": "5"},
                {"key": "D", "text": "6"},
            ],
            "correct_answer": {"key": "B"},
        }
    ]
    valid, errors = validate_generated_questions(raw, expected_type="mcq")
    assert len(valid) == 1
    assert len(errors) == 0


def test_invalid_mcq_caught() -> None:
    raw = [
        {
            "question_type": "mcq",
            "stem": "Test?",
            "options": [{"key": "A", "text": "Only one"}],
            "correct_answer": {"key": "A"},
        }
    ]
    valid, errors = validate_generated_questions(raw)
    assert len(valid) == 0
    assert len(errors) == 1


def test_missing_question_type_caught() -> None:
    raw = [{"stem": "Test?", "correct_answer": {"key": "A"}}]
    valid, errors = validate_generated_questions(raw)
    assert len(valid) == 0
    assert len(errors) == 1


def test_expected_type_override() -> None:
    raw = [
        {
            "stem": "Is sky blue?",
            "correct_answer": {"value": True},
        }
    ]
    valid, _errors = validate_generated_questions(raw, expected_type="true_false")
    assert len(valid) == 1
    assert valid[0].question_type == "true_false"


def test_mixed_valid_and_invalid() -> None:
    raw = [
        {
            "question_type": "true_false",
            "stem": "Sky is blue.",
            "correct_answer": {"value": True},
        },
        {
            "question_type": "mcq",
            "stem": "Bad question",
            "correct_answer": {"key": "Z"},
            # Missing options
        },
    ]
    valid, errors = validate_generated_questions(raw)
    assert len(valid) == 1
    assert len(errors) == 1
