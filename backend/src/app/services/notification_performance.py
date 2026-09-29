from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notifications import Notification
from app.models.patient import Patient


FAST_RESPONSE_HOURS = 24
DELAYED_RESPONSE_HOURS = 72


def _normalize_datetime(
    value: datetime | None,
) -> datetime | None:
    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(
            tzinfo=timezone.utc
        )

    return value


def _calculate_hours(
    start: datetime | None,
    end: datetime | None,
) -> float | None:
    start = _normalize_datetime(start)
    end = _normalize_datetime(end)

    if start is None or end is None:
        return None

    seconds = (
        end - start
    ).total_seconds()

    if seconds < 0:
        return None

    return round(
        seconds / 3600,
        2,
    )


def _response_category(
    response_hours: float,
) -> str:
    if response_hours < FAST_RESPONSE_HOURS:
        return "fast"

    if response_hours < DELAYED_RESPONSE_HOURS:
        return "moderate"

    return "delayed"


def _unresolved_age_category(
    age_hours: float,
) -> str:
    if age_hours < FAST_RESPONSE_HOURS:
        return "recent"

    if age_hours < DELAYED_RESPONSE_HOURS:
        return "attention"

    return "overdue"


def generate_patient_notification_performance(
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

    now = datetime.now(
        timezone.utc
    )

    resolved_notifications = [
        notification
        for notification in notifications
        if (
            notification.is_read
            and notification.read_at is not None
        )
    ]

    unresolved_notifications = [
        notification
        for notification in notifications
        if not notification.is_read
    ]

    response_times: list[float] = []

    response_categories = {
        "fast": 0,
        "moderate": 0,
        "delayed": 0,
    }

    resolution_by_priority: dict[
        str,
        dict[str, Any],
    ] = {}

    resolution_by_type: dict[
        str,
        dict[str, Any],
    ] = {}

    for notification in resolved_notifications:
        response_hours = _calculate_hours(
            notification.created_at,
            notification.read_at,
        )

        if response_hours is None:
            continue

        response_times.append(
            response_hours
        )

        category = _response_category(
            response_hours
        )

        response_categories[
            category
        ] += 1

        priority = str(
            notification.priority
        ).lower()

        priority_data = resolution_by_priority.setdefault(
            priority,
            {
                "resolved_count": 0,
                "total_response_hours": 0.0,
                "average_response_hours": None,
            },
        )

        priority_data[
            "resolved_count"
        ] += 1

        priority_data[
            "total_response_hours"
        ] += response_hours

        notification_type = (
            notification.notification_type
        )

        type_data = resolution_by_type.setdefault(
            notification_type,
            {
                "resolved_count": 0,
                "total_response_hours": 0.0,
                "average_response_hours": None,
            },
        )

        type_data[
            "resolved_count"
        ] += 1

        type_data[
            "total_response_hours"
        ] += response_hours

    for data in resolution_by_priority.values():
        count = data[
            "resolved_count"
        ]

        if count:
            data[
                "average_response_hours"
            ] = round(
                data[
                    "total_response_hours"
                ] / count,
                2,
            )

        data.pop(
            "total_response_hours"
        )

    for data in resolution_by_type.values():
        count = data[
            "resolved_count"
        ]

        if count:
            data[
                "average_response_hours"
            ] = round(
                data[
                    "total_response_hours"
                ] / count,
                2,
            )

        data.pop(
            "total_response_hours"
        )

    unresolved_aging = {
        "recent": 0,
        "attention": 0,
        "overdue": 0,
    }

    unresolved_items: list[
        dict[str, Any]
    ] = []

    for notification in unresolved_notifications:
        created_at = _normalize_datetime(
            notification.created_at
        )

        if created_at is None:
            age_hours = 0.0
        else:
            age_seconds = (
                now - created_at
            ).total_seconds()

            age_hours = round(
                max(
                    0.0,
                    age_seconds / 3600,
                ),
                2,
            )

        age_category = (
            _unresolved_age_category(
                age_hours
            )
        )

        unresolved_aging[
            age_category
        ] += 1

        unresolved_items.append(
            {
                "id": notification.id,
                "notification_type": (
                    notification.notification_type
                ),
                "priority": notification.priority,
                "title": notification.title,
                "assessment_id": (
                    notification.assessment_id
                ),
                "record_id": (
                    notification.record_id
                ),
                "created_at": (
                    notification.created_at.isoformat()
                    if notification.created_at
                    else None
                ),
                "age_hours": age_hours,
                "age_days": round(
                    age_hours / 24,
                    2,
                ),
                "age_category": (
                    age_category
                ),
            }
        )

    unresolved_items.sort(
        key=lambda item: item[
            "age_hours"
        ],
        reverse=True,
    )

    total_notifications = len(
        notifications
    )

    resolved_count = len(
        resolved_notifications
    )

    unresolved_count = len(
        unresolved_notifications
    )

    if response_times:
        average_response_hours = round(
            sum(response_times)
            / len(response_times),
            2,
        )

        fastest_response_hours = min(
            response_times
        )

        slowest_response_hours = max(
            response_times
        )
    else:
        average_response_hours = None
        fastest_response_hours = None
        slowest_response_hours = None

    if total_notifications:
        resolution_rate = round(
            (
                resolved_count
                / total_notifications
            )
            * 100,
            2,
        )
    else:
        resolution_rate = 0.0

    if unresolved_aging[
        "overdue"
    ] > 0:
        performance_status = (
            "overdue_notifications"
        )

    elif unresolved_aging[
        "attention"
    ] > 0:
        performance_status = (
            "attention_required"
        )

    elif unresolved_count > 0:
        performance_status = (
            "unresolved_notifications"
        )

    elif total_notifications > 0:
        performance_status = (
            "all_notifications_resolved"
        )

    else:
        performance_status = (
            "no_notification_history"
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
        "performance_status": (
            performance_status
        ),
        "thresholds": {
            "fast_response_hours": (
                FAST_RESPONSE_HOURS
            ),
            "delayed_response_hours": (
                DELAYED_RESPONSE_HOURS
            ),
        },
        "counts": {
            "total_notifications": (
                total_notifications
            ),
            "resolved": resolved_count,
            "unresolved": unresolved_count,
        },
        "rates": {
            "resolution_rate_percent": (
                resolution_rate
            ),
        },
        "response_time": {
            "average_hours": (
                average_response_hours
            ),
            "fastest_hours": (
                fastest_response_hours
            ),
            "slowest_hours": (
                slowest_response_hours
            ),
            "sample_size": len(
                response_times
            ),
        },
        "response_categories": (
            response_categories
        ),
        "unresolved_aging": (
            unresolved_aging
        ),
        "resolution_by_priority": (
            resolution_by_priority
        ),
        "resolution_by_notification_type": (
            resolution_by_type
        ),
        "unresolved_notifications": (
            unresolved_items
        ),
    }