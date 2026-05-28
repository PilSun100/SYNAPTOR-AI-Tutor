from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HintRequest(BaseModel):
    hint_level: int = Field(..., ge=1, le=5)


class HintResponse(BaseModel):
    id: int
    user_answer_id: int
    hint_level: int
    hint_text: str
    source: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
