import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

# --- Adaptive Session ---


class AdaptiveSessionCreate(BaseModel):
    template_id: uuid.UUID


class AdaptiveSessionOut(BaseModel):
    session_id: uuid.UUID
    template_id: uuid.UUID
    status: str
    theta: float | None
    se: float | None
    items_administered: int
    max_items: int

    model_config = {"from_attributes": True}


# --- Next Question ---


class NextQuestionOut(BaseModel):
    question_id: uuid.UUID
    stem: str
    question_type: str
    options: list[dict[str, Any]] | None
    step: int
    theta: float
    se: float
    is_finished: bool = False
    finish_reason: str | None = None


class NoMoreQuestions(BaseModel):
    is_finished: bool = True
    finish_reason: str
    theta: float
    se: float
    items_administered: int


# --- Respond ---


class AdaptiveRespond(BaseModel):
    question_id: uuid.UUID
    answer: dict[str, Any]
    time_spent_seconds: int | None = Field(None, ge=0)


class AdaptiveRespondOut(BaseModel):
    is_correct: bool
    theta: float
    se: float
    step: int
    is_finished: bool = False
    finish_reason: str | None = None


# --- Theta ---


class ThetaHistoryEntry(BaseModel):
    step: int
    question_id: uuid.UUID
    theta: float
    se: float
    is_correct: bool
    information: float | None

    model_config = {"from_attributes": True}


class ThetaOut(BaseModel):
    session_id: uuid.UUID
    current_theta: float | None
    current_se: float | None
    history: list[ThetaHistoryEntry]


# --- Item Parameters ---


class ItemParameterOut(BaseModel):
    id: uuid.UUID
    question_id: uuid.UUID
    a: float
    b: float
    se_a: float | None
    se_b: float | None
    response_count: int
    calibration_method: str | None
    calibrated_at: datetime | None

    model_config = {"from_attributes": True}


# --- Calibration ---


class CalibrationRequest(BaseModel):
    template_id: uuid.UUID | None = None
    min_responses: int = Field(default=30, ge=5)


class CalibrationResultOut(BaseModel):
    items_calibrated: int
    items_skipped: int
    errors: list[str]
