from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment_sessions import AssessmentSession
from app.models.clinician_reviews import ClinicianReview
from app.models.patient import Patient
from app.models.recommendations import Recommendation
from app.models.reports import Report


def generate_patient_follow_up(
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
            "assessment_count": 0,
            "latest_assessment": None,
            "follow_up_status": "no_assessment",
            "follow_up_count": 0,
            "items": [],
            "counts": {
                "incomplete_assessments": 0,
                "pending_recommendations": 0,
                "pending_reports": 0,
                "pending_reviews": 0,
                "completed_without_follow_up": 0,
            },
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

    items: list[dict[str, Any]] = []

    incomplete_count = 0
    pending_recommendations_count = 0
    pending_reports_count = 0
    pending_reviews_count = 0
    completed_without_follow_up_count = 0

    # ---------------------------------------------------------
    # Assessment follow-up
    # ---------------------------------------------------------

    for assessment in assessments:

        if assessment.status == "in_progress":
            incomplete_count += 1

            items.append(
                {
                    "follow_up_type": "assessment_incomplete",
                    "priority": "medium",
                    "assessment_id": assessment.id,
                    "record_id": assessment.id,
                    "title": "Assessment still in progress",
                    "description": (
                        "The assessment has not yet been "
                        "completed."
                    ),
                    "action": (
                        "Complete the assessment when "
                        "appropriate."
                    ),
                    "started_at": (
                        assessment.started_at.isoformat()
                        if assessment.started_at
                        else None
                    ),
                }
            )

    # ---------------------------------------------------------
    # Pending recommendations
    # ---------------------------------------------------------

    for recommendation in recommendations:

        status = str(
            getattr(
                recommendation,
                "status",
                "",
            )
        ).lower()

        if status in {
            "pending",
            "pending_review",
            "awaiting_review",
        }:
            pending_recommendations_count += 1

            items.append(
                {
                    "follow_up_type": "recommendation_review",
                    "priority": "medium",
                    "assessment_id": (
                        recommendation.assessment_id
                    ),
                    "record_id": recommendation.id,
                    "title": (
                        getattr(
                            recommendation,
                            "title",
                            None,
                        )
                        or "Recommendation awaiting review"
                    ),
                    "description": (
                        "A recommendation is awaiting "
                        "follow-up or clinician review."
                    ),
                    "action": (
                        "Review and update the "
                        "recommendation status."
                    ),
                    "status": status,
                }
            )

    # ---------------------------------------------------------
    # Pending reports
    # ---------------------------------------------------------

    for report in reports:

        status = str(
            getattr(
                report,
                "status",
                "",
            )
        ).lower()

        if status in {
            "draft",
            "pending_review",
            "awaiting_review",
        }:
            pending_reports_count += 1

            items.append(
                {
                    "follow_up_type": "report_review",
                    "priority": "medium",
                    "assessment_id": report.assessment_id,
                    "record_id": report.id,
                    "title": (
                        getattr(
                            report,
                            "report_title",
                            None,
                        )
                        or "Report awaiting follow-up"
                    ),
                    "description": (
                        "An assessment report has not "
                        "completed its workflow."
                    ),
                    "action": (
                        "Review and update the report "
                        "workflow status."
                    ),
                    "status": status,
                }
            )

    # ---------------------------------------------------------
    # Pending clinician reviews
    # ---------------------------------------------------------

    reviewed_assessment_ids: set[int] = set()

    for review in reviews:

        reviewed_assessment_ids.add(
            review.assessment_id
        )

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
            pending_reviews_count += 1

            items.append(
                {
                    "follow_up_type": "clinician_review",
                    "priority": "medium",
                    "assessment_id": review.assessment_id,
                    "record_id": review.id,
                    "title": "Clinician review pending",
                    "description": (
                        "A clinician review record exists "
                        "but is not yet completed."
                    ),
                    "action": (
                        "Complete the clinician review "
                        "workflow."
                    ),
                    "status": review_status,
                }
            )

    # ---------------------------------------------------------
    # Completed assessments without follow-up activity
    # ---------------------------------------------------------

    recommendation_assessment_ids = {
        recommendation.assessment_id
        for recommendation in recommendations
    }

    report_assessment_ids = {
        report.assessment_id
        for report in reports
    }

    for assessment in assessments:

        if assessment.status != "completed":
            continue

        has_recommendation = (
            assessment.id
            in recommendation_assessment_ids
        )

        has_report = (
            assessment.id
            in report_assessment_ids
        )

        has_review = (
            assessment.id
            in reviewed_assessment_ids
        )

        if not (
            has_recommendation
            or has_report
            or has_review
        ):
            completed_without_follow_up_count += 1

            items.append(
                {
                    "follow_up_type": (
                        "completed_assessment_without_follow_up"
                    ),
                    "priority": "medium",
                    "assessment_id": assessment.id,
                    "record_id": assessment.id,
                    "title": (
                        "Completed assessment without "
                        "follow-up activity"
                    ),
                    "description": (
                        "The assessment is completed but "
                        "no recommendation, report, or "
                        "clinician review is recorded."
                    ),
                    "action": (
                        "Review the completed assessment "
                        "and record the appropriate "
                        "follow-up activity."
                    ),
                    "completed_at": (
                        assessment.completed_at.isoformat()
                        if assessment.completed_at
                        else None
                    ),
                }
            )

    # ---------------------------------------------------------
    # Latest assessment
    # ---------------------------------------------------------

    latest_assessment = assessments[0]

    latest_assessment_data = {
        "id": latest_assessment.id,
        "assessment_type": (
            latest_assessment.assessment_type
        ),
        "status": latest_assessment.status,
        "started_at": (
            latest_assessment.started_at.isoformat()
            if latest_assessment.started_at
            else None
        ),
        "completed_at": (
            latest_assessment.completed_at.isoformat()
            if latest_assessment.completed_at
            else None
        ),
    }

    # ---------------------------------------------------------
    # Overall follow-up status
    # ---------------------------------------------------------

    follow_up_count = len(items)

    if follow_up_count == 0:
        follow_up_status = "no_follow_up_required"
    elif (
        pending_reviews_count > 0
        or pending_recommendations_count > 0
        or pending_reports_count > 0
    ):
        follow_up_status = "follow_up_pending"
    else:
        follow_up_status = "follow_up_required"

    return {
        "patient_id": patient_id,
        "patient": {
            "patient_number": patient.patient_number,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "status": patient.status,
        },
        "assessment_count": len(assessments),
        "latest_assessment": latest_assessment_data,
        "follow_up_status": follow_up_status,
        "follow_up_count": follow_up_count,
        "counts": {
            "incomplete_assessments": incomplete_count,
            "pending_recommendations": (
                pending_recommendations_count
            ),
            "pending_reports": pending_reports_count,
            "pending_reviews": pending_reviews_count,
            "completed_without_follow_up": (
                completed_without_follow_up_count
            ),
        },
        "items": items,
    }