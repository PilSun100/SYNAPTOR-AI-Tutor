from datetime import datetime

from pydantic import BaseModel

from app.schemas.profile import LearningProfileResponse
from app.schemas.reviews import DailyReviewResponse


class MemorySummaryResponse(BaseModel):
    total_materials: int
    total_concepts: int
    average_mastery: float
    due_today_count: int
    high_priority_count: int
    weak_concept_count: int


class MisconceptionNoteResponse(BaseModel):
    concept_id: int
    concept_title: str
    misconception_count: int
    hint_dependency: float
    reason: str


class ReviewScheduleItemResponse(BaseModel):
    concept_id: int
    concept_title: str
    next_review_at: datetime | None
    priority: str
    recommended_method: str
    reason: str


class RecentSessionResponse(BaseModel):
    session_id: int
    material_id: int
    material_title: str
    started_at: datetime
    ended_at: datetime | None
    total_answers: int
    average_score: float
    misconception_count: int


class DashboardSummaryResponse(BaseModel):
    profile: LearningProfileResponse
    daily_review: DailyReviewResponse
    memory_summary: MemorySummaryResponse
    misconception_notes: list[MisconceptionNoteResponse]
    review_schedule: list[ReviewScheduleItemResponse]
    recent_sessions: list[RecentSessionResponse]
    generated_at: datetime
