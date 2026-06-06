from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.adaptive import AdaptiveLearningStateResponse


class AnswerSubmitRequest(BaseModel):
    answer_text: str = Field(..., min_length=1)
    session_id: int | None = None
    response_time: float | None = Field(default=None, ge=0)


class AnswerEvaluationResponse(BaseModel):
    id: int
    session_id: int
    question_id: int
    answer_text: str
    correctness_score: float
    missing_points: str
    misconception_detected: bool
    response_time: float | None
    feedback: str
    adaptive_state: AdaptiveLearningStateResponse
    source: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
