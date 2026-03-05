export enum UserRole {
  Student = "student",
  Instructor = "instructor",
  Admin = "admin",
}

export enum QuestionType {
  MultipleChoice = "mcq",
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

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  locale: string;
  is_active: boolean;
  created_at: string;
}

export interface HealthCheck {
  status: string;
  db: boolean;
  redis: boolean;
  storage: boolean;
}
