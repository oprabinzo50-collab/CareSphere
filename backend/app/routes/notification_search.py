from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
)
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User
from app.security.permissions import require_roles
from app.services.notification_intelligence_audit import (
    record_notification_intelligence_audit,
)
from app.services.notification_search import (
    search_patient_notifications,
)


router = APIRouter(
    prefix="/patients",
    tags=["Notification Search"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get(
    "/{patient_id}/notification-search"
)
def search_notifications(
    patient_id: int,
    request: Request,
    search: str | None = Query(
        default=None
    ),
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
        result = search_patient_notifications(
            db=db,
            patient_id=patient_id,
            search=search,
            notification_type=(
                notification_type
            ),
            priority=priority,
            is_read=is_read,
            escalation_level=(
                escalation_level
            ),
            limit=limit,
            offset=offset,
        )

        pagination = result.get(
            "pagination",
            {},
        )

        record_notification_intelligence_audit(
            db=db,
            user_id=current_user.id,
            patient_id=patient_id,
            action=(
                "notification_intelligence_search"
            ),
            description=(
                "Notification intelligence "
                "search performed"
            ),
            metadata={
                "search": search,
                "notification_type": (
                    notification_type
                ),
                "priority": priority,
                "is_read": is_read,
                "escalation_level": (
                    escalation_level
                ),
                "limit": limit,
                "offset": offset,
                "total_count": pagination.get(
                    "total_count",
                    0,
                ),
                "returned_count": pagination.get(
                    "returned_count",
                    0,
                ),
            },
            ip_address=(
                request.client.host
                if request.client
                else None
            ),
            user_agent=request.headers.get(
                "user-agent"
            ),
        )

        return result

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )