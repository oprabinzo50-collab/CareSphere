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
from app.services.notification_reporting import (
    generate_patient_notification_report,
)


router = APIRouter(
    prefix="/patients",
    tags=["Notification Reporting"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get(
    "/{patient_id}/notification-report"
)
def get_patient_notification_report(
    patient_id: int,
    request: Request,
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
        result = generate_patient_notification_report(
            db=db,
            patient_id=patient_id,
            days=days,
            dashboard_limit=dashboard_limit,
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

        overview = result.get(
            "overview",
            {}
        )

        search_data = result.get(
            "search",
            {}
        )

        search_pagination = search_data.get(
            "pagination",
            {}
        )

        record_notification_intelligence_audit(
            db=db,
            user_id=current_user.id,
            patient_id=patient_id,
            action=(
                "notification_intelligence_report"
            ),
            description=(
                "Notification intelligence "
                "report generated"
            ),
            metadata={
                "days": days,
                "dashboard_limit": (
                    dashboard_limit
                ),
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
                "total_notifications": (
                    overview.get(
                        "total_notifications",
                        0,
                    )
                ),
                "unread_notifications": (
                    overview.get(
                        "unread_notifications",
                        0,
                    )
                ),
                "search_total_count": (
                    search_pagination.get(
                        "total_count",
                        0,
                    )
                ),
                "report_status": (
                    result.get(
                        "report",
                        {},
                    ).get(
                        "report_status"
                    )
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