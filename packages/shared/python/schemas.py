from pydantic import BaseModel


class MCQOption(BaseModel):
    key: str
    text: str


class MCQCorrectAnswer(BaseModel):
    key: str


class NumericCorrectAnswer(BaseModel):
    value: float
    tolerance: float = 0.01


class ShortAnswerCorrectAnswer(BaseModel):
    keywords: list[str]
    accept_semantic: bool = True


class RubricCriterion(BaseModel):
    id: str
    description: str
    max_points: float


class GradingRubric(BaseModel):
    max_score: float
    criteria: list[RubricCriterion]
