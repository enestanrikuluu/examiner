import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator

# --- Type-specific answer schemas ---

class MCQAnswerPayload(BaseModel):
    key: str = Field(..., min_length=1)


class TrueFalseAnswerPayload(BaseModel):
    value: bool


class NumericAnswerPayload(BaseModel):
    value: float
    tolerance: float = Field(0.01, ge=0)


class ShortAnswerPayload(BaseModel):
    keywords: list[str] = Field(..., min_length=1)
    accept_semantic: bool = True


# --- MCQ option schema ---

class MCQOptionSchema(BaseModel):
    key: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)


# --- Rubric schemas ---

class RubricCriterionSchema(BaseModel):
    id: str
    description: str
    max_points: float = Field(..., gt=0)


class RubricSchema(BaseModel):
    max_score: float = Field(..., gt=0)
    criteria: list[RubricCriterionSchema] = Field(..., min_length=1)


# --- Question create/update ---

class QuestionItemCreate(BaseModel):
    question_type: str
    stem: str = Field(..., min_length=1)
    options: list[MCQOptionSchema] | None = None
    correct_answer: dict[str, Any]
    rubric: dict[str, Any] | None = None
    explanation: str | None = None
    difficulty: float | None = Field(None, ge=-5, le=5)
    discrimination: float | None = Field(None, ge=0, le=5)
    topic: str | None = Field(None, max_length=255)
    subtopic: str | None = Field(None, max_length=255)
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None
    sort_order: int = 0

    @model_validator(mode="after")
    def validate_by_type(self) -> "QuestionItemCreate":
        qt = self.question_type

        if qt == "mcq":
            if not self.options or len(self.options) < 4:
                raise ValueError("MCQ questions must have at least 4 options")
            MCQAnswerPayload(**self.correct_answer)
            answer_key = self.correct_answer.get("key", "")
            option_keys = {o.key for o in self.options}
            if answer_key not in option_keys:
                raise ValueError(
                    f"correct_answer key '{answer_key}' not found in options"
                )

        elif qt == "true_false":
            if self.options is not None:
                raise ValueError("true_false questions must not have options")
            TrueFalseAnswerPayload(**self.correct_answer)

        elif qt == "numeric":
            if self.options is not None:
                raise ValueError("numeric questions must not have options")
            NumericAnswerPayload(**self.correct_answer)

        elif qt == "short_answer":
            if self.options is not None:
                raise ValueError("short_answer questions must not have options")
            ShortAnswerPayload(**self.correct_answer)

        elif qt == "long_form":
            if self.options is not None:
                raise ValueError("long_form questions must not have options")
            if self.rubric is None:
                raise ValueError("long_form questions must have a rubric")
            RubricSchema(**self.rubric)

        else:
            raise ValueError(f"Unknown question_type: {qt}")

        return self


class QuestionItemUpdate(BaseModel):
    stem: str | None = Field(None, min_length=1)
    options: list[MCQOptionSchema] | None = None
    correct_answer: dict[str, Any] | None = None
    rubric: dict[str, Any] | None = None
    explanation: str | None = None
    difficulty: float | None = Field(None, ge=-5, le=5)
    discrimination: float | None = Field(None, ge=0, le=5)
    topic: str | None = Field(None, max_length=255)
    subtopic: str | None = Field(None, max_length=255)
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class QuestionItemOut(BaseModel):
    id: uuid.UUID
    template_id: uuid.UUID
    question_type: str
    stem: str
    options: list[dict[str, Any]] | None
    correct_answer: dict[str, Any]
    rubric: dict[str, Any] | None
    explanation: str | None
    difficulty: float | None
    discrimination: float | None
    topic: str | None
    subtopic: str | None
    tags: list[str] | None
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class QuestionItemListResponse(BaseModel):
    items: list[QuestionItemOut]
    total: int


class BulkQuestionImport(BaseModel):
    questions: list[QuestionItemCreate] = Field(..., min_length=1, max_length=200)
