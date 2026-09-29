from datetime import datetime, time, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notifications import Notification
from app.models.patient import Patient
from app.services.notification_dashboard import (
    calculate_notification_escalation,
)
from app.services.notification_summary import (
    serialize_notification,
)


VALID_ESCALATION_LEVELS = {
    "normal",
    "attention",
    "escalated",
    "resolved",
}

VALID_PRIORITIES = {
    "high",
    "medium",
    "low",
}


def _parse_date_start(
    value: str | None,
) -> datetime | None:
    if not value:
        return None

    try:
        parsed = datetime.strptime(
            value,
            "%Y-%m-%d",
        ).date()
    except ValueError:
        raise ValueError(
            "from_date must use YYYY-MM-DD format"
        )

    return datetime.combine(
        parsed,
        time.min,
        tzinfo=timezone.utc,
    )


def _parse_date_end(
    value: str | None,
) -> datetime | None:
    if not value:
        return None

    try:
        parsed = datetime.strptime(
            value,
            "%Y-%m-%d",
        ).date()
    except ValueError:
        raise ValueError(
            "to_date must use YYYY-MM-DD format"
        )

    return datetime.combine(
        parsed,
        time.max,
        tzinfo=timezone.utc,
    )


def generate_filtered_patient_notifications(
    db: Session,
    patient_id: int,
    notification_type: str | None = None,
    priority: str | None = None,
    is_read: bool | None = None,
    escalation_level: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:

    patient = db.get(
        Patient,
        patient_id,
    )

    if patient is None:
        raise ValueError(
            "Patient not found"
        )

    if priority is not None:
        priority = priority.lower()

        if priority not in VALID_PRIORITIES:
            raise ValueError(
                "priority must be high, medium, or low"
            )

    if escalation_level is not None:
        escalation_level = (
            escalation_level.lower()
        )

        if (
            escalation_level
            not in VALID_ESCALATION_LEVELS
        ):
            raise ValueError(
                "Invalid escalation_level"
            )

    start_datetime = _parse_date_start(
        from_date
    )

    end_datetime = _parse_date_end(
        to_date
    )

    if (
        start_datetime is not None
        and end_datetime is not None
        and start_datetime > end_datetime
    ):
        raise ValueError(
            "from_date cannot be after to_date"
        )

    statement = select(
        Notification
    ).where(
        Notification.patient_id == patient_id
    )

    if notification_type:
        statement = statement.where(
            Notification.notification_type
            == notification_type
        )

    if priority:
        statement = statement.where(
            Notification.priority
            == priority
        )

    if is_read is not None:
        statement = statement.where(
            Notification.is_read
            == is_read
        )

    if start_datetime is not None:
        statement = statement.where(
            Notification.created_at
            >= start_datetime
        )

    if end_datetime is not None:
        statement = statement.where(
            Notification.created_at
            <= end_datetime
        )

    statement = statement.order_by(
        Notification.created_at.desc()
    )

    notifications = list(
        db.scalars(statement).all()
    )

    filtered_notifications = []

    for notification in notifications:
        escalation = (
            calculate_notification_escalation(
                notification
            )
        )

        if (
            escalation_level is not None
            and escalation[
                "escalation_level"
            ]
            != escalation_level
        ):
            continue

        data = serialize_notification(
            notification
        )

        data.update(
            escalation
        )

        filtered_notifications.append(
            data
        )

    total_count = len(
        filtered_notifications
    )

    paginated_notifications = (
        filtered_notifications[
            offset : offset + limit
        ]
    )

    unread_count = sum(
        1
        for item in filtered_notifications
        if not item["is_read"]
    )

    return {
        "patient": {
            "id": patient.id,
            "patient_number": (
                patient.patient_number
            ),
            "first_name": (
                patient.first_name
            ),
            "last_name": (
                patient.last_name
            ),
            "status": patient.status,
        },
        "filters": {
            "notification_type": (
                notification_type
            ),
            "priority": priority,
            "is_read": is_read,
            "escalation_level": (
                escalation_level
            ),
            "from_date": from_date,
            "to_date": to_date,
        },
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total_count": total_count,
            "returned_count": len(
                paginated_notifications
            ),
            "unread_count": unread_count,
            "has_more": (
                offset + limit
                < total_count
            ),
        },
        "notifications": (
            paginated_notifications
        ),
    }