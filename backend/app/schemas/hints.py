from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.evidence import EvidenceSnippetResponse


class HintRequest(BaseModel):
    hint_level: int = Field(..., ge=1, le=5)
    session_id: int | None = None
    stuck_reason: str | None = Field(default=None, max_length=100)


class HintResponse(BaseModel):
    id: int
    user_answer_id: int | None
    session_id: int | None = None
    question_id: int | None = None
    concept_id: int | None = None
    hint_level: int
    hint_budget: int
    hints_used: int
    hint_text: str
    stuck_reason: str | None = None
    evidence: list[EvidenceSnippetResponse]
    source: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
