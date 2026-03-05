import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ExamTemplateCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    org_id: uuid.UUID | None = None
    locale: str = "tr-TR"
    time_limit_minutes: int | None = Field(None, ge=1, le=600)
    pass_score: float | None = Field(None, ge=0, le=100)
    question_count: int | None = Field(None, ge=1, le=500)
    shuffle_questions: bool = False
    shuffle_options: bool = False
    exam_mode: str = "mock"
    settings: dict[str, Any] | None = None


class ExamTemplateUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    locale: str | None = None
    time_limit_minutes: int | None = Field(None, ge=1, le=600)
    pass_score: float | None = Field(None, ge=0, le=100)
    question_count: int | None = Field(None, ge=1, le=500)
    shuffle_questions: bool | None = None
    shuffle_options: bool | None = None
    exam_mode: str | None = None
    settings: dict[str, Any] | None = None
    is_published: bool | None = None


class ExamTemplateOut(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID | None
    title: str
    description: str | None
    locale: str
    time_limit_minutes: int | None
    pass_score: float | None
    question_count: int | None
    shuffle_questions: bool
    shuffle_options: bool
    exam_mode: str
    settings: dict[str, Any] | None
    is_published: bool
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExamTemplateListResponse(BaseModel):
    items: list[ExamTemplateOut]
    total: int
    page: int
    page_size: int
