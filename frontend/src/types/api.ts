export type MaterialUploadResponse = {
  id: number;
  title: string;
  file_path: string | null;
  extracted_text_length: number;
  preview: string;
  created_at: string;
};

export type Concept = {
  id: number;
  material_id: number;
  title: string;
  description: string;
  difficulty: string;
  parent_concept_id: number | null;
  created_at: string;
};

export type ConceptExtractionResponse = {
  material_id: number;
  source: string;
  count: number;
  concepts: Concept[];
};

export type Question = {
  id: number;
  concept_id: number;
  question_text: string;
  question_type: string;
  expected_answer: string;
  created_at: string;
};

export type QuestionGenerationResponse = {
  concept_id: number;
  source: string;
  count: number;
  questions: Question[];
};

export type AdaptiveLearningState = {
  mastery_level: number;
  confidence_score: number;
  cognitive_load_score: number;
  learner_level_label: string;
  next_difficulty: string;
  next_question_type: string;
  recommended_strategy: string;
  personalized_explanation: string;
  next_review_at: string | null;
};

export type EvidenceSnippet = {
  chunk_id: number;
  page_number: number;
  snippet: string;
  relevance_score: number;
};

export type AnswerEvaluationResponse = {
  id: number;
  session_id: number;
  question_id: number;
  answer_text: string;
  correctness_score: number;
  missing_points: string;
  misconception_detected: boolean;
  response_time: number | null;
  feedback: string;
  adaptive_state: AdaptiveLearningState;
  evidence: EvidenceSnippet[];
  source: string;
  created_at: string;
};

export type HintResponse = {
  id: number;
  user_answer_id: number;
  hint_level: number;
  hint_text: string;
  evidence: EvidenceSnippet[];
  source: string;
  created_at: string;
};

export type SelfExplanationResponse = {
  id: number;
  concept_id: number;
  explanation_text: string;
  accuracy_score: number;
  completeness_score: number;
  logical_connection_score: number;
  mastery_level: number;
  next_review_at: string | null;
  feedback: string;
  adaptive_state: AdaptiveLearningState;
  source: string;
  created_at: string;
};

export type ReportConceptItem = {
  concept_id: number;
  title: string;
  mastery_level: number | null;
  learner_level_label: string | null;
  next_difficulty: string | null;
  next_question_type: string | null;
  next_review_at: string | null;
  reason: string;
};

export type SessionReportResponse = {
  session_id: number;
  material_id: number;
  material_title: string;
  started_at: string;
  ended_at: string | null;
  total_answers: number;
  average_score: number;
  self_correct_count: number;
  hinted_correct_count: number;
  repeated_wrong_count: number;
  misconception_count: number;
  studied_concepts: ReportConceptItem[];
  self_correct_concepts: ReportConceptItem[];
  hinted_correct_concepts: ReportConceptItem[];
  repeated_wrong_concepts: ReportConceptItem[];
  next_review_concepts: ReportConceptItem[];
  adaptive_summary: AdaptiveLearningState[];
};
