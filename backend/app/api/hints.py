from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.learning import UserAnswer
from app.schemas.hints import HintRequest, HintResponse
from app.services.hint_service import generate_and_store_hint
from app.services.llm_provider import get_llm_provider
from app.services.retrieval_service import evidence_snippets

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
) -> HintResponse:
    user_answer = db.get(UserAnswer, answer_id)
    if user_answer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자 답변을 찾을 수 없습니다.",
        )

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
        hint_level=hint_log.hint_level,
        hint_text=hint_log.hint_text,
        evidence=evidence_snippets(evidence_chunks),
        source=source,
        created_at=hint_log.created_at,
    )
