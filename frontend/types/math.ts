export type MathDomainKey =
  | "ALGEBRA"
  | "ADVANCED_MATH"
  | "PROBLEM_SOLVING_DATA_ANALYSIS"
  | "GEOMETRY_TRIGONOMETRY";

export type SkillMastery = "NOT_STARTED" | "LEARNING" | "PRACTICING" | "STRONG";

export interface MathQuestionOption {
  id: string;
  label: string;
  text: string;
  order_index: number;
}

export interface MathPracticeQuestionItem {
  practice_question_id: string;
  question_id: string;
  order_index: number;
  is_answered: boolean;
  selected_option_id: string | null;
  is_correct: boolean | null;
  time_spent_seconds: number;
  domain: string;
  skill: string;
  difficulty: string;
  question_text: string;
  options: MathQuestionOption[];
  desmos_allowed: boolean;
  desmos_recommended: boolean;
  explanation?: string | null;
  hint?: string | null;
  sat_shortcut?: string | null;
  correct_option_id?: string | null;
}

export interface MathPracticeSessionResponse {
  id: string;
  status: "IN_PROGRESS" | "COMPLETED" | "ABANDONED";
  domain: string | null;
  difficulty: string | null;
  skill: string | null;
  total_questions: number;
  current_question_index: number;
  answered_count: number;
  correct_count: number;
  started_at: string;
  completed_at?: string | null;
  current_question: MathPracticeQuestionItem | null;
  questions: MathPracticeQuestionItem[];
}

export interface MathPracticeStartRequest {
  domain?: string | null;
  difficulty?: string | null;
  skill?: string | null;
  question_count?: number;
}

export interface MathPracticeAnswerRequest {
  selected_option_id: string;
  time_spent_seconds: number;
}

export interface MathPracticeAnswerResponse {
  is_correct: boolean;
  selected_option_id: string;
  correct_option_id: string;
  explanation: string;
  hint?: string | null;
  sat_shortcut?: string | null;
  session_completed: boolean;
  next_question_index: number;
}

export interface MathPracticeResultResponse {
  session_id: string;
  domain: string | null;
  difficulty: string | null;
  skill: string | null;
  total_questions: number;
  answered_questions: number;
  correct_count: number;
  accuracy_percentage: number;
  total_time_seconds: number;
  status: string;
  started_at: string;
  completed_at?: string | null;
  domain_breakdown: Record<string, { total: number; correct: number; accuracy: number }>;
  questions: MathPracticeQuestionItem[];
}

export interface SkillAnalyticsOut {
  skill: string;
  attempts: number;
  correct: number;
  accuracy: number;
  mastery_level: SkillMastery;
}

export interface DomainAnalyticsOut {
  domain: string;
  title: string;
  description: string;
  total_attempts: number;
  correct_attempts: number;
  accuracy: number;
  mastery_level: SkillMastery;
  skills: SkillAnalyticsOut[];
}

export interface MathAnalyticsResponse {
  total_attempts: number;
  correct_attempts: number;
  overall_accuracy: number;
  estimated_score_range: string | null;
  domains: DomainAnalyticsOut[];
  recommended_focus_skill: string | null;
  recommended_focus_domain: string | null;
}
