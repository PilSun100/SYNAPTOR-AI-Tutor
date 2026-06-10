from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MaterialUploadResponse(BaseModel):
    id: int
    title: str
    file_path: str | None
    extracted_text_length: int
    preview: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MaterialSummaryResponse(BaseModel):
    id: int
    title: str
    extracted_text_length: int
    preview: str
    created_at: datetime


class MaterialListResponse(BaseModel):
    materials: list[MaterialSummaryResponse]
