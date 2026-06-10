import type {
  AnswerEvaluationResponse,
  AuthResponse,
  ConceptExtractionResponse,
  DailyReviewResponse,
  DashboardSummaryResponse,
  HintResponse,
  LearningProfileResponse,
  MaterialUploadResponse,
  QuestionGenerationResponse,
  SelfExplanationResponse,
  SessionReportResponse,
  User,
} from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api';
const ACCESS_TOKEN_KEY = 'brain_sync_access_token';
const REFRESH_TOKEN_KEY = 'brain_sync_refresh_token';

export function getStoredAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getStoredRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function storeAuthTokens(accessToken: string, refreshToken: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

export function clearAuthTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

async function request<T>(path: string, init: RequestInit = {}, retry = true): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, withAuthHeader(init));
  const contentType = response.headers.get('content-type') ?? '';
  const body = contentType.includes('application/json') ? await response.json() : null;

  if (response.status === 401 && retry && getStoredRefreshToken()) {
    try {
      await refreshSession();
      return request<T>(path, init, false);
    } catch {
      clearAuthTokens();
    }
  }

  if (!response.ok) {
    const detail = body?.detail ?? 'API 요청에 실패했습니다.';
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
  }

  return body as T;
}

function withAuthHeader(init: RequestInit): RequestInit {
  const headers = new Headers(init.headers);
  const token = getStoredAccessToken();
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  return { ...init, headers };
}

export async function registerUser(
  email: string,
  password: string,
  displayName: string,
): Promise<AuthResponse> {
  const auth = await request<AuthResponse>(
    '/auth/register',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, display_name: displayName }),
    },
    false,
  );
  storeAuthTokens(auth.access_token, auth.refresh_token);
  return auth;
}

export async function loginUser(email: string, password: string): Promise<AuthResponse> {
  const auth = await request<AuthResponse>(
    '/auth/login',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    },
    false,
  );
  storeAuthTokens(auth.access_token, auth.refresh_token);
  return auth;
}

export async function refreshSession(): Promise<AuthResponse> {
  const refreshToken = getStoredRefreshToken();
  if (!refreshToken) {
    throw new Error('다시 로그인해야 합니다.');
  }

  const auth = await request<AuthResponse>(
    '/auth/refresh',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    },
    false,
  );
  storeAuthTokens(auth.access_token, auth.refresh_token);
  return auth;
}

export function getCurrentUser(): Promise<User> {
  return request<User>('/auth/me');
}

export function getLearningProfile(): Promise<LearningProfileResponse> {
  return request<LearningProfileResponse>('/profile/learning');
}

export function getDailyReview(): Promise<DailyReviewResponse> {
  return request<DailyReviewResponse>('/reviews/daily');
}

export function getDashboardSummary(): Promise<DashboardSummaryResponse> {
  return request<DashboardSummaryResponse>('/dashboard/summary');
}

export async function uploadMaterial(file: File): Promise<MaterialUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  return request<MaterialUploadResponse>('/materials/upload', {
    method: 'POST',
    body: formData,
  });
}

export function extractConcepts(materialId: number): Promise<ConceptExtractionResponse> {
  return request<ConceptExtractionResponse>(`/materials/${materialId}/concepts/extract`, {
    method: 'POST',
  });
}

export function generateQuestions(conceptId: number): Promise<QuestionGenerationResponse> {
  return request<QuestionGenerationResponse>(`/concepts/${conceptId}/questions/generate`, {
    method: 'POST',
  });
}

export function submitAnswer(
  questionId: number,
  answerText: string,
  responseTime?: number,
  sessionId?: number | null,
): Promise<AnswerEvaluationResponse> {
  return request<AnswerEvaluationResponse>(`/questions/${questionId}/answer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      answer_text: answerText,
      response_time: responseTime,
      session_id: sessionId,
    }),
  });
}

export function requestHint(answerId: number, hintLevel: number): Promise<HintResponse> {
  return request<HintResponse>(`/answers/${answerId}/hint`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ hint_level: hintLevel }),
  });
}

export function submitSelfExplanation(
  conceptId: number,
  explanationText: string,
): Promise<SelfExplanationResponse> {
  return request<SelfExplanationResponse>(`/concepts/${conceptId}/self-explanation`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ explanation_text: explanationText }),
  });
}

export function getSessionReport(sessionId: number): Promise<SessionReportResponse> {
  return request<SessionReportResponse>(`/sessions/${sessionId}/report`);
}
