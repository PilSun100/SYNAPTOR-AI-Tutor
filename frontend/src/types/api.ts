export type MaterialUploadResponse = {
  id: number;
  title: string;
  file_path: string | null;
  extracted_text_length: number;
  preview: string;
  created_at: string;
};

export type MaterialSummary = {
  id: number;
  title: string;
  extracted_text_length: number;
  preview: string;
  created_at: string;
};

export type MaterialListResponse = {
  materials: MaterialSummary[];
};

export type User = {
  id: number;
  email: string;
  display_name: string;
  created_at: string;
};

export type AuthResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
};

export type WeakConcept = {
  concept_id: number;
  title: string;
  mastery_level: number;
  misconception_count: number;
  hint_dependency: number;
  next_review_at: string | null;
  reason: string;
};

export type LearningProfileResponse = {
  user_id: number;
  average_recall_score: number;
  explanation_quality: number;
  hint_dependency: number;
  misconception_frequency: number;
  preferred_difficulty_level: string;
  frustration_risk: number;
  best_intervention_type: string;
  recommendation_reason: string;
  next_action: string;
  total_answers: number;
  total_self_explanations: number;
  weak_concepts: WeakConcept[];
  updated_at: string;
};

export type DailyReviewItem = {
  concept_id: number;
  concept_title: string;
  reason: string;
  priority: 'high' | 'medium' | 'low';
  recommended_method: string;
  estimated_minutes: number;
  next_review_at: string | null;
  mastery_level: number;
  forgetting_risk: number;
};

export type DailyReviewResponse = {
  review_items: DailyReviewItem[];
  estimated_total_minutes: number;
  generated_at: string;
};

export type MemorySummary = {
  total_materials: number;
  total_concepts: number;
  average_mastery: number;
  due_today_count: number;
  high_priority_count: number;
  weak_concept_count: number;
};

export type MisconceptionNote = {
  concept_id: number;
  concept_title: string;
  misconception_count: number;
  hint_dependency: number;
  reason: string;
};

export type ReviewScheduleItem = {
  concept_id: number;
  concept_title: string;
  next_review_at: string | null;
  priority: string;
  recommended_method: string;
  reason: string;
};

export type RecentSession = {
  session_id: number;
  material_id: number;
  material_title: string;
  started_at: string;
  ended_at: string | null;
  total_answers: number;
  average_score: number;
  misconception_count: number;
};

export type DashboardSummaryResponse = {
  profile: LearningProfileResponse;
  daily_review: DailyReviewResponse;
  memory_summary: MemorySummary;
  misconception_notes: MisconceptionNote[];
  review_schedule: ReviewScheduleItem[];
  recent_sessions: RecentSession[];
  generated_at: string;
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

export type StudyStartResponse = {
  session_id: number;
  material: MaterialSummary;
  concepts: StudyConceptItem[];
  material_mastery: MaterialMasterySummary | null;
  source: string;
};

export type StudyConceptItem = {
  concept: Concept;
  question: Question;
  difficulty: string;
  hint_budget: number;
  concept_score: number;
  tier_name: string;
  completed: boolean;
};

export type MaterialMasterySummary = {
  material_score: number;
  tier_name: string;
  completed_concepts: number;
  total_concepts: number;
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
  chunk_type: string;
  snippet: string;
  relevance_score: number;
};

export type TutorChatResponse = {
  material_id: number;
  reply: string;
  learning_mode: string;
  next_action: string;
  suggested_questions: string[];
  evidence: EvidenceSnippet[];
  source: string;
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
  hints_used: number;
  hint_budget: number;
  concept_score: number;
  concept_tier: string;
  material_score: number | null;
  material_tier: string | null;
  material_completed_concepts: number | null;
  material_total_concepts: number | null;
  adaptive_state: AdaptiveLearningState;
  evidence: EvidenceSnippet[];
  source: string;
  created_at: string;
};

export type HintResponse = {
  id: number;
  user_answer_id: number | null;
  session_id: number | null;
  question_id: number | null;
  concept_id: number | null;
  hint_level: number;
  hint_budget: number;
  hints_used: number;
  hint_text: string;
  stuck_reason: string | null;
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
