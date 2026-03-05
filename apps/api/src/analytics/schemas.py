import uuid
from datetime import datetime

from pydantic import BaseModel, Field

# --- Score Distribution ---


class ScoreBucket(BaseModel):
    range_start: float
    range_end: float
    count: int


class ScoreDistributionOut(BaseModel):
    template_id: uuid.UUID
    total_sessions: int
    graded_sessions: int
    mean_score: float | None
    median_score: float | None
    std_dev: float | None
    min_score: float | None
    max_score: float | None
    pass_rate: float | None
    distribution: list[ScoreBucket]


# --- Item Analysis ---


class ItemAnalysis(BaseModel):
    question_id: uuid.UUID
    stem_preview: str
    question_type: str
    topic: str | None
    response_count: int
    correct_count: int
    p_value: float  # proportion correct
    discrimination: float | None
    mean_score: float | None
    max_score: float | None


class ItemAnalysisOut(BaseModel):
    template_id: uuid.UUID
    total_items: int
    items: list[ItemAnalysis]


# --- Topic Mastery ---


class TopicMastery(BaseModel):
    topic: str
    question_count: int
    response_count: int
    correct_count: int
    mastery_rate: float  # proportion correct


class StudentMastery(BaseModel):
    user_id: uuid.UUID
    topics: list[TopicMastery]


class TopicMasteryOut(BaseModel):
    template_id: uuid.UUID
    mastery: list[StudentMastery] | list[TopicMastery]


# --- Performance Over Time ---


class PerformancePoint(BaseModel):
    date: str  # ISO date string
    session_count: int
    mean_percentage: float | None


class PerformanceOverTimeOut(BaseModel):
    template_id: uuid.UUID | None
    points: list[PerformancePoint]


# --- AI Cost ---


class AICostByTask(BaseModel):
    task_type: str
    call_count: int
    total_tokens: int
    total_cost_usd: float
    avg_latency_ms: float | None


class AICostByProvider(BaseModel):
    provider: str
    model: str
    call_count: int
    total_tokens: int
    total_cost_usd: float


class AICostOut(BaseModel):
    period_start: datetime | None
    period_end: datetime | None
    total_cost_usd: float
    total_calls: int
    by_task: list[AICostByTask]
    by_provider: list[AICostByProvider]


# --- Export ---


class ExportRequest(BaseModel):
    template_id: uuid.UUID
    format: str = Field(default="csv", pattern=r"^(csv|pdf)$")
    include_responses: bool = False
    include_grades: bool = True


class ExportOut(BaseModel):
    export_id: str
    status: str
    download_url: str | None = None


# --- Session Summary (for dashboard) ---


class SessionSummary(BaseModel):
    total_sessions: int
    in_progress: int
    submitted: int
    graded: int
    avg_percentage: float | None
    pass_rate: float | None


class DashboardOut(BaseModel):
    session_summary: SessionSummary
    recent_scores: list[PerformancePoint]
    top_difficult_items: list[ItemAnalysis]
    ai_cost_summary: AICostOut | None
