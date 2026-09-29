from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment_sessions import AssessmentSession
from app.models.clinician_reviews import ClinicianReview
from app.models.patient import Patient
from app.models.recommendations import Recommendation
from app.models.reports import Report


def generate_patient_care_gaps(
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

    gaps: list[dict[str, Any]] = []

    # ---------------------------------------------------------
    # No assessment
    # ---------------------------------------------------------

    if not assessments:
        gaps.append(
            {
                "gap_type": "missing_assessment",
                "severity": "medium",
                "title": "No assessment recorded",
                "description": (
                    "No assessment session is currently "
                    "recorded for this patient."
                ),
                "assessment_id": None,
                "action": "Consider creating an assessment.",
            }
        )

        return {
            "patient_id": patient_id,
            "patient": {
                "patient_number": patient.patient_number,
                "first_name": patient.first_name,
                "last_name": patient.last_name,
                "status": patient.status,
            },
            "gap_count": len(gaps),
            "gaps": gaps,
            "status": "gaps_identified",
        }

    # ---------------------------------------------------------
    # Check each assessment
    # ---------------------------------------------------------

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

    recommendations_by_assessment: dict[
        int,
        list[Recommendation],
    ] = {}

    reports_by_assessment: dict[
        int,
        list[Report],
    ] = {}

    reviews_by_assessment: dict[
        int,
        list[ClinicianReview],
    ] = {}

    for recommendation in recommendations:
        recommendations_by_assessment.setdefault(
            recommendation.assessment_id,
            [],
        ).append(recommendation)

    for report in reports:
        reports_by_assessment.setdefault(
            report.assessment_id,
            [],
        ).append(report)

    for review in reviews:
        reviews_by_assessment.setdefault(
            review.assessment_id,
            [],
        ).append(review)

    # ---------------------------------------------------------
    # Assessment workflow gaps
    # ---------------------------------------------------------

    for assessment in assessments:

        assessment_recommendations = (
            recommendations_by_assessment.get(
                assessment.id,
                [],
            )
        )

        assessment_reports = (
            reports_by_assessment.get(
                assessment.id,
                [],
            )
        )

        assessment_reviews = (
            reviews_by_assessment.get(
                assessment.id,
                [],
            )
        )

        # -----------------------------------------------------
        # Assessment still in progress
        # -----------------------------------------------------

        if assessment.status == "in_progress":
            gaps.append(
                {
                    "gap_type": "assessment_incomplete",
                    "severity": "medium",
                    "title": "Assessment still in progress",
                    "description": (
                        "This assessment has not yet been "
                        "completed."
                    ),
                    "assessment_id": assessment.id,
                    "action": (
                        "Complete the assessment when "
                        "the required information is available."
                    ),
                }
            )

        # -----------------------------------------------------
        # Completed assessment without report
        # -----------------------------------------------------

        if (
            assessment.status == "completed"
            and not assessment_reports
        ):
            gaps.append(
                {
                    "gap_type": "missing_report",
                    "severity": "medium",
                    "title": "No report generated",
                    "description": (
                        "The assessment is completed but "
                        "does not have an associated report."
                    ),
                    "assessment_id": assessment.id,
                    "action": (
                        "Generate an assessment report "
                        "for clinical review."
                    ),
                }
            )

        # -----------------------------------------------------
        # Recommendations awaiting review
        # -----------------------------------------------------

        pending_recommendations = [
            recommendation
            for recommendation in assessment_recommendations
            if getattr(
                recommendation,
                "status",
                None,
            )
            in {
                "pending",
                "pending_review",
            }
        ]

        for recommendation in pending_recommendations:
            gaps.append(
                {
                    "gap_type": "recommendation_review_pending",
                    "severity": "medium",
                    "title": "Recommendation awaiting review",
                    "description": (
                        "A generated recommendation has "
                        "not yet completed clinician review."
                    ),
                    "assessment_id": assessment.id,
                    "record_id": recommendation.id,
                    "action": (
                        "Review the recommendation "
                        "and record a clinical decision."
                    ),
                }
            )

        # -----------------------------------------------------
        # Reports awaiting review
        # -----------------------------------------------------

        pending_reports = [
            report
            for report in assessment_reports
            if getattr(
                report,
                "status",
                None,
            )
            in {
                "pending_review",
            }
        ]

        for report in pending_reports:
            gaps.append(
                {
                    "gap_type": "report_review_pending",
                    "severity": "medium",
                    "title": "Report awaiting review",
                    "description": (
                        "An assessment report is awaiting "
                        "clinician review."
                    ),
                    "assessment_id": assessment.id,
                    "record_id": report.id,
                    "action": (
                        "Review the report and record "
                        "the review outcome."
                    ),
                }
            )

        # -----------------------------------------------------
        # Completed assessment without clinician review
        # -----------------------------------------------------

        if (
            assessment.status == "completed"
            and not assessment_reviews
        ):
            gaps.append(
                {
                    "gap_type": "missing_clinician_review",
                    "severity": "medium",
                    "title": "No clinician review recorded",
                    "description": (
                        "The assessment is completed but "
                        "no clinician review is recorded."
                    ),
                    "assessment_id": assessment.id,
                    "action": (
                        "Record clinician review when "
                        "clinical review is required."
                    ),
                }
            )

        # -----------------------------------------------------
        # Recommendation without report
        # -----------------------------------------------------

        if (
            assessment_recommendations
            and not assessment_reports
        ):
            gaps.append(
                {
                    "gap_type": "recommendation_without_report",
                    "severity": "low",
                    "title": "Recommendation without report",
                    "description": (
                        "Recommendations exist for this "
                        "assessment but no report is recorded."
                    ),
                    "assessment_id": assessment.id,
                    "action": (
                        "Generate or attach the appropriate "
                        "assessment report."
                    ),
                }
            )

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    severity_counts = {
        "high": 0,
        "medium": 0,
        "low": 0,
    }

    for gap in gaps:
        severity = gap.get("severity")

        if severity in severity_counts:
            severity_counts[severity] += 1

    if not gaps:
        overall_status = "no_gaps_identified"
    elif severity_counts["high"] > 0:
        overall_status = "high_priority_gaps"
    else:
        overall_status = "follow_up_required"

    return {
        "patient_id": patient_id,
        "patient": {
            "patient_number": patient.patient_number,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "status": patient.status,
        },
        "assessment_count": len(assessments),
        "gap_count": len(gaps),
        "severity_counts": severity_counts,
        "status": overall_status,
        "gaps": gaps,
    }