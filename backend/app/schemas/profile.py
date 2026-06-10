from datetime import datetime

from pydantic import BaseModel


class WeakConceptResponse(BaseModel):
    concept_id: int
    title: str
    mastery_level: float
    misconception_count: int
    hint_dependency: float
    next_review_at: datetime | None
    reason: str


class LearningProfileResponse(BaseModel):
    user_id: int
    average_recall_score: float
    explanation_quality: float
    hint_dependency: float
    misconception_frequency: float
    preferred_difficulty_level: str
    frustration_risk: float
    best_intervention_type: str
    recommendation_reason: str
    next_action: str
    total_answers: int
    total_self_explanations: int
    weak_concepts: list[WeakConceptResponse]
    updated_at: datetime
