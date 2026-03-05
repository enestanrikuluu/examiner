import { UserRole, QuestionType, SessionStatus, GradingMethod } from "./enums";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  locale: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  settings: Record<string, unknown>;
  created_at: string;
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
  is_published: boolean;
  created_by: string;
  created_at: string;
}

export interface MCQOption {
  key: string;
  text: string;
}

export interface QuestionItem {
  id: string;
  template_id: string;
  question_type: QuestionType;
  stem: string;
  options: MCQOption[] | null;
  difficulty: number | null;
  topic: string | null;
  subtopic: string | null;
  sort_order: number;
  is_active: boolean;
}

export interface ExamSession {
  id: string;
  template_id: string;
  user_id: string;
  status: SessionStatus;
  started_at: string | null;
  submitted_at: string | null;
  expires_at: string | null;
  total_score: number | null;
  max_score: number | null;
  percentage: number | null;
  passed: boolean | null;
}

export interface Grade {
  id: string;
  response_id: string;
  grading_method: GradingMethod;
  score: number;
  max_score: number;
  is_correct: boolean | null;
  feedback: string | null;
  confidence: number | null;
}

export interface HealthCheck {
  status: string;
  db: boolean;
  redis: boolean;
  storage: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
