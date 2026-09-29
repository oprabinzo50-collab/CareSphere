from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment_sessions import AssessmentSession
from app.models.clinician_reviews import ClinicianReview
from app.models.patient import Patient
from app.models.recommendations import Recommendation
from app.models.reports import Report


def generate_patient_notifications(
    db: Session,
    patient_id: int,
) -> dict[str, Any]:

    patient = db.get(Patient, patient_id)

    if patient is None:
        raise ValueError("Patient not found")

    assessments = list(
        db.scalars(
            select(AssessmentSession)
            .where(
                AssessmentSession.patient_id == patient_id
            )
            .order_by(
                AssessmentSession.started_at.desc()
            )
        ).all()
    )

    if not assessments:
        return {
            "patient_id": patient_id,
            "patient": {
                "patient_number": patient.patient_number,
                "first_name": patient.first_name,
                "last_name": patient.last_name,
                "status": patient.status,
            },
            "notification_count": 0,
            "unread_count": 0,
            "status": "no_notifications",
            "notifications": [],
        }

    assessment_ids = [
        assessment.id
        for assessment in assessments
    ]

    recommendations = list(
        db.scalars(
            select(Recommendation)
            .where(
                Recommendation.assessment_id.in_(
                    assessment_ids
                )
            )
        ).all()
    )

    reports = list(
        db.scalars(
            select(Report)
            .where(
                Report.assessment_id.in_(
                    assessment_ids
                )
            )
        ).all()
    )

    reviews = list(
        db.scalars(
            select(ClinicianReview)
            .where(
                ClinicianReview.assessment_id.in_(
                    assessment_ids
                )
            )
        ).all()
    )

    notifications: list[dict[str, Any]] = []

    # ---------------------------------------------------------
    # Assessment notifications
    # ---------------------------------------------------------

    for assessment in assessments:

        if assessment.status == "in_progress":
            notifications.append(
                {
                    "notification_type": (
                        "assessment_in_progress"
                    ),
                    "priority": "medium",
                    "title": "Assessment still in progress",
                    "message": (
                        "An assessment has been started "
                        "but has not yet been completed."
                    ),
                    "assessment_id": assessment.id,
                    "record_id": assessment.id,
                    "status": "unread",
                    "created_at": (
                        assessment.started_at.isoformat()
                        if assessment.started_at
                        else None
                    ),
                }
            )

        elif assessment.status == "completed":
            assessment_reviews = [
                review
                for review in reviews
                if review.assessment_id == assessment.id
            ]

            if not assessment_reviews:
                notifications.append(
                    {
                        "notification_type": (
                            "assessment_review_required"
                        ),
                        "priority": "medium",
                        "title": (
                            "Completed assessment "
                            "awaiting review"
                        ),
                        "message": (
                            "A completed assessment does "
                            "not yet have a clinician review."
                        ),
                        "assessment_id": assessment.id,
                        "record_id": assessment.id,
                        "status": "unread",
                        "created_at": (
                            assessment.completed_at.isoformat()
                            if assessment.completed_at
                            else None
                        ),
                    }
                )

    # ---------------------------------------------------------
    # Recommendation notifications
    # ---------------------------------------------------------

    for recommendation in recommendations:

        recommendation_status = str(
            getattr(
                recommendation,
                "status",
                "",
            )
        ).lower()

        if recommendation_status in {
            "pending",
            "pending_review",
            "awaiting_review",
        }:
            notifications.append(
                {
                    "notification_type": (
                        "recommendation_review_required"
                    ),
                    "priority": "medium",
                    "title": (
                        getattr(
                            recommendation,
                            "title",
                            None,
                        )
                        or "Recommendation awaiting review"
                    ),
                    "message": (
                        "A recommendation is awaiting "
                        "clinician review."
                    ),
                    "assessment_id": (
                        recommendation.assessment_id
                    ),
                    "record_id": recommendation.id,
                    "status": "unread",
                    "created_at": (
                        recommendation.created_at.isoformat()
                        if getattr(
                            recommendation,
                            "created_at",
                            None,
                        )
                        else None
                    ),
                }
            )

    # ---------------------------------------------------------
    # Report notifications
    # ---------------------------------------------------------

    for report in reports:

        report_status = str(
            getattr(
                report,
                "status",
                "",
            )
        ).lower()

        if report_status in {
            "draft",
            "pending_review",
            "awaiting_review",
        }:
            notifications.append(
                {
                    "notification_type": (
                        "report_review_required"
                    ),
                    "priority": "medium",
                    "title": (
                        getattr(
                            report,
                            "report_title",
                            None,
                        )
                        or "Report awaiting review"
                    ),
                    "message": (
                        "An assessment report is awaiting "
                        "workflow completion or review."
                    ),
                    "assessment_id": report.assessment_id,
                    "record_id": report.id,
                    "status": "unread",
                    "created_at": (
                        report.generated_at.isoformat()
                        if getattr(
                            report,
                            "generated_at",
                            None,
                        )
                        else None
                    ),
                }
            )

    # ---------------------------------------------------------
    # Clinician review notifications
    # ---------------------------------------------------------

    for review in reviews:

        review_status = str(
            getattr(
                review,
                "review_status",
                "",
            )
        ).lower()

        if review_status in {
            "pending",
            "pending_review",
            "awaiting_review",
        }:
            notifications.append(
                {
                    "notification_type": (
                        "clinician_review_pending"
                    ),
                    "priority": "medium",
                    "title": "Clinician review pending",
                    "message": (
                        "A clinician review record is "
                        "awaiting completion."
                    ),
                    "assessment_id": review.assessment_id,
                    "record_id": review.id,
                    "status": "unread",
                    "created_at": (
                        review.created_at.isoformat()
                        if getattr(
                            review,
                            "created_at",
                            None,
                        )
                        else None
                    ),
                }
            )

    # ---------------------------------------------------------
    # Sort newest notifications first
    # ---------------------------------------------------------

    notifications.sort(
        key=lambda item: (
            item.get("created_at")
            or ""
        ),
        reverse=True,
    )

    notification_count = len(
        notifications
    )

    unread_count = sum(
        1
        for notification in notifications
        if notification.get("status") == "unread"
    )

    if notification_count == 0:
        overall_status = "no_notifications"
    else:
        overall_status = "notifications_available"

    return {
        "patient_id": patient_id,
        "patient": {
            "patient_number": patient.patient_number,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "status": patient.status,
        },
        "notification_count": notification_count,
        "unread_count": unread_count,
        "status": overall_status,
        "notifications": notifications,
    }