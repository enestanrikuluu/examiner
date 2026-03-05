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
  rubric_scores: Array<{
    criterion_id: string;
    score: number;
    max_score: number;
    feedback?: string;
  }> | null;
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

// ISG types

export interface ISGSubtopic {
  id: string;
  name: string;
}

export interface ISGTopic {
  id: string;
  name: string;
  subtopics: ISGSubtopic[];
}

export interface ISGTopicWeight {
  topic_id: string;
  topic_name: string;
  weight: number;
  question_count: number;
}

export interface ISGBlueprint {
  exam_class: string;
  title: string;
  description: string;
  total_questions: number;
  time_limit_minutes: number;
  pass_score: number;
  topic_weights: ISGTopicWeight[];
  allowed_question_types: string[];
}

export interface ISGRubricCriterion {
  id: string;
  description: string;
  max_points: number;
}

export interface ISGRubric {
  rubric_id: string;
  name: string;
  description: string;
  max_score: number;
  criteria: ISGRubricCriterion[];
}

export interface ISGExamResult {
  template_id: string;
  exam_class: string;
  title: string;
  total_questions: number;
  topic_distribution: ISGTopicWeight[];
}

export interface ISGGenerateTopicResult {
  topic_id: string;
  topic_name: string;
  requested_count: number;
  generated_count: number;
  errors: string[];
}

export interface ISGGenerateResult {
  template_id: string;
  total_generated: number;
  total_requested: number;
  topic_results: ISGGenerateTopicResult[];
  trace_ids: string[];
}

// Adaptive / IRT types

export interface AdaptiveSession {
  session_id: string;
  template_id: string;
  status: string;
  theta: number | null;
  se: number | null;
  items_administered: number;
  max_items: number;
}

export interface AdaptiveNextQuestion {
  question_id: string;
  stem: string;
  question_type: string;
  options: MCQOption[] | null;
  step: number;
  theta: number;
  se: number;
  is_finished: boolean;
  finish_reason: string | null;
}

export interface AdaptiveNoMore {
  is_finished: true;
  finish_reason: string;
  theta: number;
  se: number;
  items_administered: number;
}

export interface AdaptiveRespondResult {
  is_correct: boolean;
  theta: number;
  se: number;
  step: number;
  is_finished: boolean;
  finish_reason: string | null;
}

export interface ThetaHistoryEntry {
  step: number;
  question_id: string;
  theta: number;
  se: number;
  is_correct: boolean;
  information: number | null;
}

export interface ThetaResult {
  session_id: string;
  current_theta: number | null;
  current_se: number | null;
  history: ThetaHistoryEntry[];
}
