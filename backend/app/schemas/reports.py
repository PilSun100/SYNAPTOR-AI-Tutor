from datetime import datetime

from pydantic import BaseModel

from app.schemas.adaptive import AdaptiveLearningStateResponse


class ReportConceptItem(BaseModel):
    concept_id: int
    title: str
    mastery_level: float | None = None
    learner_level_label: str | None = None
    concept_score: float | None = None
    tier_name: str | None = None
    next_difficulty: str | None = None
    next_question_type: str | None = None
    next_review_at: datetime | None = None
    reason: str


class SessionReportResponse(BaseModel):
    session_id: int
    material_id: int
    material_title: str
    started_at: datetime
    ended_at: datetime | None
    total_answers: int
    average_score: float
    material_score: float | None = None
    material_tier: str | None = None
    material_completed_concepts: int | None = None
    material_total_concepts: int | None = None
    self_correct_count: int
    hinted_correct_count: int
    repeated_wrong_count: int
    misconception_count: int
    studied_concepts: list[ReportConceptItem]
    self_correct_concepts: list[ReportConceptItem]
    hinted_correct_concepts: list[ReportConceptItem]
    repeated_wrong_concepts: list[ReportConceptItem]
    next_review_concepts: list[ReportConceptItem]
    adaptive_summary: list[AdaptiveLearningStateResponse]
