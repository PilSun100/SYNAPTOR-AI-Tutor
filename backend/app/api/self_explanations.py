from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.learning import Concept
from app.schemas.self_explanations import SelfExplanationRequest, SelfExplanationResponse
from app.services.adaptive_learning_service import build_adaptive_state
from app.services.llm_provider import get_llm_provider
from app.services.self_explanation_service import evaluate_and_store_self_explanation

router = APIRouter()


@router.post(
    "/concepts/{concept_id}/self-explanation",
    response_model=SelfExplanationResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_self_explanation(
    concept_id: int,
    payload: SelfExplanationRequest,
    db: Session = Depends(get_db),
) -> SelfExplanationResponse:
    concept = db.get(Concept, concept_id)
    if concept is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="개념을 찾을 수 없습니다.",
        )

    provider = get_llm_provider()

    try:
        source, self_explanation, mastery, feedback = evaluate_and_store_self_explanation(
            db=db,
            concept=concept,
            explanation_text=payload.explanation_text,
            provider=provider,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return SelfExplanationResponse(
        id=self_explanation.id,
        concept_id=self_explanation.concept_id,
        explanation_text=self_explanation.explanation_text,
        accuracy_score=self_explanation.accuracy_score,
        completeness_score=self_explanation.completeness_score,
        logical_connection_score=self_explanation.logical_connection_score,
        mastery_level=mastery.mastery_level,
        next_review_at=mastery.next_review_at,
        feedback=feedback,
        adaptive_state=asdict(build_adaptive_state(concept, mastery)),
        source=source,
        created_at=self_explanation.created_at,
    )
