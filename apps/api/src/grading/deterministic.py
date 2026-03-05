"""Deterministic graders for objective question types (MCQ, T/F, numeric, short_answer)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class GradeResult:
    """Result from a grading operation."""

    score: float
    max_score: float
    is_correct: bool | None
    feedback: str | None = None
    confidence: float = 1.0
    grading_method: str = "deterministic"


def grade_mcq(
    answer: dict[str, Any],
    correct_answer: dict[str, Any],
    max_score: float = 1.0,
) -> GradeResult:
    """Grade a multiple-choice question by exact key match."""
    student_key = str(answer.get("key", "")).strip().upper()
    correct_key = str(correct_answer.get("key", "")).strip().upper()

    is_correct = student_key == correct_key
    return GradeResult(
        score=max_score if is_correct else 0.0,
        max_score=max_score,
        is_correct=is_correct,
        feedback=None if is_correct else f"Doğru cevap: {correct_key}",
    )


def grade_true_false(
    answer: dict[str, Any],
    correct_answer: dict[str, Any],
    max_score: float = 1.0,
) -> GradeResult:
    """Grade a true/false question by boolean match."""
    student_value = answer.get("value")
    correct_value = correct_answer.get("value")

    # Normalize to bool
    if isinstance(student_value, str):
        student_value = student_value.lower() in ("true", "1", "doğru", "evet")
    if isinstance(correct_value, str):
        correct_value = correct_value.lower() in ("true", "1", "doğru", "evet")

    is_correct = bool(student_value) == bool(correct_value)
    return GradeResult(
        score=max_score if is_correct else 0.0,
        max_score=max_score,
        is_correct=is_correct,
        feedback=None if is_correct else f"Doğru cevap: {'Doğru' if correct_value else 'Yanlış'}",
    )


def grade_numeric(
    answer: dict[str, Any],
    correct_answer: dict[str, Any],
    max_score: float = 1.0,
) -> GradeResult:
    """Grade a numeric question within tolerance."""
    try:
        student_value = float(answer.get("value", 0))
    except (TypeError, ValueError):
        return GradeResult(
            score=0.0,
            max_score=max_score,
            is_correct=False,
            feedback="Geçersiz sayısal değer.",
        )

    correct_value = float(correct_answer.get("value", 0))
    tolerance = float(correct_answer.get("tolerance", 0.01))

    is_correct = abs(student_value - correct_value) <= tolerance
    return GradeResult(
        score=max_score if is_correct else 0.0,
        max_score=max_score,
        is_correct=is_correct,
        feedback=None if is_correct else f"Doğru cevap: {correct_value} (±{tolerance})",
    )


def grade_short_answer(
    answer: dict[str, Any],
    correct_answer: dict[str, Any],
    max_score: float = 1.0,
) -> GradeResult:
    """Grade a short answer question by keyword matching.

    Scores proportionally based on how many required keywords are present.
    """
    student_text = str(answer.get("text", "")).strip().lower()
    keywords = correct_answer.get("keywords", [])

    if not student_text:
        return GradeResult(
            score=0.0,
            max_score=max_score,
            is_correct=False,
            feedback="Cevap boş bırakıldı.",
        )

    if not keywords:
        # No keywords defined; can't grade deterministically
        return GradeResult(
            score=0.0,
            max_score=max_score,
            is_correct=None,
            feedback="Anahtar kelime tanımlanmamış, manuel değerlendirme gerekli.",
            confidence=0.0,
            grading_method="fallback",
        )

    matched = sum(1 for kw in keywords if kw.lower() in student_text)
    ratio = matched / len(keywords)

    # Full credit if all keywords present, partial otherwise
    score = round(max_score * ratio, 2)
    is_correct = ratio >= 1.0

    missing = [kw for kw in keywords if kw.lower() not in student_text]
    feedback = None
    if missing:
        feedback = f"Eksik anahtar kelimeler: {', '.join(missing)}"

    return GradeResult(
        score=score,
        max_score=max_score,
        is_correct=is_correct,
        feedback=feedback,
        confidence=0.8 if ratio > 0 else 1.0,
    )


# Dispatcher

DETERMINISTIC_GRADERS = {
    "mcq": grade_mcq,
    "true_false": grade_true_false,
    "numeric": grade_numeric,
    "short_answer": grade_short_answer,
}


def can_grade_deterministically(question_type: str) -> bool:
    """Check if a question type has a deterministic grader."""
    return question_type in DETERMINISTIC_GRADERS


def grade_deterministic(
    question_type: str,
    answer: dict[str, Any],
    correct_answer: dict[str, Any],
    max_score: float = 1.0,
) -> GradeResult:
    """Grade a question using the appropriate deterministic grader."""
    grader = DETERMINISTIC_GRADERS.get(question_type)
    if grader is None:
        raise ValueError(f"No deterministic grader for question_type: {question_type}")
    return grader(answer, correct_answer, max_score)
