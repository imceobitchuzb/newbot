export type MistakeStatus = 'ACTIVE' | 'IN_REVIEW' | 'MASTERED' | 'DISMISSED';

export type MistakeType =
  | 'CONCEPT_GAP'
  | 'CARELESS_ERROR'
  | 'MISREAD'
  | 'CALCULATION_ERROR'
  | 'TIME_PRESSURE'
  | 'UNKNOWN';

export interface QuestionOptionPublic {
  id: string;
  label: string;
  text: string;
  order_index: number;
}

export interface MistakeEntryItem {
  id: string;
  user_id: string;
  question_id: string;
  attempt_id?: string | null;
  subject: string;
  domain: string;
  skill: string;
  status: MistakeStatus;
  mistake_type: MistakeType;
  review_count: number;
  correct_retry_count: number;
  incorrect_retry_count: number;
  last_reviewed_at?: string | null;
  next_review_at?: string | null;
  is_due: boolean;
  created_at: string;
  updated_at: string;
  question_text: string;
  difficulty: string;
  options: QuestionOptionPublic[];
  explanation?: string | null;
  hint?: string | null;
  sat_shortcut?: string | null;
  correct_option_id?: string | null;
  last_selected_option_id?: string | null;
}

export interface MistakeListResponse {
  items: MistakeEntryItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface MistakeAnalyticsResponse {
  total_mistakes: number;
  active_mistakes: number;
  in_review_mistakes: number;
  mastered_mistakes: number;
  due_reviews: number;
  mastery_rate: number;
  average_retries: number;
  by_subject: Record<string, number>;
  by_domain: Record<string, number>;
  by_skill: Record<string, number>;
  by_mistake_type: Record<string, number>;
}

export interface MistakeRetryRequest {
  selected_option_id: string;
  time_spent_seconds?: number;
}

export interface MistakeRetryResponse {
  is_correct: boolean;
  selected_option_id: string;
  correct_option_id: string;
  explanation: string;
  hint?: string | null;
  sat_shortcut?: string | null;
  new_status: MistakeStatus;
  correct_retry_count: number;
  incorrect_retry_count: number;
  is_mastered: boolean;
}

export interface MistakeReviewRequest {
  mistake_type?: MistakeType;
}

export interface MistakeClassifyRequest {
  mistake_type: MistakeType;
}
