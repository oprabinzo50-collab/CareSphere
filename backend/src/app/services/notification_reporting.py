from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.services.notification_intelligence import (
    generate_patient_notification_intelligence,
)
from app.services.notification_search import (
    search_patient_notifications,
)


def generate_patient_notification_report(
    db: Session,
    patient_id: int,
    days: int = 30,
    dashboard_limit: int = 20,
    search: str | None = None,
    notification_type: str | None = None,
    priority: str | None = None,
    is_read: bool | None = None,
    escalation_level: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:

    intelligence = (
        generate_patient_notification_intelligence(
            db=db,
            patient_id=patient_id,
            days=days,
            dashboard_limit=dashboard_limit,
        )
    )

    search_results = search_patient_notifications(
        db=db,
        patient_id=patient_id,
        search=search,
        notification_type=notification_type,
        priority=priority,
        is_read=is_read,
        escalation_level=escalation_level,
        limit=limit,
        offset=offset,
    )

    overview = intelligence.get(
        "overview",
        {},
    )

    escalation = intelligence.get(
        "escalation",
        {},
    )

    performance = intelligence.get(
        "performance",
        {},
    )

    analytics = intelligence.get(
        "analytics",
        {},
    )

    trends = intelligence.get(
        "trends",
        {},
    )

    dashboard = intelligence.get(
        "dashboard",
        {},
    )

    search_pagination = search_results.get(
        "pagination",
        {},
    )

    report_generated_at = (
        datetime.now(timezone.utc)
        .isoformat()
    )

    total_notifications = overview.get(
        "total_notifications",
        0,
    )

    unread_notifications = overview.get(
        "unread_notifications",
        0,
    )

    if total_notifications == 0:
        report_status = "no_notification_history"
    elif escalation.get(
        "escalated_count",
        0,
    ) > 0:
        report_status = "escalation_required"
    elif escalation.get(
        "attention_count",
        0,
    ) > 0:
        report_status = "attention_required"
    elif unread_notifications > 0:
        report_status = "notifications_pending"
    else:
        report_status = "all_notifications_resolved"

    return {
        "report": {
            "report_type": (
                "notification_intelligence"
            ),
            "report_status": report_status,
            "generated_at": (
                report_generated_at
            ),
            "period_days": days,
        },
        "patient": intelligence.get(
            "patient"
        ),
        "overview": {
            "total_notifications": (
                total_notifications
            ),
            "unread_notifications": (
                unread_notifications
            ),
            "read_notifications": (
                overview.get(
                    "read_notifications",
                    0,
                )
            ),
            "read_rate_percent": (
                overview.get(
                    "read_rate_percent",
                    0.0,
                )
            ),
        },
        "priority_breakdown": (
            analytics.get(
                "priority_counts",
                {},
            )
        ),
        "notification_type_breakdown": (
            analytics.get(
                "notification_type_counts",
                {},
            )
        ),
        "unread_priority_breakdown": (
            analytics.get(
                "unread_priority_counts",
                {},
            )
        ),
        "unread_notification_type_breakdown": (
            analytics.get(
                "unread_notification_type_counts",
                {},
            )
        ),
        "escalation": {
            "attention_count": (
                escalation.get(
                    "attention_count",
                    0,
                )
            ),
            "escalated_count": (
                escalation.get(
                    "escalated_count",
                    0,
                )
            ),
            "total_unresolved": (
                escalation.get(
                    "total_unresolved",
                    0,
                )
            ),
            "attention_threshold_hours": (
                escalation.get(
                    "attention_threshold_hours"
                )
            ),
            "escalated_threshold_hours": (
                escalation.get(
                    "escalated_threshold_hours"
                )
            ),
        },
        "performance": {
            "status": performance.get(
                "status"
            ),
            "counts": performance.get(
                "counts",
                {},
            ),
            "rates": performance.get(
                "rates",
                {},
            ),
            "response_time": performance.get(
                "response_time",
                {},
            ),
            "response_categories": performance.get(
                "response_categories",
                {},
            ),
            "unresolved_aging": performance.get(
                "unresolved_aging",
                {},
            ),
        },
        "trends": {
            "period": trends.get(
                "period",
                {},
            ),
            "summary": trends.get(
                "summary",
                {},
            ),
            "daily": trends.get(
                "daily",
                [],
            ),
        },
        "dashboard": {
            "dashboard_status": (
                dashboard.get(
                    "dashboard_status"
                )
            ),
            "summary_status": (
                dashboard.get(
                    "summary_status"
                )
            ),
            "latest_notification": (
                dashboard.get(
                    "latest_notification"
                )
            ),
            "latest_unread_notification": (
                dashboard.get(
                    "latest_unread_notification"
                )
            ),
            "escalated_notifications": (
                dashboard.get(
                    "escalated_notifications",
                    [],
                )
            ),
            "attention_notifications": (
                dashboard.get(
                    "attention_notifications",
                    [],
                )
            ),
            "recent_unread_notifications": (
                dashboard.get(
                    "recent_unread_notifications",
                    [],
                )
            ),
        },
        "search": {
            "criteria": {
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
            "pagination": (
                search_pagination
            ),
            "results": search_results.get(
                "results",
                [],
            ),
        },
    }