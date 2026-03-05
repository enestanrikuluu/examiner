
from pydantic import BaseModel, Field


class GradeUpdate(BaseModel):
    score: float | None = Field(None, ge=0)
    max_score: float | None = Field(None, gt=0)
    is_correct: bool | None = None
    feedback: str | None = None


class GradeOverride(BaseModel):
    score: float = Field(..., ge=0)
    feedback: str | None = None
