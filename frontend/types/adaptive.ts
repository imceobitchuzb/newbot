import { Question } from "./question";

export type QuestionPublic = Question;

export type AdaptiveSkillStatus =
  | "NOT_STARTED"
  | "LEARNING"
  | "PRACTICING"
  | "STRONG"
  | "MASTERED";

export type RecommendationType =
  | "MISTAKE_REVIEW"
  | "WEAK_SKILL"
  | "NEW_SKILL"
  | "DIFFICULTY_UP"
  | "DIFFICULTY_DOWN"
  | "MAINTENANCE";

export interface SkillMasteryItem {
  skill: string;
  domain: string;
  status: AdaptiveSkillStatus;
  mastery_score: number;
  confidence_score: number;
  attempts: number;
  accuracy: number;
  recent_accuracy: number;
  easy_accuracy: number;
  medium_accuracy: number;
  hard_accuracy: number;
  has_active_mistake: boolean;
}

export interface AdaptiveAnalyticsResponse {
  overall_mastery: number;
  mastered_skills_count: number;
  learning_skills_count: number;
  practicing_skills_count: number;
  strong_skills_count: number;
  recommended_skill: string;
  recommended_domain: string;
  current_difficulty: string;
  confidence: number;
  recent_accuracy: number;
  skills: SkillMasteryItem[];
}

export interface AdaptiveNextQuestionResponse {
  question: QuestionPublic;
  recommendation_type: RecommendationType;
  domain: string;
  skill: string;
  difficulty: string;
  reason: string;
}

export interface AdaptiveSessionStartRequest {
  total_questions?: number;
  subject?: string;
}

export interface AdaptiveQuestionItem {
  id: string;
  session_id: string;
  question_id: string;
  order_index: number;
  difficulty_at_assignment: string;
  recommendation_type: RecommendationType;
  reason?: string | null;
  is_answered: boolean;
  question: QuestionPublic;
}

export interface AdaptiveSessionSummary {
  total_completed: number;
  total_correct: number;
  accuracy: number;
  skills_practiced: string[];
  difficulty_progression: string[];
  next_recommended_skill: string;
  next_recommended_difficulty: string;
}

export interface AdaptiveSessionResponse {
  id: string;
  user_id: string;
  subject: string;
  current_question_index: number;
  total_questions: number;
  current_difficulty: string;
  status: string;
  current_question?: AdaptiveQuestionItem | null;
  started_at: string;
  completed_at?: string | null;
}

export interface AdaptiveAnswerRequest {
  selected_option_id: string;
  time_spent_seconds?: number;
}

export interface AdaptiveAnswerResponse {
  is_correct: boolean;
  selected_option_id: string;
  correct_option_id: string;
  explanation: string;
  hint?: string | null;
  sat_shortcut?: string | null;
  session_completed: boolean;
  next_difficulty: string;
  next_question?: AdaptiveQuestionItem | null;
  session_summary?: AdaptiveSessionSummary | null;
}
