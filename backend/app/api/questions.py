from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_current_user, get_db
from app.models.learning import Concept, User
from app.schemas.questions import QuestionGenerationResponse
from app.services.llm_provider import get_llm_provider
from app.services.ownership_service import ensure_concept_owner
from app.services.question_service import generate_and_store_questions

router = APIRouter()


@router.post(
    "/concepts/{concept_id}/questions/generate",
    response_model=QuestionGenerationResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_questions(
    concept_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QuestionGenerationResponse:
    concept = db.get(Concept, concept_id)
    if concept is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="개념을 찾을 수 없습니다.",
        )
    ensure_concept_owner(concept, current_user)

    provider = get_llm_provider()

    try:
        source, questions = generate_and_store_questions(db, concept, provider)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return QuestionGenerationResponse(
        concept_id=concept.id,
        source=source,
        count=len(questions),
        questions=questions,
    )
