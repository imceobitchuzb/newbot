export type TutorContextType =
  | "GENERAL"
  | "QUESTION"
  | "MISTAKE"
  | "SKILL"
  | "DIAGNOSTIC"
  | "DESMOS"
  | "ADAPTIVE";

export type TutorMessageRole = "USER" | "ASSISTANT" | "SYSTEM";

export type TutorMode =
  | "HINT"
  | "EXPLANATION"
  | "SOLUTION"
  | "CONCEPT"
  | "DESMOS_HELP";

export type TutorActionType =
  | "PRACTICE_SKILL"
  | "REVIEW_MISTAKE"
  | "OPEN_DESMOS"
  | "PRACTICE_ADAPTIVE"
  | "VIEW_DIAGNOSTIC";

export type QuickPromptType =
  | "WEAKEST_SKILL"
  | "MISTAKE_REVIEW"
  | "DIAGNOSTIC_ANALYSIS"
  | "DESMOS_GUIDE"
  | "SAT_MATH_STRATEGY"
  | "RW_STRATEGY"
  | "STUDY_PLAN";

export interface TutorActionItem {
  type: string;
  title: string;
  description?: string | null;
  target_id?: string | null;
  url?: string | null;
}

export interface TutorMessage {
  id: string;
  conversation_id: string;
  role: TutorMessageRole | string;
  content: string;
  mode?: TutorMode | string | null;
  actions?: TutorActionItem[] | null;
  created_at: string;
}

export interface TutorConversationSummary {
  id: string;
  title?: string | null;
  context_type: TutorContextType | string;
  context_id?: string | null;
  subject?: string | null;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message_preview?: string | null;
}

export interface TutorConversationDetail {
  id: string;
  title?: string | null;
  context_type: TutorContextType | string;
  context_id?: string | null;
  subject?: string | null;
  created_at: string;
  updated_at: string;
  messages: TutorMessage[];
}

export interface TutorCreateConversationRequest {
  title?: string;
  context_type?: TutorContextType;
  context_id?: string;
  subject?: string;
}

export interface TutorSendMessageRequest {
  content: string;
  mode?: TutorMode;
  quick_prompt?: QuickPromptType;
}

export interface TutorExplainRequest {
  question_id?: string;
  mistake_id?: string;
  mode?: TutorMode;
  prompt?: string;
}

export interface TutorExplainResponse {
  message: string;
  mode: string;
  actions: TutorActionItem[];
  suggested_skill?: string | null;
  suggested_technique?: string | null;
}
