import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    template_id: uuid.UUID


class SessionOut(BaseModel):
    id: uuid.UUID
    template_id: uuid.UUID
    user_id: uuid.UUID
    status: str
    question_order: list[str] | None
    started_at: datetime | None
    submitted_at: datetime | None
    expires_at: datetime | None
    total_score: float | None
    max_score: float | None
    percentage: float | None
    passed: bool | None
    theta: float | None
    session_metadata: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SessionListResponse(BaseModel):
    items: list[SessionOut]
    total: int
    page: int
    page_size: int


class ResponseSubmit(BaseModel):
    question_id: uuid.UUID
    answer: dict[str, Any]
    time_spent_seconds: int | None = Field(None, ge=0)
    is_flagged: bool = False


class BatchResponseSubmit(BaseModel):
    responses: list[ResponseSubmit] = Field(..., min_length=1, max_length=200)


class ResponseOut(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    question_id: uuid.UUID
    answer: dict[str, Any]
    answered_at: datetime
    time_spent_seconds: int | None
    is_flagged: bool

    model_config = {"from_attributes": True}


class GradeOut(BaseModel):
    id: uuid.UUID
    response_id: uuid.UUID
    grading_method: str
    score: float
    max_score: float
    is_correct: bool | None
    feedback: str | None
    confidence: float | None
    rubric_scores: dict[str, Any] | None
    graded_at: datetime
    graded_by: uuid.UUID | None

    model_config = {"from_attributes": True}


class SessionResultOut(BaseModel):
    session: SessionOut
    responses: list[ResponseOut]
    grades: list[GradeOut]


class IntegrityEvent(BaseModel):
    event_type: str = Field(
        ..., description="tab_switch, copy, paste, fullscreen_exit, focus_loss"
    )
    details: dict[str, Any] | None = None


class IntegrityBatch(BaseModel):
    events: list[IntegrityEvent] = Field(..., min_length=1, max_length=100)


class HeartbeatOut(BaseModel):
    status: str
    server_time: datetime
    expires_at: datetime | None
    remaining_seconds: int | None


class FeatureFlagsOut(BaseModel):
    proctoring_enabled: bool
    tab_switch_detection: bool
    copy_paste_block: bool
    fullscreen_required: bool


class ResumeOut(BaseModel):
    session: SessionOut
    responses: list[ResponseOut]
