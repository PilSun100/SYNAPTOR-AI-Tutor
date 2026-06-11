from collections import defaultdict
from dataclasses import asdict

from app.models.learning import LearningSession, UserAnswer
from app.services.adaptive_learning_service import build_adaptive_state
from app.schemas.reports import ReportConceptItem, SessionReportResponse

CORRECT_THRESHOLD = 0.7


def build_session_report(session: LearningSession) -> SessionReportResponse:
    answers = list(session.answers)
    total_answers = len(answers)
    average_score = _average_score(answers)

    concept_answers: dict[int, list[UserAnswer]] = defaultdict(list)
    for answer in answers:
        concept_answers[answer.question.concept_id].append(answer)

    studied_concepts = []
    self_correct_concepts = []
    hinted_correct_concepts = []
    repeated_wrong_concepts = []
    next_review_concepts = []
    adaptive_summary = []

    self_correct_count = 0
    hinted_correct_count = 0
    repeated_wrong_count = 0
    misconception_count = sum(1 for answer in answers if answer.misconception_detected)

    for concept_id, grouped_answers in concept_answers.items():
        concept = grouped_answers[0].question.concept
        mastery = concept.mastery
        item = _concept_item(
            concept_id=concept_id,
            title=concept.title,
            mastery_level=mastery.mastery_level if mastery else None,
            learner_level_label=mastery.learner_level_label if mastery else None,
            concept_score=mastery.concept_score if mastery else None,
            tier_name=mastery.tier_name if mastery else None,
            next_difficulty=mastery.next_difficulty if mastery else None,
            next_question_type=mastery.next_question_type if mastery else None,
            next_review_at=mastery.next_review_at if mastery else None,
            reason="이번 세션에서 학습한 개념입니다.",
        )
        studied_concepts.append(item)
        if mastery:
            adaptive_summary.append(asdict(build_adaptive_state(concept, mastery)))

        if any(_is_self_correct(answer) for answer in grouped_answers):
            self_correct_count += 1
            self_correct_concepts.append(item.model_copy(update={"reason": "힌트 없이 기준 점수 이상으로 답했습니다."}))

        if any(_is_hinted_correct(answer) for answer in grouped_answers):
            hinted_correct_count += 1
            hinted_correct_concepts.append(item.model_copy(update={"reason": "힌트를 사용한 뒤 기준 점수에 도달했습니다."}))

        wrong_attempts = [answer for answer in grouped_answers if answer.correctness_score < CORRECT_THRESHOLD]
        if len(wrong_attempts) >= 2 or any(answer.misconception_detected for answer in grouped_answers):
            repeated_wrong_count += 1
            repeated_wrong_concepts.append(item.model_copy(update={"reason": "반복 오답 또는 오개념이 감지되었습니다."}))

        if _needs_review(grouped_answers, mastery):
            next_review_concepts.append(item.model_copy(update={"reason": _review_reason(grouped_answers, mastery)}))

    return SessionReportResponse(
        session_id=session.id,
        material_id=session.material_id,
        material_title=session.material.title,
        started_at=session.started_at,
        ended_at=session.ended_at,
        total_answers=total_answers,
        average_score=average_score,
        material_score=_material_mastery_value(session, "material_score"),
        material_tier=_material_mastery_value(session, "tier_name"),
        material_completed_concepts=_material_mastery_value(session, "completed_concepts"),
        material_total_concepts=_material_mastery_value(session, "total_concepts"),
        self_correct_count=self_correct_count,
        hinted_correct_count=hinted_correct_count,
        repeated_wrong_count=repeated_wrong_count,
        misconception_count=misconception_count,
        studied_concepts=studied_concepts,
        self_correct_concepts=self_correct_concepts,
        hinted_correct_concepts=hinted_correct_concepts,
        repeated_wrong_concepts=repeated_wrong_concepts,
        next_review_concepts=next_review_concepts,
        adaptive_summary=adaptive_summary,
    )


def _average_score(answers: list[UserAnswer]) -> float:
    if not answers:
        return 0.0
    return round(sum(answer.correctness_score for answer in answers) / len(answers), 2)


def _concept_item(
    concept_id: int,
    title: str,
    mastery_level: float | None,
    learner_level_label: str | None,
    concept_score: float | None,
    tier_name: str | None,
    next_difficulty: str | None,
    next_question_type: str | None,
    next_review_at,
    reason: str,
) -> ReportConceptItem:
    return ReportConceptItem(
        concept_id=concept_id,
        title=title,
        mastery_level=mastery_level,
        learner_level_label=learner_level_label,
        concept_score=concept_score,
        tier_name=tier_name,
        next_difficulty=next_difficulty,
        next_question_type=next_question_type,
        next_review_at=next_review_at,
        reason=reason,
    )


def _material_mastery_value(session: LearningSession, field_name: str):
    if session.user is None:
        return None
    for record in session.user.material_mastery_records:
        if record.material_id == session.material_id:
            return getattr(record, field_name)
    return None


def _is_self_correct(answer: UserAnswer) -> bool:
    return answer.correctness_score >= CORRECT_THRESHOLD and len(answer.hints) == 0


def _is_hinted_correct(answer: UserAnswer) -> bool:
    return answer.correctness_score >= CORRECT_THRESHOLD and len(answer.hints) > 0


def _needs_review(answers: list[UserAnswer], mastery) -> bool:
    if mastery and mastery.next_review_at:
        return True
    if any(answer.misconception_detected for answer in answers):
        return True
    return any(answer.correctness_score < CORRECT_THRESHOLD for answer in answers)


def _review_reason(answers: list[UserAnswer], mastery) -> str:
    if any(answer.misconception_detected for answer in answers):
        return "오개념이 감지되어 우선 복습이 필요합니다."
    if any(answer.correctness_score < CORRECT_THRESHOLD for answer in answers):
        return "기준 점수에 도달하지 못해 재인출 연습이 필요합니다."
    if mastery and mastery.next_review_at:
        return "간격 반복 일정에 따라 다시 복습할 개념입니다."
    return "복습 추천 개념입니다."
