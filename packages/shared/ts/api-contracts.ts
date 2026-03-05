export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
  locale?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface CreateTemplateRequest {
  title: string;
  description?: string;
  locale?: string;
  time_limit_minutes?: number;
  pass_score?: number;
  shuffle_questions?: boolean;
  shuffle_options?: boolean;
}

export interface GenerateQuestionsRequest {
  template_id: string;
  topic: string;
  subtopic?: string;
  question_type: string;
  count: number;
  difficulty_min?: number;
  difficulty_max?: number;
  locale?: string;
}

export interface SubmitResponseRequest {
  question_id: string;
  answer: Record<string, unknown>;
}
