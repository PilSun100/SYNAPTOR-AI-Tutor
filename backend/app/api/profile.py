from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.dependencies import get_current_user, get_db
from app.models.learning import User
from app.schemas.profile import LearningProfileResponse
from app.services.learning_profile_service import build_learning_profile_response

router = APIRouter()


@router.get("/profile/learning", response_model=LearningProfileResponse)
def get_learning_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LearningProfileResponse:
    return build_learning_profile_response(db, current_user.id)
