from pydantic import BaseModel, Field

from app.schemas.evidence import EvidenceSnippetResponse


class TutorChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


class TutorChatResponse(BaseModel):
    material_id: int
    reply: str
    learning_mode: str
    next_action: str
    suggested_questions: list[str]
    evidence: list[EvidenceSnippetResponse]
    source: str
