from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.learning import HintLog, LearningSession, Question, User, UserAnswer
from app.services.adaptive_learning_service import register_hint_use
from app.services.evidence_hint_service import build_evidence_hint
from app.services.learning_profile_service import update_learning_profile
from app.services.llm_provider import LLMProvider
from app.services.retrieval_service import (
    RetrievedChunk,
    log_evidence,
    retrieve_chunks_for_answer,
    retrieve_chunks_for_question,
)
from app.services.tier_service import hint_budget_for_difficulty


def generate_and_store_hint(
    db: Session,
    user_answer: UserAnswer,
    hint_level: int,
    provider: LLMProvider,
) -> tuple[str, HintLog, list[RetrievedChunk]]:
    if hint_level < 1 or hint_level > 5:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="힌트 레벨은 1부터 5 사이여야 합니다.",
        )

    question = user_answer.question
    hint_budget = hint_budget_for_difficulty(question.concept.difficulty)
    if hint_level > hint_budget:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"이 개념은 최대 {hint_budget}개의 힌트만 사용할 수 있습니다.",
        )
    evidence_chunks = retrieve_chunks_for_answer(db, question.id, user_answer.answer_text)
    hint_text = build_evidence_hint(question, evidence_chunks, hint_level)
    if not hint_text:
        hint = provider.generate_hint(
            question_text=question.question_text,
            expected_answer=question.expected_answer,
            answer_text=user_answer.answer_text,
            missing_points=user_answer.missing_points,
            hint_level=hint_level,
            evidence_context=format_evidence_context(evidence_chunks),
        )
        hint_text = hint.hint_text

    if not hint_text:
        raise ValueError("생성된 힌트가 없습니다.")

    hint_log = HintLog(
        user_answer_id=user_answer.id,
        session_id=user_answer.session_id,
        question_id=question.id,
        concept_id=question.concept_id,
        user_id=user_answer.session.user_id,
        hint_level=hint_level,
        hint_text=hint_text,
    )
    db.add(hint_log)
    db.flush()
    log_evidence(
        db,
        evidence_chunks,
        purpose="hint_generation",
        related_question_id=question.id,
        related_answer_id=user_answer.id,
    )
    register_hint_use(db, user_answer)
    update_learning_profile(db, user_answer.session.user_id)
    db.commit()
    db.refresh(hint_log)

    return "rag", hint_log, evidence_chunks


def generate_and_store_question_hint(
    db: Session,
    question: Question,
    session: LearningSession,
    user: User,
    hint_level: int,
    provider: LLMProvider,
    stuck_reason: str | None = None,
) -> tuple[str, HintLog, list[RetrievedChunk], int, int]:
    hint_budget = hint_budget_for_difficulty(question.concept.difficulty)
    existing_count = (
        db.query(HintLog)
        .filter(
            HintLog.session_id == session.id,
            HintLog.question_id == question.id,
        )
        .count()
    )
    if hint_level < 1 or hint_level > hint_budget:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"이 개념은 최대 {hint_budget}개의 힌트만 사용할 수 있습니다.",
        )
    if existing_count >= hint_budget:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="이 개념의 힌트를 모두 사용했습니다.",
        )
    if hint_level != existing_count + 1:
        hint_level = existing_count + 1

    evidence_chunks = retrieve_chunks_for_question(db, question.id)
    answer_context = _stuck_context(stuck_reason)
    hint_text = build_evidence_hint(question, evidence_chunks, hint_level, stuck_reason)
    if not hint_text:
        hint = provider.generate_hint(
            question_text=question.question_text,
            expected_answer=question.expected_answer,
            answer_text=answer_context,
            missing_points=answer_context,
            hint_level=hint_level,
            evidence_context=format_evidence_context(evidence_chunks),
        )
        hint_text = hint.hint_text

    if not hint_text:
        raise ValueError("생성된 힌트가 없습니다.")

    hint_log = HintLog(
        session_id=session.id,
        question_id=question.id,
        concept_id=question.concept_id,
        user_id=user.id,
        hint_level=hint_level,
        hint_text=hint_text,
        stuck_reason=stuck_reason,
    )
    db.add(hint_log)
    db.flush()
    log_evidence(
        db,
        evidence_chunks,
        purpose="pre_answer_hint_generation",
        related_question_id=question.id,
    )
    db.commit()
    db.refresh(hint_log)

    return "rag", hint_log, evidence_chunks, hint_budget, existing_count + 1


def _stuck_context(stuck_reason: str | None) -> str:
    if not stuck_reason:
        return "사용자는 아직 답변 전이며 작은 단계적 힌트를 요청했습니다."
    reason_map = {
        "forgot_word": "사용자는 핵심 단어가 기억나지 않는다고 했습니다. 키워드 단서 중심으로 도와주세요.",
        "cannot_explain": "사용자는 개념은 알지만 설명이 어렵다고 했습니다. 문장 시작이나 설명 구조를 주세요.",
        "confusing_concepts": "사용자는 두 개념을 헷갈린다고 했습니다. 비교 기준을 주세요.",
        "question_unclear": "사용자는 질문이 이해되지 않는다고 했습니다. 질문을 더 쉬운 하위 질문으로 바꿔주세요.",
    }
    return reason_map.get(stuck_reason, f"사용자가 막힌 이유: {stuck_reason}")
