from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.learning import Concept, ConceptMastery, UserAnswer, utc_now


@dataclass(frozen=True)
class AdaptiveLearningState:
    mastery_level: float
    confidence_score: float
    cognitive_load_score: float
    learner_level_label: str
    next_difficulty: str
    next_question_type: str
    recommended_strategy: str
    personalized_explanation: str
    next_review_at: datetime | None


def update_mastery_from_answer(
    db: Session,
    answer: UserAnswer,
    hints_used: int = 0,
) -> ConceptMastery:
    concept = answer.question.concept
    mastery = get_or_create_mastery(db, concept)
    if mastery.user_id is None:
        mastery.user_id = answer.session.user_id
    answer_quality = _clamp(answer.correctness_score)
    speed_score = _response_speed_score(answer.response_time)
    misconception_penalty = 0.18 if answer.misconception_detected else 0.0
    hint_penalty = min(0.22, hints_used * 0.05)
    confidence = _clamp((answer_quality * 0.7) + (speed_score * 0.3) - misconception_penalty - hint_penalty)
    cognitive_load = _clamp((1 - answer_quality) * 0.6 + (1 - speed_score) * 0.25 + misconception_penalty + hint_penalty)
    mastery_score = _clamp((answer_quality * 0.72) + (confidence * 0.28) - (cognitive_load * 0.12))

    previous_attempts = mastery.total_attempts
    mastery.total_attempts += 1
    if answer_quality >= 0.7 and not answer.misconception_detected:
        mastery.correct_attempts += 1
    if answer.misconception_detected:
        mastery.misconception_count += 1
    mastery.hint_used_count += hints_used

    mastery.last_answer_quality = round(answer_quality, 2)
    mastery.response_speed_score = round(speed_score, 2)
    mastery.confidence_score = round(confidence, 2)
    mastery.cognitive_load_score = round(cognitive_load, 2)
    mastery.hint_dependency = round(mastery.hint_used_count / max(mastery.total_attempts, 1), 2)
    mastery.mastery_level = _moving_average(
        current=mastery.mastery_level,
        incoming=mastery_score,
        previous_attempts=previous_attempts,
    )

    state = build_adaptive_state(concept, mastery)
    mastery.learner_level_label = state.learner_level_label
    mastery.next_difficulty = state.next_difficulty
    mastery.next_question_type = state.next_question_type
    mastery.recommended_strategy = state.recommended_strategy
    mastery.personalized_explanation = state.personalized_explanation
    mastery.last_reviewed_at = utc_now()
    mastery.next_review_at = _next_review_at(mastery.mastery_level, mastery.cognitive_load_score)
    return mastery


def update_mastery_from_self_explanation(
    db: Session,
    concept: Concept,
    score: float,
    user_id: int | None = None,
) -> ConceptMastery:
    mastery = get_or_create_mastery(db, concept)
    if mastery.user_id is None:
        mastery.user_id = user_id
    previous_attempts = mastery.total_attempts
    mastery.total_attempts += 1
    if score >= 0.7:
        mastery.correct_attempts += 1

    mastery.last_answer_quality = round(_clamp(score), 2)
    mastery.confidence_score = round(_clamp((mastery.confidence_score + score) / 2), 2)
    mastery.cognitive_load_score = round(_clamp((mastery.cognitive_load_score + (1 - score)) / 2), 2)
    mastery.mastery_level = _moving_average(
        current=mastery.mastery_level,
        incoming=score,
        previous_attempts=previous_attempts,
    )

    state = build_adaptive_state(concept, mastery)
    mastery.learner_level_label = state.learner_level_label
    mastery.next_difficulty = state.next_difficulty
    mastery.next_question_type = state.next_question_type
    mastery.recommended_strategy = state.recommended_strategy
    mastery.personalized_explanation = state.personalized_explanation
    mastery.last_reviewed_at = utc_now()
    mastery.next_review_at = _next_review_at(mastery.mastery_level, mastery.cognitive_load_score)
    return mastery


def register_hint_use(db: Session, answer: UserAnswer) -> ConceptMastery:
    concept = answer.question.concept
    mastery = get_or_create_mastery(db, concept)
    mastery.hint_used_count += 1
    mastery.hint_dependency = round(mastery.hint_used_count / max(mastery.total_attempts, 1), 2)
    mastery.cognitive_load_score = round(_clamp(mastery.cognitive_load_score + 0.05), 2)

    state = build_adaptive_state(concept, mastery)
    mastery.learner_level_label = state.learner_level_label
    mastery.next_difficulty = state.next_difficulty
    mastery.next_question_type = state.next_question_type
    mastery.recommended_strategy = state.recommended_strategy
    mastery.personalized_explanation = state.personalized_explanation
    mastery.next_review_at = _next_review_at(mastery.mastery_level, mastery.cognitive_load_score)
    return mastery


def get_or_create_mastery(db: Session, concept: Concept) -> ConceptMastery:
    mastery = (
        db.query(ConceptMastery)
        .filter(ConceptMastery.concept_id == concept.id)
        .one_or_none()
    )

    if mastery is None:
        mastery = ConceptMastery(concept_id=concept.id)
        db.add(mastery)
        db.flush()

    return mastery


def build_adaptive_state(concept: Concept, mastery: ConceptMastery) -> AdaptiveLearningState:
    level_label = _level_label(mastery.mastery_level)
    next_difficulty, next_question_type = _next_step(
        mastery.mastery_level,
        mastery.cognitive_load_score,
        mastery.misconception_count,
    )
    strategy = _strategy(level_label, mastery)
    explanation = _personalized_explanation(concept, level_label, mastery)

    return AdaptiveLearningState(
        mastery_level=round(mastery.mastery_level, 2),
        confidence_score=round(mastery.confidence_score, 2),
        cognitive_load_score=round(mastery.cognitive_load_score, 2),
        learner_level_label=level_label,
        next_difficulty=next_difficulty,
        next_question_type=next_question_type,
        recommended_strategy=strategy,
        personalized_explanation=explanation,
        next_review_at=mastery.next_review_at,
    )


def _level_label(mastery_level: float) -> str:
    if mastery_level < 0.2:
        return "초심자"
    if mastery_level < 0.4:
        return "견습생"
    if mastery_level < 0.6:
        return "숙련자"
    if mastery_level < 0.78:
        return "탐구자"
    return "현자"


def _next_step(
    mastery_level: float,
    cognitive_load_score: float,
    misconception_count: int,
) -> tuple[str, str]:
    if misconception_count > 0 and mastery_level < 0.65:
        return "easy", "misconception_check"
    if cognitive_load_score >= 0.68:
        return "easy", "definition"
    if mastery_level < 0.35:
        return "easy", "definition"
    if mastery_level < 0.6:
        return "medium", "cause_effect"
    if mastery_level < 0.8:
        return "medium", "example"
    return "hard", "application"


def _strategy(level_label: str, mastery: ConceptMastery) -> str:
    if mastery.cognitive_load_score >= 0.68:
        return "개념을 더 작은 단위로 나누고 정의형 질문으로 인지 부하를 낮추세요."
    if mastery.misconception_count > 0 and mastery.mastery_level < 0.65:
        return "비슷한 개념과 헷갈린 지점을 먼저 확인한 뒤 짧은 역질문으로 교정하세요."
    if mastery.mastery_level < 0.4:
        return "정답을 보기 전에 핵심 키워드 2개를 먼저 떠올리는 진단 질문을 반복하세요."
    if mastery.mastery_level < 0.7:
        return "원인과 결과를 연결해 말하게 하고, 부족한 부분만 단계적 힌트로 보강하세요."
    if mastery.mastery_level < 0.88:
        return "사용자 자신의 예시를 만들게 한 뒤 다른 개념과의 관계를 비교하게 하세요."
    return "응용 문제와 함정 질문으로 난이도를 올리고 장기 기억을 위한 간격 복습으로 넘기세요."


def _personalized_explanation(
    concept: Concept,
    level_label: str,
    mastery: ConceptMastery,
) -> str:
    base = concept.description.strip() or f"{concept.title}의 핵심 설명을 학습 자료에서 다시 확인하세요."
    if mastery.cognitive_load_score >= 0.68:
        return f"{concept.title}은 지금 한 번에 처리하기엔 부담이 큰 상태입니다. 먼저 핵심만 잡으면, {base[:180]}"
    if mastery.mastery_level < 0.4:
        return f"{concept.title}은 아직 기초 연결이 약합니다. 한 문장으로는 이렇게 잡아보세요: {base[:220]}"
    if mastery.mastery_level < 0.7:
        return f"{concept.title}은 기본 의미는 잡혔습니다. 이제 왜 그런지와 어떤 결과가 생기는지를 이어보세요: {base[:240]}"
    if mastery.mastery_level < 0.88:
        return f"{concept.title}은 설명 가능한 수준입니다. 이제 실제 예시나 비슷한 개념과의 차이를 붙이면 더 강해집니다: {base[:240]}"
    return f"{concept.title}은 응용 단계로 올릴 수 있습니다. 이 개념을 새로운 상황에 적용하고 예외 사례까지 점검해보세요: {base[:240]}"


def _response_speed_score(response_time: float | None) -> float:
    if response_time is None:
        return 0.5
    if response_time <= 20:
        return 1.0
    if response_time <= 45:
        return 0.75
    if response_time <= 90:
        return 0.5
    if response_time <= 180:
        return 0.3
    return 0.15


def _moving_average(current: float, incoming: float, previous_attempts: int) -> float:
    if previous_attempts == 0:
        return round(_clamp(incoming), 2)
    return round(_clamp((current * 0.65) + (incoming * 0.35)), 2)


def _next_review_at(mastery_level: float, cognitive_load_score: float):
    now = utc_now()
    if cognitive_load_score >= 0.68 or mastery_level < 0.35:
        return now + timedelta(hours=6)
    if mastery_level < 0.6:
        return now + timedelta(days=1)
    if mastery_level < 0.82:
        return now + timedelta(days=3)
    return now + timedelta(days=7)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))
