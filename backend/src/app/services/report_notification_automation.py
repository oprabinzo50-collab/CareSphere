from typing import Any

from sqlalchemy.orm import Session

from app.models.assessment_sessions import AssessmentSession
from app.models.reports import Report
from app.services.notification_sync import (
    synchronize_patient_notification_inbox,
)


REVIEW_REQUIRED_STATUSES = {
    "draft",
    "pending_review",
    "awaiting_review",
}


def trigger_report_notifications(
    db: Session,
    *,
    report: Report,
) -> dict[str, Any]:
    """
    Synchronize patient notifications whenever a report changes,
    allowing obsolete review notifications to resolve.
    """

    report_status = str(
        getattr(
            report,
            "status",
            "",
        )
    ).lower()

    assessment = db.get(
        AssessmentSession,
        report.assessment_id,
    )

    if assessment is None:
        return {
            "patient_id": None,
            "triggered": False,
            "reason": "assessment_not_found",
            "status": report_status,
        }

    patient_id = assessment.patient_id

    result = synchronize_patient_notification_inbox(
        db=db,
        patient_id=patient_id,
    )

    if report_status in REVIEW_REQUIRED_STATUSES:
        reason = "report_review_required"
    else:
        reason = "report_status_updated"

    return {
        "patient_id": patient_id,
        "triggered": True,
        "reason": reason,
        "status": report_status,
        "result": result,
    }