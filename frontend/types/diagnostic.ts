import { Question } from "./question";

export interface DiagnosticSession {
  id: string;
  status: "NOT_STARTED" | "IN_PROGRESS" | "COMPLETED" | "ABANDONED";
  current_module: "MATH" | "READING_WRITING";
  current_question_index: number;
  started_at: string;
  total_questions: number;
}

export interface CurrentDiagnosticState {
  id: string;
  status: "IN_PROGRESS" | "COMPLETED" | "NOT_STARTED";
  subject: "MATH" | "READING_WRITING";
  module_number: number;
  current_question_index: number;
  answered_in_module: number;
  total_in_module: number;
  total_answered: number;
  total_questions: number;
  progress_percent: number;
  current_question: Question | null;
}

export interface DiagnosticAnswerRequest {
  selected_option_id: string;
  time_spent_seconds: number;
}

export interface DiagnosticAnswerResponse {
  module_completed: boolean;
  diagnostic_completed: boolean;
  current_module: "MATH" | "READING_WRITING";

  current_question_index: number;
  total_answered: number;
  total_questions: number;
}

export interface DomainBreakdownItem {
  domain: string;
  subject: string;
  total_questions: number;
  correct_questions: number;
  accuracy: number;
  classification: "WEAK" | "MODERATE" | "STRONG";
}

export interface DiagnosticResult {
  id: string;
  session_id: string;
  math_correct: number;
  math_total: number;
  rw_correct: number;
  rw_total: number;
  math_accuracy: number;
  rw_accuracy: number;
  total_accuracy: number;
  estimated_math_low: number;
  estimated_math_high: number;
  estimated_rw_low: number;
  estimated_rw_high: number;
  estimated_total_low: number;
  estimated_total_high: number;
  duration_seconds: number;
  domain_breakdown: DomainBreakdownItem[];
  weak_domains: string[];
  strong_domains: string[];
  completed_at: string;
}
