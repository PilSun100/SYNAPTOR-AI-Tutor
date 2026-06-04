from collections import defaultdict

from app.models.learning import LearningSession, UserAnswer
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
            next_review_at=mastery.next_review_at if mastery else None,
            reason="이번 세션에서 학습한 개념입니다.",
        )
        studied_concepts.append(item)

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
        self_correct_count=self_correct_count,
        hinted_correct_count=hinted_correct_count,
        repeated_wrong_count=repeated_wrong_count,
        misconception_count=misconception_count,
        studied_concepts=studied_concepts,
        self_correct_concepts=self_correct_concepts,
        hinted_correct_concepts=hinted_correct_concepts,
        repeated_wrong_concepts=repeated_wrong_concepts,
        next_review_concepts=next_review_concepts,
    )


def _average_score(answers: list[UserAnswer]) -> float:
    if not answers:
        return 0.0
    return round(sum(answer.correctness_score for answer in answers) / len(answers), 2)


def _concept_item(
    concept_id: int,
    title: str,
    mastery_level: float | None,
    next_review_at,
    reason: str,
) -> ReportConceptItem:
    return ReportConceptItem(
        concept_id=concept_id,
        title=title,
        mastery_level=mastery_level,
        next_review_at=next_review_at,
        reason=reason,
    )


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
