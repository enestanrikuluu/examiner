from enum import StrEnum


class UserRole(StrEnum):
    STUDENT = "student"
    INSTRUCTOR = "instructor"
    ADMIN = "admin"


class QuestionType(StrEnum):
    MCQ = "mcq"
    TRUE_FALSE = "true_false"
    NUMERIC = "numeric"
    SHORT_ANSWER = "short_answer"
    LONG_FORM = "long_form"


class SessionStatus(StrEnum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    GRADED = "graded"
    EXPIRED = "expired"


class GradingMethod(StrEnum):
    DETERMINISTIC = "deterministic"
    LLM = "llm"
    MANUAL = "manual"
    FALLBACK = "fallback"


class ExamMode(StrEnum):
    PRACTICE = "practice"
    MOCK = "mock"
    HIGH_STAKES = "high_stakes"


class DocumentStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class GradeStatus(StrEnum):
    PENDING = "pending"
    GRADED = "graded"
    FLAGGED = "flagged"
    MANUAL_REVIEW = "manual_review"
