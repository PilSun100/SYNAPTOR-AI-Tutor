from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.learning import LearningSession
from app.schemas.reports import SessionReportResponse
from app.services.report_service import build_session_report

router = APIRouter()


@router.get(
    "/sessions/{session_id}/report",
    response_model=SessionReportResponse,
)
def get_session_report(
    session_id: int,
    db: Session = Depends(get_db),
) -> SessionReportResponse:
    session = db.get(LearningSession, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="학습 세션을 찾을 수 없습니다.",
        )

    return build_session_report(session)
