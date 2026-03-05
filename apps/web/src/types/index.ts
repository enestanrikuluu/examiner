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

export interface ExamTemplate {
  id: string;
  org_id: string | null;
  title: string;
  description: string | null;
  locale: string;
  time_limit_minutes: number | null;
  pass_score: number | null;
  question_count: number | null;
  shuffle_questions: boolean;
  shuffle_options: boolean;
  exam_mode: string;
  settings: Record<string, unknown> | null;
  is_published: boolean;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface ExamTemplateListResponse {
  items: ExamTemplate[];
  total: number;
  page: number;
  page_size: number;
}

export interface MCQOption {
  key: string;
  text: string;
}

export interface QuestionItem {
  id: string;
  template_id: string;
  question_type: string;
  stem: string;
  options: MCQOption[] | null;
  correct_answer: Record<string, unknown>;
  rubric: Record<string, unknown> | null;
  explanation: string | null;
  difficulty: number | null;
  discrimination: number | null;
  topic: string | null;
  subtopic: string | null;
  tags: string[] | null;
  sort_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface QuestionItemListResponse {
  items: QuestionItem[];
  total: number;
}

export interface ExamSession {
  id: string;
  template_id: string;
  user_id: string;
  status: string;
  question_order: string[] | null;
  started_at: string | null;
  submitted_at: string | null;
  expires_at: string | null;
  total_score: number | null;
  max_score: number | null;
  percentage: number | null;
  passed: boolean | null;
  created_at: string;
  updated_at: string;
}

export interface SessionListResponse {
  items: ExamSession[];
  total: number;
  page: number;
  page_size: number;
}

export interface SessionResponse {
  id: string;
  session_id: string;
  question_id: string;
  answer: Record<string, unknown>;
  answered_at: string;
  time_spent_seconds: number | null;
  is_flagged: boolean;
}

export interface Grade {
  id: string;
  response_id: string;
  grading_method: string;
  score: number;
  max_score: number;
  is_correct: boolean | null;
  feedback: string | null;
  confidence: number | null;
  graded_at: string;
}

export interface SessionResult {
  session: ExamSession;
  responses: SessionResponse[];
  grades: Grade[];
}

// AI / Document types

export interface DocumentInfo {
  id: string;
  template_id: string;
  filename: string;
  content_type: string;
  file_size_bytes: number;
  status: string;
  chunk_count: number;
  error_message: string | null;
  uploaded_by: string;
  created_at: string;
}

export interface GeneratedQuestion {
  stem: string;
  question_type: string;
  options: MCQOption[] | null;
  correct_answer: Record<string, unknown>;
  explanation: string | null;
  topic: string | null;
  subtopic: string | null;
  difficulty: number | null;
  warnings: string[];
}

export interface GenerateResult {
  task_id: string;
  status: string;
  questions: GeneratedQuestion[];
  errors: string[];
  trace_id: string | null;
}

export interface GenerateRequest {
  template_id: string;
  question_type: string;
  topic: string;
  subtopic?: string;
  count: number;
  difficulty?: number;
  locale: string;
  use_rag: boolean;
}
