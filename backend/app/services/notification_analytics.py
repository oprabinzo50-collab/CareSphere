from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notifications import Notification
from app.models.patient import Patient
from app.services.notification_dashboard import (
    calculate_notification_escalation,
)


def generate_patient_notification_analytics(
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
                Notification.created_at.asc()
            )
        ).all()
    )

    total = len(notifications)

    unread = [
        notification
        for notification in notifications
        if not notification.is_read
    ]

    read = [
        notification
        for notification in notifications
        if notification.is_read
    ]

    priority_counts: dict[str, int] = {}
    notification_type_counts: dict[str, int] = {}

    unread_priority_counts: dict[str, int] = {}
    unread_type_counts: dict[str, int] = {}

    escalation_counts = {
        "normal": 0,
        "attention": 0,
        "escalated": 0,
        "resolved": 0,
    }

    for notification in notifications:
        priority = str(
            notification.priority
        ).lower()

        notification_type = (
            notification.notification_type
        )

        priority_counts[priority] = (
            priority_counts.get(
                priority,
                0,
            )
            + 1
        )

        notification_type_counts[
            notification_type
        ] = (
            notification_type_counts.get(
                notification_type,
                0,
            )
            + 1
        )

        if not notification.is_read:
            unread_priority_counts[priority] = (
                unread_priority_counts.get(
                    priority,
                    0,
                )
                + 1
            )

            unread_type_counts[
                notification_type
            ] = (
                unread_type_counts.get(
                    notification_type,
                    0,
                )
                + 1
            )

        escalation = calculate_notification_escalation(
            notification
        )

        escalation_level = escalation[
            "escalation_level"
        ]

        escalation_counts[
            escalation_level
        ] = (
            escalation_counts.get(
                escalation_level,
                0,
            )
            + 1
        )

    if total:
        read_rate = round(
            (len(read) / total) * 100,
            2,
        )
    else:
        read_rate = 0.0

    if total:
        unread_rate = round(
            (len(unread) / total) * 100,
            2,
        )
    else:
        unread_rate = 0.0

    resolution_times_hours: list[float] = []

    for notification in read:
        if (
            notification.created_at is None
            or notification.read_at is None
        ):
            continue

        created_at = notification.created_at
        read_at = notification.read_at

        if created_at.tzinfo is None:
            created_at = created_at.replace(
                tzinfo=timezone.utc
            )

        if read_at.tzinfo is None:
            read_at = read_at.replace(
                tzinfo=timezone.utc
            )

        seconds = (
            read_at - created_at
        ).total_seconds()

        if seconds >= 0:
            resolution_times_hours.append(
                seconds / 3600
            )

    if resolution_times_hours:
        average_resolution_hours = round(
            sum(resolution_times_hours)
            / len(resolution_times_hours),
            2,
        )
    else:
        average_resolution_hours = None

    latest_notification = (
        notifications[-1]
        if notifications
        else None
    )

    earliest_notification = (
        notifications[0]
        if notifications
        else None
    )

    analytics_status = (
        "no_notification_history"
        if total == 0
        else (
            "escalation_attention"
            if (
                escalation_counts.get(
                    "escalated",
                    0,
                )
                > 0
            )
            else (
                "unresolved_notifications"
                if unread
                else "all_notifications_resolved"
            )
        )
    )

    return {
        "patient": {
            "id": patient.id,
            "patient_number": patient.patient_number,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "status": patient.status,
        },
        "analytics_status": analytics_status,
        "counts": {
            "total": total,
            "read": len(read),
            "unread": len(unread),
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
        },
        "rates": {
            "read_rate_percent": read_rate,
            "unread_rate_percent": unread_rate,
        },
        "priority_counts": priority_counts,
        "unread_priority_counts": (
            unread_priority_counts
        ),
        "notification_type_counts": (
            notification_type_counts
        ),
        "unread_notification_type_counts": (
            unread_type_counts
        ),
        "escalation_counts": escalation_counts,
        "average_resolution_hours": (
            average_resolution_hours
        ),
        "resolution_sample_size": len(
            resolution_times_hours
        ),
        "period": {
            "first_notification_at": (
                earliest_notification.created_at.isoformat()
                if (
                    earliest_notification
                    and earliest_notification.created_at
                )
                else None
            ),
            "latest_notification_at": (
                latest_notification.created_at.isoformat()
                if (
                    latest_notification
                    and latest_notification.created_at
                )
                else None
            ),
        },
    }