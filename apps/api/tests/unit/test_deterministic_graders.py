from src.grading.deterministic import (
    can_grade_deterministically,
    grade_deterministic,
    grade_mcq,
    grade_numeric,
    grade_short_answer,
    grade_true_false,
)

# --- MCQ ---

def test_mcq_correct() -> None:
    result = grade_mcq({"key": "B"}, {"key": "B"})
    assert result.score == 1.0
    assert result.is_correct is True
    assert result.feedback is None


def test_mcq_incorrect() -> None:
    result = grade_mcq({"key": "A"}, {"key": "B"})
    assert result.score == 0.0
    assert result.is_correct is False
    assert "B" in (result.feedback or "")


def test_mcq_case_insensitive() -> None:
    result = grade_mcq({"key": "b"}, {"key": "B"})
    assert result.is_correct is True


def test_mcq_custom_max_score() -> None:
    result = grade_mcq({"key": "A"}, {"key": "A"}, max_score=5.0)
    assert result.score == 5.0
    assert result.max_score == 5.0


# --- True/False ---

def test_tf_correct_true() -> None:
    result = grade_true_false({"value": True}, {"value": True})
    assert result.is_correct is True
    assert result.score == 1.0


def test_tf_correct_false() -> None:
    result = grade_true_false({"value": False}, {"value": False})
    assert result.is_correct is True


def test_tf_incorrect() -> None:
    result = grade_true_false({"value": True}, {"value": False})
    assert result.is_correct is False
    assert result.score == 0.0


def test_tf_string_normalization() -> None:
    result = grade_true_false({"value": "true"}, {"value": True})
    assert result.is_correct is True


def test_tf_turkish_normalization() -> None:
    result = grade_true_false({"value": "doğru"}, {"value": True})
    assert result.is_correct is True


# --- Numeric ---

def test_numeric_exact() -> None:
    result = grade_numeric({"value": 3.14}, {"value": 3.14, "tolerance": 0.01})
    assert result.is_correct is True
    assert result.score == 1.0


def test_numeric_within_tolerance() -> None:
    result = grade_numeric({"value": 3.145}, {"value": 3.14, "tolerance": 0.01})
    assert result.is_correct is True


def test_numeric_outside_tolerance() -> None:
    result = grade_numeric({"value": 3.2}, {"value": 3.14, "tolerance": 0.01})
    assert result.is_correct is False


def test_numeric_invalid_value() -> None:
    result = grade_numeric({"value": "abc"}, {"value": 3.14})
    assert result.is_correct is False
    assert result.score == 0.0


def test_numeric_missing_value() -> None:
    result = grade_numeric({}, {"value": 5.0})
    assert result.is_correct is False


# --- Short Answer ---

def test_short_answer_all_keywords() -> None:
    result = grade_short_answer(
        {"text": "Ankara başkenttir"},
        {"keywords": ["Ankara", "başkent"]},
    )
    assert result.is_correct is True
    assert result.score == 1.0


def test_short_answer_partial_keywords() -> None:
    result = grade_short_answer(
        {"text": "Ankara büyük bir şehir"},
        {"keywords": ["Ankara", "başkent"]},
    )
    assert result.score == 0.5
    assert result.is_correct is False


def test_short_answer_no_keywords() -> None:
    result = grade_short_answer(
        {"text": "İstanbul güzel"},
        {"keywords": ["Ankara", "başkent"]},
    )
    assert result.score == 0.0
    assert result.is_correct is False


def test_short_answer_empty_text() -> None:
    result = grade_short_answer({"text": ""}, {"keywords": ["test"]})
    assert result.score == 0.0
    assert result.is_correct is False


def test_short_answer_no_keywords_defined() -> None:
    result = grade_short_answer({"text": "some answer"}, {"keywords": []})
    assert result.grading_method == "fallback"
    assert result.confidence == 0.0


# --- Dispatcher ---

def test_can_grade_deterministically_mcq() -> None:
    assert can_grade_deterministically("mcq") is True


def test_can_grade_deterministically_long_form() -> None:
    assert can_grade_deterministically("long_form") is False


def test_grade_deterministic_dispatcher() -> None:
    result = grade_deterministic("mcq", {"key": "A"}, {"key": "A"})
    assert result.is_correct is True
    assert result.grading_method == "deterministic"
