from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_current_user, get_db
from app.models.learning import LearningMaterial, User
from app.schemas.tutor_chat import TutorChatRequest, TutorChatResponse
from app.services.llm_provider import get_llm_provider
from app.services.ownership_service import ensure_material_owner
from app.services.retrieval_service import evidence_snippets
from app.services.tutor_chat_service import generate_material_chat_reply

router = APIRouter()


@router.post("/materials/{material_id}/chat", response_model=TutorChatResponse)
def chat_with_material(
    material_id: int,
    payload: TutorChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TutorChatResponse:
    material = db.get(LearningMaterial, material_id)
    if material is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="학습 자료를 찾을 수 없습니다.",
        )
    ensure_material_owner(material, current_user)

    provider = get_llm_provider()

    try:
        reply, learning_mode, next_action, suggested_questions, evidence_chunks = generate_material_chat_reply(
            db=db,
            material=material,
            message=payload.message,
            provider=provider,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return TutorChatResponse(
        material_id=material.id,
        reply=reply,
        learning_mode=learning_mode,
        next_action=next_action,
        suggested_questions=suggested_questions,
        evidence=evidence_snippets(evidence_chunks),
        source=provider.source,
    )
