"""Validates that AI-generated questions conform to expected JSON schemas."""

from __future__ import annotations

from typing import Any

from src.questions.schemas import QuestionItemCreate


class SchemaValidationError(Exception):
    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__(f"Schema validation failed: {'; '.join(errors)}")


def validate_generated_questions(
    raw_questions: list[dict[str, Any]],
    expected_type: str | None = None,
) -> tuple[list[QuestionItemCreate], list[str]]:
    """Validate a list of raw question dicts.

    Returns:
        Tuple of (valid questions, list of error messages for invalid ones)
    """
    valid: list[QuestionItemCreate] = []
    errors: list[str] = []

    for i, q_data in enumerate(raw_questions):
        try:
            if expected_type and q_data.get("question_type") != expected_type:
                q_data["question_type"] = expected_type

            if "question_type" not in q_data:
                errors.append(f"Question {i + 1}: missing question_type")
                continue

            question = QuestionItemCreate(**q_data)
            valid.append(question)
        except Exception as e:
            errors.append(f"Question {i + 1}: {e}")

    return valid, errors
