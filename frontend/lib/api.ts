import {
  CurrentDiagnosticState,
  DiagnosticAnswerRequest,
  DiagnosticAnswerResponse,
  DiagnosticResult,
  DiagnosticSession,
} from "@/types/diagnostic";
import { AttemptResult, AttemptSubmitRequest, Question } from "@/types/question";
import { AuthResponse, User } from "@/types/user";


export interface HealthStatus {
  status: string;
  app: string;
  version: string;
  database?: string;
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
}


export const api = new ApiClient(API_BASE_URL);

