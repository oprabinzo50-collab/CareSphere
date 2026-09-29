from typing import Any

from sqlalchemy import or_, select
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


def search_patient_notifications(
    db: Session,
    patient_id: int,
    search: str | None = None,
    notification_type: str | None = None,
    priority: str | None = None,
    is_read: bool | None = None,
    escalation_level: str | None = None,
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

    statement = select(
        Notification
    ).where(
        Notification.patient_id == patient_id
    )

    if search:
        search_term = (
            f"%{search.strip()}%"
        )

        statement = statement.where(
            or_(
                Notification.title.ilike(
                    search_term
                ),
                Notification.message.ilike(
                    search_term
                ),
            )
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
            Notification.is_read == is_read
        )

    statement = statement.order_by(
        Notification.created_at.desc()
    )

    notifications = list(
        db.scalars(statement).all()
    )

    results: list[dict[str, Any]] = []

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

        results.append(data)

    total_count = len(results)

    paginated_results = results[
        offset : offset + limit
    ]

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
        "query": {
            "search": search,
            "notification_type": (
                notification_type
            ),
            "priority": priority,
            "is_read": is_read,
            "escalation_level": (
                escalation_level
            ),
        },
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total_count": total_count,
            "returned_count": len(
                paginated_results
            ),
            "has_more": (
                offset + limit
                < total_count
            ),
        },
        "results": paginated_results,
    }
