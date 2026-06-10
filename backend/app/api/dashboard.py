from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.dependencies import get_current_user, get_db
from app.models.learning import User
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.dashboard_service import build_dashboard_summary

router = APIRouter()


@router.get("/dashboard/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardSummaryResponse:
    return build_dashboard_summary(db, current_user.id)
