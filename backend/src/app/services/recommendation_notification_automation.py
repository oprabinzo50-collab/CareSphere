from typing import Any

from sqlalchemy.orm import Session

from app.models.assessment_sessions import AssessmentSession
from app.models.recommendations import Recommendation
from app.services.notification_sync import (
    synchronize_patient_notification_inbox,
)


REVIEW_REQUIRED_STATUSES = {
    "pending",
    "pending_review",
    "awaiting_review",
}


def trigger_recommendation_notifications(
    db: Session,
    *,
    recommendation: Recommendation,
) -> dict[str, Any]:
    """
    Synchronize patient notifications whenever a recommendation
    changes, allowing obsolete review notifications to resolve.
    """

    status = str(
        getattr(
            recommendation,
            "status",
            "",
        )
    ).lower()

    assessment = db.get(
        AssessmentSession,
        recommendation.assessment_id,
    )

    if assessment is None:
        return {
            "patient_id": None,
            "triggered": False,
            "reason": "assessment_not_found",
            "status": status,
        }

    patient_id = assessment.patient_id

    result = synchronize_patient_notification_inbox(
        db=db,
        patient_id=patient_id,
    )

    if status in REVIEW_REQUIRED_STATUSES:
        reason = "recommendation_review_required"
    else:
        reason = "recommendation_status_updated"

    return {
        "patient_id": patient_id,
        "triggered": True,
        "reason": reason,
        "status": status,
        "result": result,
    }