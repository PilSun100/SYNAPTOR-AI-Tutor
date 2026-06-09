from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.learning import HintLog, UserAnswer
from app.services.adaptive_learning_service import register_hint_use
from app.services.llm_provider import LLMProvider
from app.services.retrieval_service import (
    RetrievedChunk,
    format_evidence_context,
    log_evidence,
    retrieve_chunks_for_answer,
)


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
    evidence_chunks = retrieve_chunks_for_answer(db, question.id, user_answer.answer_text)
    hint = provider.generate_hint(
        question_text=question.question_text,
        expected_answer=question.expected_answer,
        answer_text=user_answer.answer_text,
        missing_points=user_answer.missing_points,
        hint_level=hint_level,
        evidence_context=format_evidence_context(evidence_chunks),
    )

    if not hint.hint_text:
        raise ValueError("생성된 힌트가 없습니다.")

    hint_log = HintLog(
        user_answer_id=user_answer.id,
        hint_level=hint_level,
        hint_text=hint.hint_text,
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
    db.commit()
    db.refresh(hint_log)

    return provider.source, hint_log, evidence_chunks
