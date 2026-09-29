from typing import Any

from sqlalchemy.orm import Session

from app.models.assessment_sessions import AssessmentSession
from app.models.clinician_reviews import ClinicianReview
from app.services.notification_sync import (
    synchronize_patient_notification_inbox,
)


REVIEW_PENDING_STATUSES = {
    "pending",
    "pending_review",
    "awaiting_review",
}


def trigger_clinician_review_notifications(
    db: Session,
    *,
    review: ClinicianReview,
) -> dict[str, Any]:
    """
    Synchronize patient notifications whenever a clinician review
    changes, allowing obsolete pending-review notifications to resolve.
    """

    review_status = str(
        getattr(
            review,
            "review_status",
            "",
        )
    ).lower()

    assessment = db.get(
        AssessmentSession,
        review.assessment_id,
    )

    if assessment is None:
        return {
            "patient_id": None,
            "triggered": False,
            "reason": "assessment_not_found",
            "status": review_status,
        }

    patient_id = assessment.patient_id

    result = synchronize_patient_notification_inbox(
        db=db,
        patient_id=patient_id,
    )

    if review_status in REVIEW_PENDING_STATUSES:
        reason = "clinician_review_pending"
    else:
        reason = "clinician_review_status_updated"

    return {
        "patient_id": patient_id,
        "triggered": True,
        "reason": reason,
        "status": review_status,
        "result": result,
    }