from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notifications import Notification
from app.models.patient import Patient


DEFAULT_DAYS = 30
MAX_DAYS = 365


def generate_patient_notification_trends(
    db: Session,
    patient_id: int,
    days: int = DEFAULT_DAYS,
) -> dict[str, Any]:

    patient = db.get(
        Patient,
        patient_id,
    )

    if patient is None:
        raise ValueError("Patient not found")

    if days < 1:
        raise ValueError(
            "Days must be greater than or equal to 1"
        )

    if days > MAX_DAYS:
        raise ValueError(
            f"Days cannot exceed {MAX_DAYS}"
        )

    now = datetime.now(timezone.utc)

    start_date = (
        now - timedelta(days=days - 1)
    ).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    end_date = now.replace(
        hour=23,
        minute=59,
        second=59,
        microsecond=999999,
    )

    notifications = list(
        db.scalars(
            select(Notification)
            .where(
                Notification.patient_id == patient_id,
                Notification.created_at >= start_date,
                Notification.created_at <= end_date,
            )
            .order_by(
                Notification.created_at.asc()
            )
        ).all()
    )

    trend_map: dict[str, dict[str, Any]] = {}

    current_date = start_date.date()

    while current_date <= end_date.date():
        date_key = current_date.isoformat()

        trend_map[date_key] = {
            "date": date_key,
            "created_count": 0,
            "read_count": 0,
            "unread_count": 0,
            "high_priority_count": 0,
            "medium_priority_count": 0,
            "low_priority_count": 0,
            "notification_types": {},
        }

        current_date += timedelta(days=1)

    for notification in notifications:
        if notification.created_at is None:
            continue

        created_at = notification.created_at

        if created_at.tzinfo is None:
            created_at = created_at.replace(
                tzinfo=timezone.utc
            )

        date_key = created_at.date().isoformat()

        if date_key not in trend_map:
            continue

        bucket = trend_map[date_key]

        bucket["created_count"] += 1

        priority = str(
            notification.priority
        ).lower()

        if priority == "high":
            bucket["high_priority_count"] += 1
        elif priority == "low":
            bucket["low_priority_count"] += 1
        else:
            bucket["medium_priority_count"] += 1

        notification_type = (
            notification.notification_type
        )

        type_counts = bucket[
            "notification_types"
        ]

        type_counts[notification_type] = (
            type_counts.get(
                notification_type,
                0,
            )
            + 1
        )

        if notification.is_read:
            bucket["read_count"] += 1
        else:
            bucket["unread_count"] += 1

    trends = list(
        trend_map.values()
    )

    total_created = sum(
        item["created_count"]
        for item in trends
    )

    total_read = sum(
        item["read_count"]
        for item in trends
    )

    total_unread = sum(
        item["unread_count"]
        for item in trends
    )

    if total_created:
        overall_read_rate = round(
            (
                total_read
                / total_created
            )
            * 100,
            2,
        )
    else:
        overall_read_rate = 0.0

    peak_creation_day = None

    if trends:
        peak_creation_day = max(
            trends,
            key=lambda item: item[
                "created_count"
            ],
        )

        if (
            peak_creation_day[
                "created_count"
            ]
            == 0
        ):
            peak_creation_day = None

    return {
        "patient": {
            "id": patient.id,
            "patient_number": patient.patient_number,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "status": patient.status,
        },
        "period": {
            "days": days,
            "start_date": (
                start_date.date().isoformat()
            ),
            "end_date": (
                end_date.date().isoformat()
            ),
        },
        "summary": {
            "total_created": total_created,
            "total_read": total_read,
            "total_unread": total_unread,
            "overall_read_rate_percent": (
                overall_read_rate
            ),
            "peak_creation_day": peak_creation_day,
        },
        "trends": trends,
    }