from typing import Any

from sqlalchemy.orm import Session

from app.services.notification_analytics import (
    generate_patient_notification_analytics,
)
from app.services.notification_dashboard import (
    generate_patient_notification_dashboard,
)
from app.services.notification_performance import (
    generate_patient_notification_performance,
)
from app.services.notification_trends import (
    generate_patient_notification_trends,
)


def generate_patient_notification_intelligence(
    db: Session,
    patient_id: int,
    days: int = 30,
    dashboard_limit: int = 20,
) -> dict[str, Any]:

    analytics = (
        generate_patient_notification_analytics(
            db=db,
            patient_id=patient_id,
        )
    )

    trends = (
        generate_patient_notification_trends(
            db=db,
            patient_id=patient_id,
            days=days,
        )
    )

    dashboard = (
        generate_patient_notification_dashboard(
            db=db,
            patient_id=patient_id,
            limit=dashboard_limit,
        )
    )

    performance = (
        generate_patient_notification_performance(
            db=db,
            patient_id=patient_id,
        )
    )

    counts = analytics.get(
        "counts",
        {},
    )

    escalation = dashboard.get(
        "escalation",
        {},
    )

    performance_status = performance.get(
        "performance_status",
        "unknown",
    )

    if (
        escalation.get(
            "escalated_count",
            0,
        )
        > 0
    ):
        intelligence_status = (
            "escalation_required"
        )

    elif (
        escalation.get(
            "attention_count",
            0,
        )
        > 0
    ):
        intelligence_status = (
            "attention_required"
        )

    elif counts.get(
        "unread",
        0,
    ) > 0:
        intelligence_status = (
            "notifications_pending"
        )

    elif counts.get(
        "total",
        0,
    ) > 0:
        intelligence_status = (
            "all_notifications_resolved"
        )

    else:
        intelligence_status = (
            "no_notification_history"
        )

    return {
        "patient": analytics.get(
            "patient"
        ),
        "intelligence_status": (
            intelligence_status
        ),
        "overview": {
            "total_notifications": counts.get(
                "total",
                0,
            ),
            "unread_notifications": counts.get(
                "unread",
                0,
            ),
            "read_notifications": counts.get(
                "read",
                0,
            ),
            "read_rate_percent": (
                analytics.get(
                    "rates",
                    {},
                ).get(
                    "read_rate_percent",
                    0.0,
                )
            ),
        },
        "escalation": escalation,
        "performance": {
            "status": performance_status,
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
            "response_categories": (
                performance.get(
                    "response_categories",
                    {},
                )
            ),
            "unresolved_aging": (
                performance.get(
                    "unresolved_aging",
                    {},
                )
            ),
        },
        "analytics": {
            "priority_counts": (
                analytics.get(
                    "priority_counts",
                    {},
                )
            ),
            "notification_type_counts": (
                analytics.get(
                    "notification_type_counts",
                    {},
                )
            ),
            "unread_priority_counts": (
                analytics.get(
                    "unread_priority_counts",
                    {},
                )
            ),
            "unread_notification_type_counts": (
                analytics.get(
                    "unread_notification_type_counts",
                    {},
                )
            ),
            "average_resolution_hours": (
                analytics.get(
                    "average_resolution_hours"
                )
            ),
            "resolution_sample_size": (
                analytics.get(
                    "resolution_sample_size",
                    0,
                )
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
                "trends",
                [],
            ),
        },
        "dashboard": {
            "dashboard_status": dashboard.get(
                "dashboard_status"
            ),
            "summary_status": dashboard.get(
                "summary_status"
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
    }