from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.learning import (
    Concept,
    ConceptMastery,
    LearningMaterial,
    LearningSession,
    SelfExplanation,
    UserAnswer,
    UserLearningProfile,
    utc_now,
)
from app.schemas.profile import LearningProfileResponse, WeakConceptResponse


@dataclass(frozen=True)
class ProfileRecommendation:
    method: str
    reason: str
    next_action: str


def update_learning_profile(db: Session, user_id: int | None) -> UserLearningProfile | None:
    if user_id is None:
        return None

    profile = get_or_create_learning_profile(db, user_id)
    metrics = _profile_metrics(db, user_id)
    recommendation = _recommend_intervention(metrics)

    profile.average_recall_score = metrics["average_recall_score"]
    profile.explanation_quality = metrics["explanation_quality"]
    profile.hint_dependency = metrics["hint_dependency"]
    profile.misconception_frequency = metrics["misconception_frequency"]
    profile.preferred_difficulty_level = _preferred_difficulty(metrics["average_mastery"])
    profile.frustration_risk = _frustration_risk(metrics)
    profile.best_intervention_type = recommendation.method
    profile.updated_at = utc_now()
    return profile


def build_learning_profile_response(db: Session, user_id: int) -> LearningProfileResponse:
    profile = update_learning_profile(db, user_id)
    if profile is None:
        raise ValueError("학습 프로필을 생성할 수 없습니다.")

    metrics = _profile_metrics(db, user_id)
    recommendation = _recommend_intervention(metrics)
    weak_concepts = _weak_concepts(db, user_id)
    db.commit()
    db.refresh(profile)

    return LearningProfileResponse(
        user_id=user_id,
        average_recall_score=profile.average_recall_score,
        explanation_quality=profile.explanation_quality,
        hint_dependency=profile.hint_dependency,
        misconception_frequency=profile.misconception_frequency,
        preferred_difficulty_level=profile.preferred_difficulty_level,
        frustration_risk=profile.frustration_risk,
        best_intervention_type=profile.best_intervention_type,
        recommendation_reason=recommendation.reason,
        next_action=recommendation.next_action,
        total_answers=metrics["total_answers"],
        total_self_explanations=metrics["total_self_explanations"],
        weak_concepts=weak_concepts,
        updated_at=profile.updated_at,
    )


def get_or_create_learning_profile(db: Session, user_id: int) -> UserLearningProfile:
    profile = (
        db.query(UserLearningProfile)
        .filter(UserLearningProfile.user_id == user_id)
        .one_or_none()
    )
    if profile is None:
        profile = UserLearningProfile(user_id=user_id)
        db.add(profile)
        db.flush()
    return profile


def _profile_metrics(db: Session, user_id: int) -> dict[str, float | int]:
    answers = (
        db.query(UserAnswer)
        .join(LearningSession, UserAnswer.session_id == LearningSession.id)
        .filter(LearningSession.user_id == user_id)
        .all()
    )
    explanations = (
        db.query(SelfExplanation)
        .join(Concept, SelfExplanation.concept_id == Concept.id)
        .join(LearningMaterial, Concept.material_id == LearningMaterial.id)
        .filter(LearningMaterial.user_id == user_id)
        .all()
    )
    masteries = (
        db.query(ConceptMastery)
        .filter(ConceptMastery.user_id == user_id)
        .all()
    )

    total_answers = len(answers)
    average_recall_score = _average([answer.correctness_score for answer in answers])
    hint_count = sum(len(answer.hints) for answer in answers)
    hint_dependency = _safe_ratio(hint_count, total_answers)
    misconception_frequency = _safe_ratio(
        sum(1 for answer in answers if answer.misconception_detected),
        total_answers,
    )
    explanation_quality = _average(
        [
            (
                explanation.accuracy_score
                + explanation.completeness_score
                + explanation.logical_connection_score
            )
            / 3
            for explanation in explanations
        ]
    )
    average_mastery = _average([mastery.mastery_level for mastery in masteries])
    average_cognitive_load = _average([mastery.cognitive_load_score for mastery in masteries])

    return {
        "total_answers": total_answers,
        "total_self_explanations": len(explanations),
        "average_recall_score": average_recall_score,
        "explanation_quality": explanation_quality,
        "hint_dependency": hint_dependency,
        "misconception_frequency": misconception_frequency,
        "average_mastery": average_mastery,
        "average_cognitive_load": average_cognitive_load,
    }


def _weak_concepts(db: Session, user_id: int) -> list[WeakConceptResponse]:
    masteries = (
        db.query(ConceptMastery)
        .filter(ConceptMastery.user_id == user_id)
        .order_by(
            ConceptMastery.mastery_level.asc(),
            ConceptMastery.misconception_count.desc(),
            ConceptMastery.hint_dependency.desc(),
        )
        .limit(5)
        .all()
    )

    weak_items = []
    for mastery in masteries:
        if mastery.mastery_level >= 0.78 and mastery.misconception_count == 0 and mastery.hint_dependency < 0.4:
            continue
        weak_items.append(
            WeakConceptResponse(
                concept_id=mastery.concept_id,
                title=mastery.concept.title,
                mastery_level=round(mastery.mastery_level, 2),
                misconception_count=mastery.misconception_count,
                hint_dependency=round(mastery.hint_dependency, 2),
                next_review_at=mastery.next_review_at,
                reason=_weak_reason(mastery),
            )
        )
    return weak_items


def _recommend_intervention(metrics: dict[str, float | int]) -> ProfileRecommendation:
    recall = float(metrics["average_recall_score"])
    explanation = float(metrics["explanation_quality"])
    hints = float(metrics["hint_dependency"])
    misconceptions = float(metrics["misconception_frequency"])
    frustration = _frustration_risk(metrics)

    if int(metrics["total_answers"]) == 0:
        return ProfileRecommendation(
            method="active_recall",
            reason="아직 답변 데이터가 부족해 첫 진단은 능동 회상 질문으로 시작합니다.",
            next_action="업로드한 자료에서 핵심 개념 하나를 고르고, 정답을 보기 전에 직접 답해보세요.",
        )
    if misconceptions >= 0.35:
        return ProfileRecommendation(
            method="misconception_repair",
            reason="오개념 비율이 높아 새 개념으로 넘어가기보다 헷갈린 개념을 먼저 교정해야 합니다.",
            next_action="틀린 답과 PDF 근거의 차이를 비교하는 오개념 점검 질문부터 풀어보세요.",
        )
    if hints >= 0.75 or frustration >= 0.72:
        return ProfileRecommendation(
            method="example_first",
            reason="힌트 의존도와 인지 부담이 높아 추상 설명보다 짧은 예시로 진입하는 편이 효율적입니다.",
            next_action="쉬운 예시를 하나 본 뒤, 같은 구조의 새 예시를 직접 만들어보세요.",
        )
    if recall >= 0.7 and explanation < 0.55:
        return ProfileRecommendation(
            method="feynman_check",
            reason="답은 맞히지만 자기 설명 품질이 낮아 이해한 것 같은 착각을 점검해야 합니다.",
            next_action="정답을 다시 풀기 전에 중학생에게 설명하듯 한 문단으로 재구성해보세요.",
        )
    if recall < 0.55:
        return ProfileRecommendation(
            method="active_recall",
            reason="기억 인출 점수가 낮아 다시 읽기보다 짧은 회상 질문을 반복하는 편이 좋습니다.",
            next_action="핵심 키워드 2개를 먼저 떠올린 뒤 정의형 질문에 답해보세요.",
        )
    if float(metrics["average_mastery"]) >= 0.8:
        return ProfileRecommendation(
            method="mixed_practice",
            reason="숙련도가 높아져 같은 유형 반복보다 응용과 비교 문제를 섞는 편이 효율적입니다.",
            next_action="비슷한 개념과 비교하거나 실제 사례에 적용하는 hard 질문으로 넘어가세요.",
        )
    return ProfileRecommendation(
        method="spaced_review",
        reason="현재 수행은 안정적이므로 망각 위험이 오기 전에 간격 반복으로 고정하는 단계입니다.",
        next_action="다음 복습 예정 개념을 1~2개 골라 힌트 없이 다시 답해보세요.",
    )


def _preferred_difficulty(average_mastery: float | int) -> str:
    mastery = float(average_mastery)
    if mastery < 0.35:
        return "easy"
    if mastery < 0.75:
        return "medium"
    return "hard"


def _frustration_risk(metrics: dict[str, float | int]) -> float:
    risk = (
        float(metrics["average_cognitive_load"]) * 0.45
        + float(metrics["hint_dependency"]) * 0.3
        + float(metrics["misconception_frequency"]) * 0.25
    )
    return round(_clamp(risk), 2)


def _weak_reason(mastery: ConceptMastery) -> str:
    if mastery.misconception_count > 0:
        return "오개념이 반복되어 먼저 교정해야 합니다."
    if mastery.hint_dependency >= 0.6:
        return "힌트를 많이 사용해 독립 회상 연습이 필요합니다."
    if mastery.mastery_level < 0.45:
        return "숙련도가 낮아 쉬운 질문부터 다시 인출해야 합니다."
    return "복습 주기에 맞춰 기억을 다시 강화할 시점입니다."


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)


def _safe_ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 2)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))
