export interface DesmosOption {
  id: string;
  label: string;
  text: string;
}

export interface DesmosTechnique {
  id: string;
  slug: string;
  title: string;
  description: string;
  technique_type: string;
  subject: string;
  difficulty: "EASY" | "MEDIUM" | "HARD";
  when_to_use: string;
  when_not_to_use: string;
  sat_tip: string;
  question_count: number;
  practiced_count: number;
  accuracy_percent: number;
}

export interface ExampleQuestion {
  id: string;
  domain: string;
  skill: string;
  difficulty: string;
  question_text: string;
  explanation: string;
  sat_shortcut?: string | null;
  options: DesmosOption[];
}

export interface DesmosTechniqueDetail {
  id: string;
  slug: string;
  title: string;
  description: string;
  technique_type: string;
  subject: string;
  difficulty: "EASY" | "MEDIUM" | "HARD";
  when_to_use: string;
  when_not_to_use: string;
  steps: string[];
  common_mistakes: string[];
  sat_tip: string;
  example_question?: ExampleQuestion | null;
  question_count: number;
}

export interface DesmosQuestionItem {
  id: string;
  question_id: string;
  order_index: number;
  domain: string;
  skill: string;
  difficulty: string;
  question_text: string;
  estimated_time_seconds: number;
  desmos_allowed: boolean;
  desmos_recommended: boolean;
  technique_type?: string | null;
  technique_title?: string | null;
  technique_slug?: string | null;
  recommendation_status: "RECOMMENDED" | "ALLOWED" | "FORBIDDEN";
  recommendation_reason: string;
  options: DesmosOption[];
  is_answered: boolean;
  is_correct?: boolean | null;
  selected_option_id?: string | null;
  time_spent_seconds?: number | null;
  desmos_used: boolean;
}

export interface DesmosSession {
  id: string;
  status: "IN_PROGRESS" | "COMPLETED" | "ABANDONED";
  technique_slug?: string | null;
  technique_title?: string | null;
  difficulty?: string | null;
  target_count: number;
  completed_count: number;
  correct_count: number;
  accuracy_percent: number;
  current_question?: DesmosQuestionItem | null;
  questions: DesmosQuestionItem[];
  started_at: string;
  completed_at?: string | null;
}

export interface DesmosAnswerResponse {
  is_correct: boolean;
  correct_option_id: string;
  explanation: string;
  hint?: string | null;
  sat_shortcut?: string | null;
  desmos_guidance?: string | null;
  session_completed: boolean;
  session_accuracy: number;
  next_question_id?: string | null;
}

export interface TechniqueAnalyticsItem {
  technique_type: string;
  technique_slug: string;
  technique_title: string;
  practiced_count: number;
  correct_count: number;
  accuracy_percent: number;
  avg_time_seconds: number;
}

export interface DesmosAnalytics {
  total_questions_attempted: number;
  total_correct: number;
  overall_accuracy: number;
  avg_time_seconds: number;
  recommended_count: number;
  allowed_count: number;
  techniques: TechniqueAnalyticsItem[];
}
