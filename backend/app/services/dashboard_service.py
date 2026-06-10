from datetime import UTC, datetime, time

from sqlalchemy.orm import Session

from app.models.learning import (
    Concept,
    ConceptMastery,
    LearningMaterial,
    LearningSession,
    utc_now,
)
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    MemorySummaryResponse,
    MisconceptionNoteResponse,
    RecentSessionResponse,
    ReviewScheduleItemResponse,
)
from app.services.learning_profile_service import build_learning_profile_response
from app.services.review_service import build_daily_review


def build_dashboard_summary(db: Session, user_id: int) -> DashboardSummaryResponse:
    profile = build_learning_profile_response(db, user_id)
    daily_review = build_daily_review(db, user_id)
    masteries = _user_masteries(db, user_id)

    return DashboardSummaryResponse(
        profile=profile,
        daily_review=daily_review,
        memory_summary=_memory_summary(
            db,
            user_id,
            masteries,
            sum(1 for item in daily_review.review_items if item.priority == "high"),
        ),
        misconception_notes=_misconception_notes(masteries),
        review_schedule=_review_schedule(masteries, daily_review),
        recent_sessions=_recent_sessions(db, user_id),
        generated_at=utc_now(),
    )


def _user_masteries(db: Session, user_id: int) -> list[ConceptMastery]:
    return (
        db.query(ConceptMastery)
        .join(Concept, ConceptMastery.concept_id == Concept.id)
        .join(LearningMaterial, Concept.material_id == LearningMaterial.id)
        .filter(LearningMaterial.user_id == user_id)
        .all()
    )


def _memory_summary(
    db: Session,
    user_id: int,
    masteries: list[ConceptMastery],
    high_priority_count: int,
) -> MemorySummaryResponse:
    total_materials = db.query(LearningMaterial).filter(LearningMaterial.user_id == user_id).count()
    total_concepts = (
        db.query(Concept)
        .join(LearningMaterial, Concept.material_id == LearningMaterial.id)
        .filter(LearningMaterial.user_id == user_id)
        .count()
    )
    average_mastery = _average([mastery.mastery_level for mastery in masteries])
    due_today_count = sum(1 for mastery in masteries if _is_due_today(mastery.next_review_at))
    weak_concept_count = sum(
        1
        for mastery in masteries
        if mastery.mastery_level < 0.65 or mastery.misconception_count > 0 or mastery.hint_dependency >= 0.6
    )

    return MemorySummaryResponse(
        total_materials=total_materials,
        total_concepts=total_concepts,
        average_mastery=average_mastery,
        due_today_count=due_today_count,
        high_priority_count=high_priority_count,
        weak_concept_count=weak_concept_count,
    )


def _misconception_notes(masteries: list[ConceptMastery]) -> list[MisconceptionNoteResponse]:
    notes = [
        MisconceptionNoteResponse(
            concept_id=mastery.concept_id,
            concept_title=mastery.concept.title,
            misconception_count=mastery.misconception_count,
            hint_dependency=round(mastery.hint_dependency, 2),
            reason=_misconception_reason(mastery),
        )
        for mastery in sorted(
            masteries,
            key=lambda item: (item.misconception_count, item.hint_dependency, 1 - item.mastery_level),
            reverse=True,
        )
        if mastery.misconception_count > 0 or mastery.hint_dependency >= 0.6
    ]
    return notes[:5]


def _review_schedule(masteries: list[ConceptMastery], daily_review) -> list[ReviewScheduleItemResponse]:
    daily_by_concept = {item.concept_id: item for item in daily_review.review_items}
    scheduled = []

    for mastery in sorted(
        masteries,
        key=lambda item: (
            _as_utc(item.next_review_at) or datetime.max.replace(tzinfo=UTC),
            item.mastery_level,
        ),
    ):
        daily_item = daily_by_concept.get(mastery.concept_id)
        if daily_item:
            scheduled.append(
                ReviewScheduleItemResponse(
                    concept_id=daily_item.concept_id,
                    concept_title=daily_item.concept_title,
                    next_review_at=daily_item.next_review_at,
                    priority=daily_item.priority,
                    recommended_method=daily_item.recommended_method,
                    reason=daily_item.reason,
                )
            )
        elif mastery.next_review_at:
            scheduled.append(
                ReviewScheduleItemResponse(
                    concept_id=mastery.concept_id,
                    concept_title=mastery.concept.title,
                    next_review_at=mastery.next_review_at,
                    priority="upcoming",
                    recommended_method=mastery.next_question_type or "spaced_review",
                    reason="간격 반복 일정에 따라 예정된 복습입니다.",
                )
            )

    return scheduled[:8]


def _recent_sessions(db: Session, user_id: int) -> list[RecentSessionResponse]:
    sessions = (
        db.query(LearningSession)
        .filter(LearningSession.user_id == user_id)
        .order_by(LearningSession.started_at.desc())
        .limit(5)
        .all()
    )

    return [
        RecentSessionResponse(
            session_id=session.id,
            material_id=session.material_id,
            material_title=session.material.title,
            started_at=session.started_at,
            ended_at=session.ended_at,
            total_answers=len(session.answers),
            average_score=_average([answer.correctness_score for answer in session.answers]),
            misconception_count=sum(1 for answer in session.answers if answer.misconception_detected),
        )
        for session in sessions
    ]


def _misconception_reason(mastery: ConceptMastery) -> str:
    if mastery.misconception_count > 0 and mastery.hint_dependency >= 0.6:
        return "오개념과 힌트 의존도가 함께 높아 교정 질문 뒤 쉬운 예시가 필요합니다."
    if mastery.misconception_count > 0:
        return "반복 오개념이 있어 PDF 근거와 내 답변의 차이를 비교해야 합니다."
    return "힌트 의존도가 높아 독립 회상으로 전환해야 합니다."


def _is_due_today(value: datetime | None) -> bool:
    if value is None:
        return False
    now = utc_now()
    due = _as_utc(value)
    return due <= datetime.combine(now.date(), time.max, tzinfo=UTC)


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)
