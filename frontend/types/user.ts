export interface UserProfile {
  id: string;
  user_id: string;
  target_score: number;
  diagnostic_status: "not_started" | "in_progress" | "completed";
  study_goal: string;
  daily_goal_minutes: number;
  math_estimate: number | null;
  rw_estimate: number | null;
  created_at: string;
  updated_at: string;
}

export interface User {
  id: string;
  telegram_id: number;
  username: string | null;
  first_name: string;
  last_name: string | null;
  language_code: string;
  avatar_url: string | null;
  target_score: number;
  current_score_estimate: number;
  math_estimate: number;
  rw_estimate: number;
  level: number;
  xp: number;
  is_active: boolean;
  last_active_at: string;
  created_at: string;
  updated_at: string;
  profile?: UserProfile | null;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}
