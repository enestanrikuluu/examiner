import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    template_id: uuid.UUID
    question_type: str = "mcq"
    topic: str
    subtopic: str | None = None
    count: int = Field(5, ge=1, le=50)
    difficulty: int | None = Field(None, ge=1, le=5)
    locale: str = "tr-TR"
    use_rag: bool = True


class GenerateTaskOut(BaseModel):
    task_id: str
    status: str  # "pending", "processing", "completed", "failed"


class GeneratedQuestion(BaseModel):
    stem: str
    question_type: str
    options: list[dict[str, str]] | None = None
    correct_answer: dict[str, Any]
    explanation: str | None = None
    topic: str | None = None
    subtopic: str | None = None
    difficulty: float | None = None
    warnings: list[str] = Field(default_factory=list)


class GenerateResultOut(BaseModel):
    task_id: str
    status: str
    questions: list[GeneratedQuestion] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    trace_id: uuid.UUID | None = None


class AcceptQuestionsRequest(BaseModel):
    question_indices: list[int] = Field(
        ..., min_length=1, description="Indices of questions to accept"
    )


class ModelTraceOut(BaseModel):
    id: uuid.UUID
    provider: str
    model: str
    task_type: str
    prompt_id: str | None
    input_tokens: int | None
    output_tokens: int | None
    latency_ms: int | None
    cost_usd: float | None
    status: str
    template_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ModelTraceListResponse(BaseModel):
    items: list[ModelTraceOut]
    total: int
    page: int
    page_size: int


class DocumentOut(BaseModel):
    id: uuid.UUID
    template_id: uuid.UUID
    filename: str
    content_type: str
    file_size_bytes: int
    status: str
    chunk_count: int
    error_message: str | None
    uploaded_by: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class PromptVersionOut(BaseModel):
    id: uuid.UUID
    prompt_id: str
    version: int
    description: str | None
    ai_model: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
