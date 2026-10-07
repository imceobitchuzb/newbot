export interface QuestionOption {
  id: string;
  label: string; // 'A', 'B', 'C', 'D'
  text: string;
  order_index: number;
}

export interface Passage {
  id: string;
  title?: string | null;
  passage_text: string;
  source_info?: string | null;
}

export interface Question {
  id: string;
  subject: "MATH" | "READING_WRITING";
  domain: string;
  skill: string;
  subskill?: string | null;
  question_type: string;
  difficulty: "EASY" | "MEDIUM" | "HARD";
  question_text: string;
  options: QuestionOption[];
  passage?: Passage | null;
  estimated_time_seconds: number;
  desmos_allowed: boolean;
  desmos_recommended: boolean;
}

export interface AttemptSubmitRequest {
  selected_option_id: string;
  time_spent_seconds: number;
}

export interface AttemptResult {
  attempt_id: string;
  question_id: string;
  selected_option_id: string;
  is_correct: boolean;
  correct_option_id: string;
  explanation: string;
  hint?: string | null;
  sat_shortcut?: string | null;
  time_spent_seconds: number;
  answered_at: string;
}
