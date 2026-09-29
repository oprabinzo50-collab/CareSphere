from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User
from app.security.dependencies import (
    require_administrator,
)
from app.services.notification_intelligence import (
    generate_patient_notification_intelligence,
)


router = APIRouter(
    prefix="/patients",
    tags=["Notification Intelligence"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get(
    "/{patient_id}/notification-intelligence"
)
def get_patient_notification_intelligence(
    patient_id: int,
    days: int = Query(
        default=30,
        ge=1,
        le=365,
    ),
    dashboard_limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_administrator
    ),
):
    try:
        return (
            generate_patient_notification_intelligence(
                db=db,
                patient_id=patient_id,
                days=days,
                dashboard_limit=dashboard_limit,
            )
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )