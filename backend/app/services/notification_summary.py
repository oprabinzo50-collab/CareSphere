from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notifications import Notification
from app.models.patient import Patient


def generate_patient_notification_summary(
    db: Session,
    patient_id: int,
) -> dict[str, Any]:

    patient = db.get(
        Patient,
        patient_id,
    )

    if patient is None:
        raise ValueError("Patient not found")

    notifications = list(
        db.scalars(
            select(Notification)
            .where(
                Notification.patient_id == patient_id
            )
            .order_by(
                Notification.created_at.desc()
            )
        ).all()
    )

    priority_counts = {
        "high": 0,
        "medium": 0,
        "low": 0,
    }

    unread_priority_counts = {
        "high": 0,
        "medium": 0,
        "low": 0,
    }

    type_counts: dict[str, int] = {}

    unread_type_counts: dict[str, int] = {}

    for notification in notifications:

        priority = str(
            notification.priority
        ).lower()

        if priority not in priority_counts:
            priority_counts[priority] = 0

        priority_counts[priority] += 1

        notification_type = (
            notification.notification_type
        )

        type_counts[notification_type] = (
            type_counts.get(
                notification_type,
                0,
            )
            + 1
        )

        if not notification.is_read:

            if priority not in unread_priority_counts:
                unread_priority_counts[
                    priority
                ] = 0

            unread_priority_counts[
                priority
            ] += 1

            unread_type_counts[
                notification_type
            ] = (
                unread_type_counts.get(
                    notification_type,
                    0,
                )
                + 1
            )

    unread_notifications = [
        notification
        for notification in notifications
        if not notification.is_read
    ]

    high_priority_unread = [
        notification
        for notification in unread_notifications
        if str(
            notification.priority
        ).lower()
        == "high"
    ]

    if high_priority_unread:
        summary_status = "high_priority_attention"

    elif unread_notifications:
        summary_status = "unread_notifications"

    elif notifications:
        summary_status = "all_notifications_read"

    else:
        summary_status = "no_notifications"

    latest_notification = (
        notifications[0]
        if notifications
        else None
    )

    latest_unread_notification = (
        unread_notifications[0]
        if unread_notifications
        else None
    )

    return {
        "patient": {
            "id": patient.id,
            "patient_number": (
                patient.patient_number
            ),
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "status": patient.status,
        },

        "summary_status": summary_status,

        "counts": {
            "total": len(notifications),
            "unread": len(
                unread_notifications
            ),
            "read": (
                len(notifications)
                - len(unread_notifications)
            ),
            "high_priority": priority_counts.get(
                "high",
                0,
            ),
            "medium_priority": priority_counts.get(
                "medium",
                0,
            ),
            "low_priority": priority_counts.get(
                "low",
                0,
            ),
            "unread_high_priority": (
                unread_priority_counts.get(
                    "high",
                    0,
                )
            ),
            "unread_medium_priority": (
                unread_priority_counts.get(
                    "medium",
                    0,
                )
            ),
            "unread_low_priority": (
                unread_priority_counts.get(
                    "low",
                    0,
                )
            ),
        },

        "priority_counts": priority_counts,

        "unread_priority_counts": (
            unread_priority_counts
        ),

        "notification_type_counts": (
            type_counts
        ),

        "unread_notification_type_counts": (
            unread_type_counts
        ),

        "latest_notification": (
            serialize_notification(
                latest_notification
            )
            if latest_notification
            else None
        ),

        "latest_unread_notification": (
            serialize_notification(
                latest_unread_notification
            )
            if latest_unread_notification
            else None
        ),
    }


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