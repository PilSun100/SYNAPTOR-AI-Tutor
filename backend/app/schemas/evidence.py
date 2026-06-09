from pydantic import BaseModel


class EvidenceSnippetResponse(BaseModel):
    chunk_id: int
    page_number: int
    snippet: str
    relevance_score: float
