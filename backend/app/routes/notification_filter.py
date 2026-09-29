from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User
from app.security.permissions import require_roles
from app.services.notification_filter import (
    generate_filtered_patient_notifications,
)


router = APIRouter(
    prefix="/patients",
    tags=["Notification Filtering"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get(
    "/{patient_id}/notification-filter"
)
def filter_patient_notifications(
    patient_id: int,
    notification_type: str | None = Query(
        default=None
    ),
    priority: str | None = Query(
        default=None
    ),
    is_read: bool | None = Query(
        default=None
    ),
    escalation_level: str | None = Query(
        default=None
    ),
    from_date: str | None = Query(
        default=None
    ),
    to_date: str | None = Query(
        default=None
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("administrator", "clinician")),
):
    try:
        return (
            generate_filtered_patient_notifications(
                db=db,
                patient_id=patient_id,
                notification_type=(
                    notification_type
                ),
                priority=priority,
                is_read=is_read,
                escalation_level=(
                    escalation_level
                ),
                from_date=from_date,
                to_date=to_date,
                limit=limit,
                offset=offset,
            )
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )