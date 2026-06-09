from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.learning import Question
from app.schemas.answers import AnswerEvaluationResponse, AnswerSubmitRequest
from app.services.answer_service import evaluate_and_store_answer
from app.services.llm_provider import get_llm_provider
from app.services.retrieval_service import evidence_snippets

router = APIRouter()


@router.post(
    "/questions/{question_id}/answer",
    response_model=AnswerEvaluationResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_answer(
    question_id: int,
    payload: AnswerSubmitRequest,
    db: Session = Depends(get_db),
) -> AnswerEvaluationResponse:
    question = db.get(Question, question_id)
    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="질문을 찾을 수 없습니다.",
        )

    provider = get_llm_provider()

    try:
        source, user_answer, feedback, adaptive_state, evidence_chunks = evaluate_and_store_answer(
            db=db,
            question=question,
            answer_text=payload.answer_text,
            provider=provider,
            session_id=payload.session_id,
            response_time=payload.response_time,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return AnswerEvaluationResponse(
        id=user_answer.id,
        session_id=user_answer.session_id,
        question_id=user_answer.question_id,
        answer_text=user_answer.answer_text,
        correctness_score=user_answer.correctness_score,
        missing_points=user_answer.missing_points,
        misconception_detected=user_answer.misconception_detected,
        response_time=user_answer.response_time,
        feedback=feedback,
        adaptive_state=asdict(adaptive_state),
        evidence=evidence_snippets(evidence_chunks),
        source=source,
        created_at=user_answer.created_at,
    )
