from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notifications import Notification
from app.models.patient import Patient
from app.services.notification_summary import (
    generate_patient_notification_summary,
    serialize_notification,
)


ESCALATION_ATTENTION_HOURS = 24
ESCALATION_ESCALATED_HOURS = 72


def calculate_notification_escalation(
    notification: Notification,
) -> dict[str, Any]:
    """
    Calculate deterministic escalation state for an unread
    notification based on its age.
    """

    now = datetime.now(timezone.utc)

    created_at = notification.created_at

    if created_at is None:
        age_hours = 0.0
    else:
        if created_at.tzinfo is None:
            created_at = created_at.replace(
                tzinfo=timezone.utc
            )

        age_seconds = (
            now - created_at
        ).total_seconds()

        age_hours = max(
            0.0,
            age_seconds / 3600,
        )

    if notification.is_read:
        escalation_level = "resolved"
    elif age_hours >= ESCALATION_ESCALATED_HOURS:
        escalation_level = "escalated"
    elif age_hours >= ESCALATION_ATTENTION_HOURS:
        escalation_level = "attention"
    else:
        escalation_level = "normal"

    return {
        "escalation_level": escalation_level,
        "age_hours": round(
            age_hours,
            2,
        ),
        "age_days": round(
            age_hours / 24,
            2,
        ),
    }


def serialize_dashboard_notification(
    notification: Notification,
) -> dict[str, Any]:

    data = serialize_notification(
        notification
    )

    escalation = calculate_notification_escalation(
        notification
    )

    data.update(escalation)

    return data


def generate_patient_notification_dashboard(
    db: Session,
    patient_id: int,
    limit: int = 20,
) -> dict[str, Any]:

    patient = db.get(
        Patient,
        patient_id,
    )

    if patient is None:
        raise ValueError("Patient not found")

    summary = generate_patient_notification_summary(
        db=db,
        patient_id=patient_id,
    )

    notifications = list(
        db.scalars(
            select(Notification)
            .where(
                Notification.patient_id == patient_id
            )
            .order_by(
                Notification.created_at.desc()
            )
            .limit(limit)
        ).all()
    )

    unread_notifications = [
        notification
        for notification in notifications
        if not notification.is_read
    ]

    recent_notifications = [
        serialize_dashboard_notification(
            notification
        )
        for notification in notifications
    ]

    unread_recent_notifications = [
        serialize_dashboard_notification(
            notification
        )
        for notification in unread_notifications
    ]

    attention_notifications = [
        notification
        for notification in unread_notifications
        if calculate_notification_escalation(
            notification
        )["escalation_level"]
        == "attention"
    ]

    escalated_notifications = [
        notification
        for notification in unread_notifications
        if calculate_notification_escalation(
            notification
        )["escalation_level"]
        == "escalated"
    ]

    counts = summary.get(
        "counts",
        {},
    )

    if escalated_notifications:
        dashboard_status = "escalation_required"
    elif attention_notifications:
        dashboard_status = "attention_required"
    elif counts.get("unread", 0) > 0:
        dashboard_status = "notifications_pending"
    elif counts.get("total", 0) > 0:
        dashboard_status = "all_notifications_read"
    else:
        dashboard_status = "no_notifications"

    return {
        "patient": summary.get(
            "patient"
        ),
        "dashboard_status": dashboard_status,
        "summary_status": summary.get(
            "summary_status"
        ),
        "counts": counts,
        "priority_counts": summary.get(
            "priority_counts",
            {},
        ),
        "unread_priority_counts": summary.get(
            "unread_priority_counts",
            {},
        ),
        "notification_type_counts": summary.get(
            "notification_type_counts",
            {},
        ),
        "unread_notification_type_counts": summary.get(
            "unread_notification_type_counts",
            {},
        ),
        "latest_notification": summary.get(
            "latest_notification"
        ),
        "latest_unread_notification": summary.get(
            "latest_unread_notification"
        ),
        "escalation": {
            "attention_count": len(
                attention_notifications
            ),
            "escalated_count": len(
                escalated_notifications
            ),
            "total_unresolved": len(
                unread_notifications
            ),
            "attention_threshold_hours": (
                ESCALATION_ATTENTION_HOURS
            ),
            "escalated_threshold_hours": (
                ESCALATION_ESCALATED_HOURS
            ),
        },
        "escalated_notifications": [
            serialize_dashboard_notification(
                notification
            )
            for notification in escalated_notifications
        ],
        "attention_notifications": [
            serialize_dashboard_notification(
                notification
            )
            for notification in attention_notifications
        ],
        "recent_notifications": recent_notifications,
        "recent_unread_notifications": (
            unread_recent_notifications
        ),
        "recent_notification_count": len(
            recent_notifications
        ),
        "recent_unread_count": len(
            unread_recent_notifications
        ),
        "limit": limit,
    }