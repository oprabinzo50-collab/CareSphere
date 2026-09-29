from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.notifications import Notification
from app.models.patient import Patient
from app.models.user import User
from app.security.permissions import require_roles
from app.services.notification_persistence import (
    mark_all_patient_notifications_as_read,
    mark_notification_as_read,
    serialize_notification,
)
from app.services.notification_sync import (
    synchronize_patient_notification_inbox,
)


router = APIRouter(
    prefix="/patients",
    tags=["Notifications"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post(
    "/{patient_id}/notifications/synchronize"
)
def synchronize_notifications(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("administrator", "clinician")),
):
    patient = db.get(
        Patient,
        patient_id,
    )

    if patient is None:
        raise HTTPException(
            status_code=404,
            detail="Patient not found",
        )

    return synchronize_patient_notification_inbox(
        db=db,
        patient_id=patient_id,
    )


@router.get(
    "/{patient_id}/notifications/persistent"
)
def get_persistent_notifications(
    patient_id: int,
    unread_only: bool = Query(
        default=False
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
    patient = db.get(
        Patient,
        patient_id,
    )

    if patient is None:
        raise HTTPException(
            status_code=404,
            detail="Patient not found",
        )

    base_filter = [
        Notification.patient_id == patient_id
    ]

    if unread_only:
        base_filter.append(
            Notification.is_read.is_(False)
        )

    total_count = db.scalar(
        select(
            func.count(Notification.id)
        ).where(
            *base_filter
        )
    ) or 0

    unread_count = db.scalar(
        select(
            func.count(Notification.id)
        ).where(
            Notification.patient_id == patient_id,
            Notification.is_read.is_(False),
        )
    ) or 0

    notifications = list(
        db.scalars(
            select(Notification)
            .where(*base_filter)
            .order_by(
                Notification.created_at.desc()
            )
            .offset(offset)
            .limit(limit)
        ).all()
    )

    return {
        "patient_id": patient_id,
        "total_count": total_count,
        "unread_count": unread_count,
        "limit": limit,
        "offset": offset,
        "returned_count": len(
            notifications
        ),
        "notifications": [
            serialize_notification(
                notification
            )
            for notification in notifications
        ],
    }


@router.put(
    "/notifications/{notification_id}/read"
)
def read_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("administrator", "clinician")),
):
    notification = db.get(
        Notification,
        notification_id,
    )

    if notification is None:
        raise HTTPException(
            status_code=404,
            detail="Notification not found",
        )

    notification = mark_notification_as_read(
        db=db,
        notification=notification,
    )

    return {
        "message": "Notification marked as read",
        "notification": serialize_notification(
            notification
        ),
    }


@router.put(
    "/{patient_id}/notifications/read-all"
)
def read_all_notifications(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("administrator", "clinician")),
):
    patient = db.get(
        Patient,
        patient_id,
    )

    if patient is None:
        raise HTTPException(
            status_code=404,
            detail="Patient not found",
        )

    count = mark_all_patient_notifications_as_read(
        db=db,
        patient_id=patient_id,
    )

    return {
        "patient_id": patient_id,
        "message": (
            "Patient notifications marked as read"
        ),
        "updated_count": count,
    }