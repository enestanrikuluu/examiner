"""Pydantic schemas for the ISG module API."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Blueprint output schemas
# ---------------------------------------------------------------------------

class SubtopicOut(BaseModel):
    id: str
    name: str


class TopicOut(BaseModel):
    id: str
    name: str
    subtopics: list[SubtopicOut]


class TopicWeightOut(BaseModel):
    topic_id: str
    topic_name: str
    weight: float
    question_count: int


class BlueprintOut(BaseModel):
    exam_class: str
    title: str
    description: str
    total_questions: int
    time_limit_minutes: int
    pass_score: float
    topic_weights: list[TopicWeightOut]
    allowed_question_types: list[str]


class BlueprintListOut(BaseModel):
    blueprints: list[BlueprintOut]


# ---------------------------------------------------------------------------
# Rubric output schemas
# ---------------------------------------------------------------------------

class RubricCriterionOut(BaseModel):
    id: str
    description: str
    max_points: float


class RubricOut(BaseModel):
    rubric_id: str
    name: str
    description: str
    max_score: float
    criteria: list[RubricCriterionOut]


class RubricListOut(BaseModel):
    rubrics: list[RubricOut]


# ---------------------------------------------------------------------------
# ISG exam creation
# ---------------------------------------------------------------------------

class TopicOverride(BaseModel):
    """Optional per-topic overrides for question count."""
    topic_id: str
    question_count: int = Field(..., ge=0, le=100)


class ISGExamCreate(BaseModel):
    """Request body to create an ISG exam from a blueprint."""
    exam_class: str = Field(..., pattern=r"^[ABCabc]$")
    title: str | None = None
    description: str | None = None
    org_id: uuid.UUID | None = None
    time_limit_minutes: int | None = Field(None, ge=1, le=600)
    pass_score: float | None = Field(None, ge=0, le=100)
    shuffle_questions: bool = True
    shuffle_options: bool = True
    topic_overrides: list[TopicOverride] | None = None


class ISGExamOut(BaseModel):
    template_id: uuid.UUID
    exam_class: str
    title: str
    total_questions: int
    topic_distribution: list[TopicWeightOut]

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# ISG question generation
# ---------------------------------------------------------------------------

class ISGGenerateRequest(BaseModel):
    """Request to generate all questions for an ISG exam template."""
    template_id: uuid.UUID
    question_types: list[str] = Field(
        default_factory=lambda: ["mcq"],
        description="Question types to generate (mcq, true_false, short_answer, long_form)",
    )
    difficulty: int | None = Field(None, ge=1, le=5)
    use_rag: bool = True
    rubric_id: str | None = Field(
        None,
        description="Default rubric ID to apply to long_form questions",
    )


class ISGGenerateTopicResult(BaseModel):
    topic_id: str
    topic_name: str
    requested_count: int
    generated_count: int
    errors: list[str] = Field(default_factory=list)


class ISGGenerateResultOut(BaseModel):
    template_id: uuid.UUID
    total_generated: int
    total_requested: int
    topic_results: list[ISGGenerateTopicResult]
    trace_ids: list[uuid.UUID]


class ISGGenerateTaskOut(BaseModel):
    """Returned immediately when generation is dispatched to background."""
    task_id: str
    template_id: uuid.UUID
    total_topics: int
    total_requested: int


class ISGTaskProgressTopic(BaseModel):
    topic_id: str
    topic_name: str
    requested_count: int
    generated_count: int
    status: str = "pending"  # pending, generating, done, error
    errors: list[str] = Field(default_factory=list)


class ISGTaskStatusOut(BaseModel):
    task_id: str
    status: str  # pending, started, generating, completed, failed
    template_id: uuid.UUID | None = None
    total_generated: int = 0
    total_requested: int = 0
    topic_progress: list[ISGTaskProgressTopic] = Field(default_factory=list)
    current_topic: str | None = None
    error: str | None = None


# ---------------------------------------------------------------------------
# Topics listing
# ---------------------------------------------------------------------------

class TopicListOut(BaseModel):
    topics: list[TopicOut]
