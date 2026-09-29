from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User
from app.security.permissions import require_roles
from app.services.notification_analytics import (
    generate_patient_notification_analytics,
)


router = APIRouter(
    prefix="/patients",
    tags=["Notification Analytics"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get(
    "/{patient_id}/notification-analytics"
)
def get_patient_notification_analytics(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("administrator", "clinician")),
):
    try:
        return generate_patient_notification_analytics(
            db=db,
            patient_id=patient_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )