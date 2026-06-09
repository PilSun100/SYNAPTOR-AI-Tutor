from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_current_user, get_db
from app.models.learning import LearningMaterial, User
from app.schemas.concepts import ConceptExtractionResponse
from app.services.concept_service import extract_and_store_concepts
from app.services.llm_provider import get_llm_provider
from app.services.ownership_service import ensure_material_owner

router = APIRouter()


@router.post(
    "/materials/{material_id}/concepts/extract",
    response_model=ConceptExtractionResponse,
    status_code=status.HTTP_201_CREATED,
)
def extract_concepts(
    material_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConceptExtractionResponse:
    material = db.get(LearningMaterial, material_id)
    if material is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="학습 자료를 찾을 수 없습니다.",
        )
    ensure_material_owner(material, current_user)

    provider = get_llm_provider()

    try:
        source, concepts = extract_and_store_concepts(db, material, provider)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return ConceptExtractionResponse(
        material_id=material.id,
        source=source,
        count=len(concepts),
        concepts=concepts,
    )
