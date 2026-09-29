from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notifications import Notification


ACTIONABLE_NOTIFICATION_TYPES = {
    "assessment_in_progress",
    "assessment_review_required",
    "recommendation_review_required",
    "report_review_required",
    "clinician_review_pending",
}


def create_notification(
    db: Session,
    *,
    patient_id: int,
    assessment_id: int | None,
    record_id: int | None,
    notification_type: str,
    priority: str,
    title: str,
    message: str,
    source: str | None = None,
) -> Notification:

    existing = db.scalar(
        select(Notification)
        .where(
            Notification.patient_id == patient_id,
            Notification.assessment_id == assessment_id,
            Notification.record_id == record_id,
            Notification.notification_type
            == notification_type,
            Notification.is_read.is_(False),
        )
        .order_by(
            Notification.created_at.desc()
        )
    )

    if existing is not None:
        return existing

    notification = Notification(
        patient_id=patient_id,
        assessment_id=assessment_id,
        record_id=record_id,
        notification_type=notification_type,
        priority=priority,
        title=title,
        message=message,
        source=source,
        is_read=False,
        created_at=datetime.now(timezone.utc),
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

    return notification


def reconcile_patient_notifications(
    db: Session,
    *,
    patient_id: int,
    generated_notifications: list[dict[str, Any]],
) -> int:
    """
    Resolve unread persistent notifications that are no longer
    present in the current notification intelligence output.

    Resolved notifications remain in the database for history.
    """

    current_keys = {
        (
            item.get("notification_type"),
            item.get("assessment_id"),
            item.get("record_id"),
        )
        for item in generated_notifications
    }

    existing_notifications = list(
        db.scalars(
            select(Notification)
            .where(
                Notification.patient_id == patient_id,
                Notification.is_read.is_(False),
                Notification.notification_type.in_(
                    ACTIONABLE_NOTIFICATION_TYPES
                ),
            )
        ).all()
    )

    now = datetime.now(timezone.utc)
    resolved_count = 0

    for notification in existing_notifications:
        notification_key = (
            notification.notification_type,
            notification.assessment_id,
            notification.record_id,
        )

        if notification_key not in current_keys:
            notification.is_read = True
            notification.read_at = now
            resolved_count += 1

    if resolved_count:
        db.commit()

    return resolved_count


def synchronize_patient_notifications(
    db: Session,
    *,
    patient_id: int,
    generated_notifications: list[dict[str, Any]],
) -> dict[str, Any]:

    resolved_count = reconcile_patient_notifications(
        db=db,
        patient_id=patient_id,
        generated_notifications=generated_notifications,
    )

    created_notifications: list[Notification] = []
    existing_notifications: list[Notification] = []

    for item in generated_notifications:

        notification_type = item.get(
            "notification_type",
            "general",
        )

        assessment_id = item.get(
            "assessment_id"
        )

        record_id = item.get(
            "record_id"
        )

        existing = db.scalar(
            select(Notification)
            .where(
                Notification.patient_id == patient_id,
                Notification.assessment_id == assessment_id,
                Notification.record_id == record_id,
                Notification.notification_type == notification_type,
                Notification.is_read.is_(False),
            )
            .order_by(
                Notification.created_at.desc()
            )
        )

        if existing is not None:
            existing_notifications.append(existing)
            continue

        notification = Notification(
            patient_id=patient_id,
            assessment_id=assessment_id,
            record_id=record_id,
            notification_type=notification_type,
            priority=item.get(
                "priority",
                "medium",
            ),
            title=item.get(
                "title",
                "Patient notification",
            ),
            message=item.get(
                "message",
                "",
            ),
            source=item.get(
                "source",
                "patient_notification_engine",
            ),
            is_read=False,
            created_at=datetime.now(timezone.utc),
        )

        db.add(notification)
        created_notifications.append(notification)

    db.commit()

    for notification in created_notifications:
        db.refresh(notification)

    return {
        "patient_id": patient_id,
        "generated_count": len(
            generated_notifications
        ),
        "created_count": len(
            created_notifications
        ),
        "existing_count": len(
            existing_notifications
        ),
        "resolved_count": resolved_count,
        "created": [
            serialize_notification(
                notification
            )
            for notification in created_notifications
        ],
    }


def mark_notification_as_read(
    db: Session,
    notification: Notification,
) -> Notification:

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(
            timezone.utc
        )

        db.commit()
        db.refresh(notification)

    return notification


def mark_all_patient_notifications_as_read(
    db: Session,
    patient_id: int,
) -> int:

    notifications = list(
        db.scalars(
            select(Notification)
            .where(
                Notification.patient_id == patient_id,
                Notification.is_read.is_(False),
            )
        ).all()
    )

    now = datetime.now(timezone.utc)

    for notification in notifications:
        notification.is_read = True
        notification.read_at = now

    db.commit()

    return len(notifications)


def serialize_notification(
    notification: Notification,
) -> dict[str, Any]:

    return {
        "id": notification.id,
        "patient_id": notification.patient_id,
        "assessment_id": notification.assessment_id,
        "record_id": notification.record_id,
        "notification_type": (
            notification.notification_type
        ),
        "priority": notification.priority,
        "title": notification.title,
        "message": notification.message,
        "source": notification.source,
        "is_read": notification.is_read,
        "created_at": (
            notification.created_at.isoformat()
            if notification.created_at
            else None
        ),
        "read_at": (
            notification.read_at.isoformat()
            if notification.read_at
            else None
        ),
    }