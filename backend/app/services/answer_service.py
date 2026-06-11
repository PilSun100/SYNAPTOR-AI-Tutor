from sqlalchemy.orm import Session

from app.models.learning import HintLog, LearningSession, MaterialMastery, Question, User, UserAnswer
from app.services.adaptive_learning_service import AdaptiveLearningState, build_adaptive_state, update_mastery_from_answer
from app.services.llm_provider import EvaluatedAnswer, LLMProvider
from app.services.learning_profile_service import update_learning_profile
from app.services.retrieval_service import (
    RetrievedChunk,
    format_evidence_context,
    log_evidence,
    retrieve_chunks_for_answer,
)
from app.services.tier_service import (
    apply_concept_score,
    concept_score,
    hint_budget_for_difficulty,
    is_low_information_answer,
    update_material_mastery,
)


def evaluate_and_store_answer(
    db: Session,
    question: Question,
    answer_text: str,
    provider: LLMProvider,
    user: User,
    session_id: int | None = None,
    response_time: float | None = None,
) -> tuple[
    str,
    UserAnswer,
    str,
    AdaptiveLearningState,
    list[RetrievedChunk],
    int,
    int,
    float,
    str,
    MaterialMastery | None,
]:
    session = _resolve_session(db, question, user, session_id)
    evidence_chunks = retrieve_chunks_for_answer(db, question.id, answer_text)
    if is_low_information_answer(answer_text):
        evaluation = EvaluatedAnswer(
            correctness_score=0.0,
            missing_points="의미 있는 개념 설명이 필요합니다.",
            misconception_detected=True,
            feedback=(
                "의미 있는 개념 설명이 필요합니다. "
                "아직 평가할 만한 학습 답변이 충분하지 않습니다. "
                "자료 근거를 떠올려 핵심 개념, 관계, 이유를 한두 문장으로 설명해보세요."
            ),
        )
    else:
        evaluation = provider.evaluate_answer(
            question_text=question.question_text,
            expected_answer=question.expected_answer,
            answer_text=answer_text,
            evidence_context=format_evidence_context(evidence_chunks),
        )

    user_answer = UserAnswer(
        session_id=session.id,
        question_id=question.id,
        answer_text=answer_text,
        correctness_score=evaluation.correctness_score,
        missing_points=evaluation.missing_points,
        misconception_detected=evaluation.misconception_detected,
        response_time=response_time,
    )

    db.add(user_answer)
    db.flush()
    hints_used = _attach_pre_answer_hints(db, user_answer)
    log_evidence(
        db,
        evidence_chunks,
        purpose="answer_evaluation",
        related_question_id=question.id,
        related_answer_id=user_answer.id,
    )
    mastery = update_mastery_from_answer(db, user_answer, hints_used=hints_used)
    score = concept_score(user_answer, hints_used)
    apply_concept_score(mastery, score)
    adaptive_state = build_adaptive_state(question.concept, mastery)
    material_mastery = update_material_mastery(db, session)
    update_learning_profile(db, user.id)
    db.commit()
    db.refresh(user_answer)
    if material_mastery is not None:
        db.refresh(material_mastery)

    return (
        provider.source,
        user_answer,
        evaluation.feedback,
        adaptive_state,
        evidence_chunks,
        hints_used,
        hint_budget_for_difficulty(question.concept.difficulty),
        score,
        mastery.tier_name,
        material_mastery,
    )


def _resolve_session(
    db: Session,
    question: Question,
    user: User,
    session_id: int | None,
) -> LearningSession:
    if session_id is not None:
        session = db.get(LearningSession, session_id)
        if session is not None and session.user_id == user.id:
            return session

    material_id = question.concept.material_id
    session = LearningSession(material_id=material_id, user_id=user.id)
    db.add(session)
    db.flush()
    return session


def _attach_pre_answer_hints(db: Session, user_answer: UserAnswer) -> int:
    hints = (
        db.query(HintLog)
        .filter(
            HintLog.session_id == user_answer.session_id,
            HintLog.question_id == user_answer.question_id,
            HintLog.user_answer_id.is_(None),
        )
        .all()
    )
    for hint in hints:
        hint.user_answer_id = user_answer.id
    return len(hints)
