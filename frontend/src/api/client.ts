import type {
  AnswerEvaluationResponse,
  ConceptExtractionResponse,
  HintResponse,
  MaterialUploadResponse,
  QuestionGenerationResponse,
  SelfExplanationResponse,
  SessionReportResponse,
} from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
  const contentType = response.headers.get('content-type') ?? '';
  const body = contentType.includes('application/json') ? await response.json() : null;

  if (!response.ok) {
    const detail = body?.detail ?? 'API 요청에 실패했습니다.';
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
  }

  return body as T;
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
