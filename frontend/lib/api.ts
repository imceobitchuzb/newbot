import {
  CurrentDiagnosticState,
  DiagnosticAnswerRequest,
  DiagnosticAnswerResponse,
  DiagnosticResult,
  DiagnosticSession,
} from "@/types/diagnostic";
import {
  AdaptiveAnalyticsResponse,
  AdaptiveAnswerRequest,
  AdaptiveAnswerResponse,
  AdaptiveNextQuestionResponse,
  AdaptiveSessionResponse,
  AdaptiveSessionStartRequest,
} from "@/types/adaptive";
import {
  MistakeAnalyticsResponse,
  MistakeClassifyRequest,
  MistakeEntryItem,
  MistakeListResponse,
  MistakeRetryRequest,
  MistakeRetryResponse,
  MistakeReviewRequest,
} from "@/types/mistake";
import {
  DesmosAnalytics,
  DesmosAnswerResponse,
  DesmosSession,
  DesmosTechnique,
  DesmosTechniqueDetail,
} from "@/types/desmos";
import {
  TutorConversationDetail,
  TutorConversationSummary,
  TutorCreateConversationRequest,
  TutorExplainRequest,
  TutorExplainResponse,
  TutorMessage,
  TutorSendMessageRequest,
} from "@/types/tutor";
import { AttemptResult, AttemptSubmitRequest, Question } from "@/types/question";
import { AuthResponse, User } from "@/types/user";


export interface HealthStatus {
  status: string;
  app: string;
  version: string;
  database?: string;
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  (typeof window === "undefined" ? "http://localhost:8000" : "");

const TOKEN_STORAGE_KEY = "sat_master_access_token";

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl.replace(/\/+$/, "");
  }

  public getToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem(TOKEN_STORAGE_KEY);
  }

  public setToken(token: string): void {
    if (typeof window === "undefined") return;
    localStorage.setItem(TOKEN_STORAGE_KEY, token);
  }

  public clearToken(): void {
    if (typeof window === "undefined") return;
    localStorage.removeItem(TOKEN_STORAGE_KEY);
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      Accept: "application/json",
    };

    const token = this.getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers: {
        ...headers,
        ...options.headers,
      },
    });

    if (!response.ok) {
      let errorMessage = `HTTP error ${response.status}`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || errorMessage;
      } catch {
        // Fallback
      }
      throw new Error(errorMessage);
    }

    return response.json();
  }

  /**
   * Health check endpoint
   */
  async getHealth(): Promise<HealthStatus> {
    return this.request<HealthStatus>("/api/v1/health");
  }

  /**
   * Telegram WebApp authentication endpoint
   */
  async loginTelegram(initData: string): Promise<AuthResponse> {
    const result = await this.request<AuthResponse>("/api/v1/auth/telegram", {
      method: "POST",
      body: JSON.stringify({ init_data: initData }),
    });
    this.setToken(result.access_token);
    return result;
  }

  /**
   * Development login endpoint for browser testing outside Telegram
   */
  async loginDev(payload: { telegram_id?: number; first_name?: string; username?: string } = {}): Promise<AuthResponse> {
    const result = await this.request<AuthResponse>("/api/v1/auth/dev", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    this.setToken(result.access_token);
    return result;
  }

  /**
   * Retrieve current authenticated user profile
   */
  async getMe(): Promise<User> {
    return this.request<User>("/api/v1/users/me");
  }

  /**
   * Fetch published questions with optional filters
   */
  async getQuestions(params: {
    subject?: string;
    domain?: string;
    skill?: string;
    difficulty?: string;
    limit?: number;
  } = {}): Promise<Question[]> {
    const query = new URLSearchParams();
    if (params.subject) query.append("subject", params.subject);
    if (params.domain) query.append("domain", params.domain);
    if (params.skill) query.append("skill", params.skill);
    if (params.difficulty) query.append("difficulty", params.difficulty);
    if (params.limit) query.append("limit", params.limit.toString());

    const qs = query.toString();
    return this.request<Question[]>(`/api/v1/questions${qs ? `?${qs}` : ""}`);
  }

  /**
   * Fetch a single question by UUID
   */
  async getQuestionById(questionId: string): Promise<Question> {
    return this.request<Question>(`/api/v1/questions/${questionId}`);
  }

  /**
   * Fetch a random question for practice
   */
  async getRandomQuestion(params: { subject?: string; difficulty?: string } = {}): Promise<Question> {
    const query = new URLSearchParams();
    if (params.subject) query.append("subject", params.subject);
    if (params.difficulty) query.append("difficulty", params.difficulty);

    const qs = query.toString();
    return this.request<Question>(`/api/v1/questions/random${qs ? `?${qs}` : ""}`);
  }

  /**
   * Submit an answer attempt for a question
   */
  async submitAttempt(
    questionId: string,
    payload: AttemptSubmitRequest,
  ): Promise<AttemptResult> {
    return this.request<AttemptResult>(`/api/v1/questions/${questionId}/attempt`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  /**
   * Start or resume a 40-question SAT Master Diagnostic session
   */
  async startOrResumeDiagnostic(): Promise<DiagnosticSession> {
    return this.request<DiagnosticSession>("/api/v1/diagnostics", {
      method: "POST",
    });
  }

  /**
   * Get current active diagnostic state & question
   */
  async getCurrentDiagnostic(): Promise<CurrentDiagnosticState | null> {
    return this.request<CurrentDiagnosticState | null>("/api/v1/diagnostics/current");
  }

  /**
   * Submit an answer for an assigned diagnostic question
   */
  async submitDiagnosticAnswer(
    diagnosticId: string,
    questionId: string,
    payload: DiagnosticAnswerRequest,
  ): Promise<DiagnosticAnswerResponse> {
    return this.request<DiagnosticAnswerResponse>(
      `/api/v1/diagnostics/${diagnosticId}/questions/${questionId}/answer`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    );
  }

  /**
   * Retrieve calculated results for a completed diagnostic
   */
  async getDiagnosticResult(diagnosticId?: string): Promise<DiagnosticResult> {
    const endpoint = diagnosticId
      ? `/api/v1/diagnostics/${diagnosticId}/result`
      : `/api/v1/diagnostics/latest/result`;
    return this.request<DiagnosticResult>(endpoint);
  }

  // ==================== MATH MODULE ====================

  /**
   * Start or resume a customized math practice session
   */
  async startMathPractice(
    data: import("@/types/math").MathPracticeStartRequest
  ): Promise<import("@/types/math").MathPracticeSessionResponse> {
    return this.request<import("@/types/math").MathPracticeSessionResponse>(
      "/api/v1/math/practice",
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    );
  }

  /**
   * Get active practice session if any
   */
  async getCurrentMathPractice(): Promise<import("@/types/math").MathPracticeSessionResponse | null> {
    try {
      return await this.request<import("@/types/math").MathPracticeSessionResponse | null>(
        "/api/v1/math/practice/current"
      );
    } catch {
      return null;
    }
  }

  /**
   * Get practice session by ID
   */
  async getMathPracticeSession(
    sessionId: string
  ): Promise<import("@/types/math").MathPracticeSessionResponse> {
    return this.request<import("@/types/math").MathPracticeSessionResponse>(
      `/api/v1/math/practice/${sessionId}`
    );
  }

  /**
   * Submit answer for a practice question in session
   */
  async submitMathPracticeAnswer(
    sessionId: string,
    practiceQuestionId: string,
    payload: import("@/types/math").MathPracticeAnswerRequest
  ): Promise<import("@/types/math").MathPracticeAnswerResponse> {
    return this.request<import("@/types/math").MathPracticeAnswerResponse>(
      `/api/v1/math/practice/${sessionId}/questions/${practiceQuestionId}/answer`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    );
  }

  /**
   * Get completion results and domain breakdown for practice session
   */
  async getMathPracticeResult(
    sessionId: string
  ): Promise<import("@/types/math").MathPracticeResultResponse> {
    return this.request<import("@/types/math").MathPracticeResultResponse>(
      `/api/v1/math/practice/${sessionId}/result`
    );
  }

  /**
   * Get user's overall math mastery and domain analytics
   */
  async getMathAnalytics(): Promise<import("@/types/math").MathAnalyticsResponse> {
    return this.request<import("@/types/math").MathAnalyticsResponse>(
      "/api/v1/math/analytics"
    );
  }

  /**
   * Get single domain analytics and skills breakdown
   */
  async getDomainAnalytics(
    domain: string
  ): Promise<import("@/types/math").DomainAnalyticsOut> {
    return this.request<import("@/types/math").DomainAnalyticsOut>(
      `/api/v1/math/domains/${encodeURIComponent(domain)}`
    );
  }

  // ==================== MISTAKE BOOK ====================

  /**
   * List mistake book entries with optional filters
   */
  async listMistakes(params?: {
    subject?: string;
    status?: string;
    mistake_type?: string;
    domain?: string;
    is_due?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<MistakeListResponse> {
    const query = new URLSearchParams();
    if (params?.subject) query.append("subject", params.subject);
    if (params?.status) query.append("status", params.status);
    if (params?.mistake_type) query.append("mistake_type", params.mistake_type);
    if (params?.domain) query.append("domain", params.domain);
    if (params?.is_due !== undefined) query.append("is_due", String(params.is_due));
    if (params?.limit !== undefined) query.append("limit", String(params.limit));
    if (params?.offset !== undefined) query.append("offset", String(params.offset));

    const qs = query.toString();
    const endpoint = qs ? `/api/v1/mistakes?${qs}` : "/api/v1/mistakes";
    return this.request<MistakeListResponse>(endpoint);
  }

  /**
   * Get highest priority due/unresolved mistake for remediation
   */
  async getNextMistake(): Promise<MistakeEntryItem | null> {
    try {
      return await this.request<MistakeEntryItem | null>("/api/v1/mistakes/next");
    } catch {
      return null;
    }
  }

  /**
   * Get user's error analytics and spaced repetition telemetry
   */
  async getMistakeAnalytics(): Promise<MistakeAnalyticsResponse> {
    return this.request<MistakeAnalyticsResponse>("/api/v1/mistakes/analytics");
  }

  /**
   * Get single mistake book entry by ID
   */
  async getMistakeById(id: string): Promise<MistakeEntryItem> {
    return this.request<MistakeEntryItem>(`/api/v1/mistakes/${id}`);
  }

  /**
   * Record spaced review on mistake
   */
  async reviewMistake(
    id: string,
    payload?: MistakeReviewRequest
  ): Promise<MistakeEntryItem> {
    return this.request<MistakeEntryItem>(`/api/v1/mistakes/${id}/review`, {
      method: "POST",
      body: JSON.stringify(payload || {}),
    });
  }

  /**
   * Update classification/root cause of mistake
   */
  async classifyMistake(
    id: string,
    payload: MistakeClassifyRequest
  ): Promise<MistakeEntryItem> {
    return this.request<MistakeEntryItem>(`/api/v1/mistakes/${id}/classify`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  }

  /**
   * Submit retry attempt on mistake
   */
  async retryMistake(
    id: string,
    payload: MistakeRetryRequest
  ): Promise<MistakeRetryResponse> {
    return this.request<MistakeRetryResponse>(`/api/v1/mistakes/${id}/retry`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  // ==================== ADAPTIVE LEARNING ENGINE ====================

  /**
   * Get standalone next question recommendation
   */
  async getAdaptiveNextQuestion(subject: string = "MATH"): Promise<AdaptiveNextQuestionResponse> {
    return this.request<AdaptiveNextQuestionResponse>(
      `/api/v1/adaptive/next?subject=${encodeURIComponent(subject)}`
    );
  }

  /**
   * Get comprehensive skill mastery analytics and curriculum trajectory
   */
  async getAdaptiveAnalytics(subject: string = "MATH"): Promise<AdaptiveAnalyticsResponse> {
    return this.request<AdaptiveAnalyticsResponse>(
      `/api/v1/adaptive/analytics?subject=${encodeURIComponent(subject)}`
    );
  }

  /**
   * Start or resume an adaptive practice session
   */
  async startAdaptiveSession(
    data?: AdaptiveSessionStartRequest
  ): Promise<AdaptiveSessionResponse> {
    return this.request<AdaptiveSessionResponse>("/api/v1/adaptive/session", {
      method: "POST",
      body: JSON.stringify(data || {}),
    });
  }

  /**
   * Get current active adaptive session
   */
  async getCurrentAdaptiveSession(subject: string = "MATH"): Promise<AdaptiveSessionResponse | null> {
    try {
      return await this.request<AdaptiveSessionResponse | null>(
        `/api/v1/adaptive/session/current?subject=${encodeURIComponent(subject)}`
      );
    } catch {
      return null;
    }
  }

  /**
   * Get adaptive session by ID
   */
  async getAdaptiveSession(sessionId: string): Promise<AdaptiveSessionResponse> {
    return this.request<AdaptiveSessionResponse>(`/api/v1/adaptive/session/${sessionId}`);
  }

  /**
   * Submit answer for a question in adaptive session
   */
  async submitAdaptiveAnswer(
    sessionId: string,
    questionId: string,
    payload: AdaptiveAnswerRequest
  ): Promise<AdaptiveAnswerResponse> {
    return this.request<AdaptiveAnswerResponse>(
      `/api/v1/adaptive/session/${sessionId}/questions/${questionId}/answer`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    );
  }

  // ==================== DESMOS LAB ====================

  /**
   * List all canonical Desmos techniques with user practice metrics
   */
  async getDesmosTechniques(): Promise<{ items: DesmosTechnique[]; total: number }> {
    return this.request<{ items: DesmosTechnique[]; total: number }>("/api/v1/desmos/techniques");
  }

  /**
   * Get technique details by slug
   */
  async getDesmosTechniqueBySlug(slug: string): Promise<DesmosTechniqueDetail> {
    return this.request<DesmosTechniqueDetail>(`/api/v1/desmos/techniques/${encodeURIComponent(slug)}`);
  }

  /**
   * Query questions where Desmos is permitted
   */
  async getDesmosQuestions(params?: {
    technique_slug?: string;
    recommended_only?: boolean;
    difficulty?: string;
    limit?: number;
  }): Promise<{ items: any[]; total: number }> {
    const query = new URLSearchParams();
    if (params?.technique_slug) query.set("technique_slug", params.technique_slug);
    if (params?.recommended_only) query.set("recommended_only", "true");
    if (params?.difficulty) query.set("difficulty", params.difficulty);
    if (params?.limit) query.set("limit", params.limit.toString());
    const qs = query.toString();
    return this.request<{ items: any[]; total: number }>(`/api/v1/desmos/questions${qs ? `?${qs}` : ""}`);
  }

  /**
   * Start or resume a Desmos practice session
   */
  async startDesmosSession(data?: {
    technique_slug?: string;
    technique_type?: string;
    difficulty?: string;
    target_count?: number;
    recommended_only?: boolean;
  }): Promise<DesmosSession> {
    return this.request<DesmosSession>("/api/v1/desmos/session", {
      method: "POST",
      body: JSON.stringify(data || {}),
    });
  }

  /**
   * Get active Desmos practice session
   */
  async getCurrentDesmosSession(): Promise<DesmosSession | null> {
    try {
      return await this.request<DesmosSession | null>("/api/v1/desmos/session/current");
    } catch {
      return null;
    }
  }

  /**
   * Get Desmos practice session by ID
   */
  async getDesmosSession(sessionId: string): Promise<DesmosSession> {
    return this.request<DesmosSession>(`/api/v1/desmos/session/${sessionId}`);
  }

  /**
   * Submit answer in a Desmos practice session
   */
  async submitDesmosAnswer(
    sessionId: string,
    questionId: string,
    payload: {
      selected_option_id: string;
      time_spent_seconds?: number;
      desmos_used?: boolean;
    }
  ): Promise<DesmosAnswerResponse> {
    return this.request<DesmosAnswerResponse>(
      `/api/v1/desmos/session/${sessionId}/questions/${questionId}/answer`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    );
  }

  /**
   * Abandon an in-progress Desmos practice session
   */
  async abandonDesmosSession(sessionId: string): Promise<DesmosSession> {
    return this.request<DesmosSession>(`/api/v1/desmos/session/${sessionId}/abandon`, {
      method: "POST",
    });
  }

  /**
   * Get user's Desmos usage analytics
   */
  async getDesmosAnalytics(): Promise<DesmosAnalytics> {
    return this.request<DesmosAnalytics>("/api/v1/desmos/analytics");
  }

  // ==================== AI SAT TUTOR ====================

  /**
   * Create a new tutor conversation
   */
  async createTutorConversation(
    data: TutorCreateConversationRequest
  ): Promise<TutorConversationDetail> {
    return this.request<TutorConversationDetail>("/api/v1/tutor/conversations", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  /**
   * List all user's conversations
   */
  async getTutorConversations(): Promise<TutorConversationSummary[]> {
    return this.request<TutorConversationSummary[]>("/api/v1/tutor/conversations");
  }

  /**
   * Get conversation detail by ID
   */
  async getTutorConversation(conversationId: string): Promise<TutorConversationDetail> {
    return this.request<TutorConversationDetail>(`/api/v1/tutor/conversations/${conversationId}`);
  }

  /**
   * Delete conversation by ID
   */
  async deleteTutorConversation(conversationId: string): Promise<void> {
    await this.request<void>(`/api/v1/tutor/conversations/${conversationId}`, {
      method: "DELETE",
    });
  }

  /**
   * Send a message to AI Tutor
   */
  async sendTutorMessage(
    conversationId: string,
    data: TutorSendMessageRequest
  ): Promise<TutorMessage> {
    return this.request<TutorMessage>(
      `/api/v1/tutor/conversations/${conversationId}/messages`,
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    );
  }

  /**
   * One-shot explanation/hint request
   */
  async explainWithTutor(data: TutorExplainRequest): Promise<TutorExplainResponse> {
    return this.request<TutorExplainResponse>("/api/v1/tutor/explain", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  /**
   * Get question context
   */
  async getTutorQuestionContext(questionId: string, mode: string = "HINT"): Promise<any> {
    return this.request<any>(
      `/api/v1/tutor/context/question/${questionId}?mode=${encodeURIComponent(mode)}`
    );
  }

  /**
   * Get mistake context
   */
  async getTutorMistakeContext(mistakeId: string): Promise<any> {
    return this.request<any>(`/api/v1/tutor/context/mistake/${mistakeId}`);
  }

  /**
   * Get skill context
   */
  async getTutorSkillContext(skill: string): Promise<any> {
    return this.request<any>(`/api/v1/tutor/context/skill/${encodeURIComponent(skill)}`);
  }
}



export const api = new ApiClient(API_BASE_URL);

