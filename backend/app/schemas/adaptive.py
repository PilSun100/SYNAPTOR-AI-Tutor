from datetime import datetime

from pydantic import BaseModel


class AdaptiveLearningStateResponse(BaseModel):
    mastery_level: float
    confidence_score: float
    cognitive_load_score: float
    learner_level_label: str
    next_difficulty: str
    next_question_type: str
    recommended_strategy: str
    personalized_explanation: str
    next_review_at: datetime | None = None
