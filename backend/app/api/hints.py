from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_current_user, get_db
from app.models.learning import HintLog, LearningSession, Question, User, UserAnswer
from app.schemas.hints import HintRequest, HintResponse
from app.services.hint_service import generate_and_store_hint, generate_and_store_question_hint
from app.services.llm_provider import get_llm_provider
from app.services.ownership_service import ensure_answer_owner, ensure_question_owner, ensure_session_owner
from app.services.retrieval_service import evidence_snippets
from app.services.tier_service import hint_budget_for_difficulty

router = APIRouter()


@router.post(
    "/answers/{answer_id}/hint",
    response_model=HintResponse,
    status_code=status.HTTP_201_CREATED,
)
def request_hint(
    answer_id: int,
    payload: HintRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HintResponse:
    user_answer = db.get(UserAnswer, answer_id)
    if user_answer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자 답변을 찾을 수 없습니다.",
        )
    ensure_answer_owner(user_answer, current_user)

    provider = get_llm_provider()

    try:
        source, hint_log, evidence_chunks = generate_and_store_hint(
            db=db,
            user_answer=user_answer,
            hint_level=payload.hint_level,
            provider=provider,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return HintResponse(
        id=hint_log.id,
        user_answer_id=hint_log.user_answer_id,
        session_id=hint_log.session_id,
        question_id=hint_log.question_id,
        concept_id=hint_log.concept_id,
        hint_level=hint_log.hint_level,
        hint_budget=hint_budget_for_difficulty(user_answer.question.concept.difficulty),
        hints_used=db.query(HintLog).filter(HintLog.user_answer_id == user_answer.id).count(),
        hint_text=hint_log.hint_text,
        stuck_reason=hint_log.stuck_reason,
        evidence=evidence_snippets(evidence_chunks),
        source=source,
        created_at=hint_log.created_at,
    )


@router.post(
    "/questions/{question_id}/hint",
    response_model=HintResponse,
    status_code=status.HTTP_201_CREATED,
)
def request_question_hint(
    question_id: int,
    payload: HintRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HintResponse:
    question = db.get(Question, question_id)
    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="질문을 찾을 수 없습니다.",
        )
    ensure_question_owner(question, current_user)
    if payload.session_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="세션 정보가 필요합니다.",
        )
    session = db.get(LearningSession, payload.session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="학습 세션을 찾을 수 없습니다.",
        )
    ensure_session_owner(session, current_user)

    provider = get_llm_provider()

    try:
        source, hint_log, evidence_chunks, hint_budget, hints_used = generate_and_store_question_hint(
            db=db,
            question=question,
            session=session,
            user=current_user,
            hint_level=payload.hint_level,
            provider=provider,
            stuck_reason=payload.stuck_reason,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return HintResponse(
        id=hint_log.id,
        user_answer_id=hint_log.user_answer_id,
        session_id=hint_log.session_id,
        question_id=hint_log.question_id,
        concept_id=hint_log.concept_id,
        hint_level=hint_log.hint_level,
        hint_budget=hint_budget,
        hints_used=hints_used,
        hint_text=hint_log.hint_text,
        stuck_reason=hint_log.stuck_reason,
        evidence=evidence_snippets(evidence_chunks),
        source=source,
        created_at=hint_log.created_at,
    )
