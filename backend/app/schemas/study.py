from pydantic import BaseModel

from app.schemas.concepts import ConceptResponse
from app.schemas.materials import MaterialSummaryResponse
from app.schemas.questions import QuestionResponse


class StudyConceptItem(BaseModel):
    concept: ConceptResponse
    question: QuestionResponse
    difficulty: str
    hint_budget: int
    concept_score: float
    tier_name: str
    completed: bool


class MaterialMasterySummary(BaseModel):
    material_score: float
    tier_name: str
    completed_concepts: int
    total_concepts: int


class StudyStartResponse(BaseModel):
    session_id: int
    material: MaterialSummaryResponse
    concepts: list[StudyConceptItem]
    material_mastery: MaterialMasterySummary | None = None
    source: str
