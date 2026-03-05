export enum UserRole {
  Student = "student",
  Instructor = "instructor",
  Admin = "admin",
}

export enum QuestionType {
  MCQ = "mcq",
  TrueFalse = "true_false",
  Numeric = "numeric",
  ShortAnswer = "short_answer",
  LongForm = "long_form",
}

export enum SessionStatus {
  Created = "created",
  InProgress = "in_progress",
  Submitted = "submitted",
  Graded = "graded",
  Expired = "expired",
}

export enum GradingMethod {
  Deterministic = "deterministic",
  LLM = "llm",
  Manual = "manual",
  Fallback = "fallback",
}

export enum ExamMode {
  Practice = "practice",
  Mock = "mock",
  HighStakes = "high_stakes",
}

export enum DocumentStatus {
  Pending = "pending",
  Processing = "processing",
  Ready = "ready",
  Failed = "failed",
}
