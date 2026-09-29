from typing import Any

from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.services.clinical_summary import (
    generate_patient_clinical_summary,
)
from app.services.care_gaps import (
    generate_patient_care_gaps,
)
from app.services.patient_follow_up import (
    generate_patient_follow_up,
)
from app.services.risk_trends import (
    generate_patient_risk_trends,
)
from typing import Any


def generate_patient_care_coordination(
    db: Session,
    patient_id: int,
) -> dict[str, Any]:

    patient = db.get(Patient, patient_id)

    if patient is None:
        raise ValueError("Patient not found")

    clinical_summary = generate_patient_clinical_summary(
        db=db,
        patient_id=patient_id,
    )

    risk_trends = generate_patient_risk_trends(
        db=db,
        patient_id=patient_id,
    )

    care_gaps = generate_patient_care_gaps(
        db=db,
        patient_id=patient_id,
    )

    follow_up = generate_patient_follow_up(
        db=db,
        patient_id=patient_id,
    )

    # ---------------------------------------------------------
    # Recent timeline activity
    # ---------------------------------------------------------

    timeline = clinical_summary.get(
        "timeline",
        [],
    )

    recent_activity = timeline[:10]

    # ---------------------------------------------------------
    # Coordination counts
    # ---------------------------------------------------------

    clinical_counts = clinical_summary.get(
        "counts",
        {},
    )

    gap_counts = care_gaps.get(
        "severity_counts",
        {},
    )

    follow_up_counts = follow_up.get(
        "counts",
        {},
    )

    coordination_counts = {
        "assessments": clinical_counts.get(
            "assessments",
            0,
        ),
        "health_concerns": clinical_counts.get(
            "health_concerns",
            0,
        ),
        "recommendations": clinical_counts.get(
            "recommendations",
            0,
        ),
        "reports": clinical_counts.get(
            "reports",
            0,
        ),
        "clinician_reviews": clinical_counts.get(
            "clinician_reviews",
            0,
        ),
        "care_gaps": care_gaps.get(
            "gap_count",
            0,
        ),
        "follow_up_items": follow_up.get(
            "follow_up_count",
            0,
        ),
        "medium_priority_gaps": gap_counts.get(
            "medium",
            0,
        ),
        "pending_recommendations": follow_up_counts.get(
            "pending_recommendations",
            0,
        ),
        "pending_reports": follow_up_counts.get(
            "pending_reports",
            0,
        ),
        "pending_reviews": follow_up_counts.get(
            "pending_reviews",
            0,
        ),
    }

    # ---------------------------------------------------------
    # Overall coordination status
    # ---------------------------------------------------------

    if care_gaps.get("status") == "high_priority_gaps":
        coordination_status = "attention_required"

    elif follow_up.get("follow_up_status") in {
        "follow_up_pending",
        "follow_up_required",
    }:
        coordination_status = "follow_up_required"

    elif care_gaps.get("gap_count", 0) > 0:
        coordination_status = "attention_required"

    else:
        coordination_status = "no_outstanding_items"

    # ---------------------------------------------------------
    # Latest assessment
    # ---------------------------------------------------------

    latest_assessment = clinical_summary.get(
        "latest_assessment"
    )

    # ---------------------------------------------------------
    # Latest risk
    # ---------------------------------------------------------

    risk_summary = clinical_summary.get(
        "risk_summary",
        {},
    )

    latest_risk = risk_summary.get(
        "latest"
    )

    return {
        "patient": clinical_summary.get(
            "patient"
        ),

        "coordination_status": coordination_status,

        "latest_assessment": latest_assessment,

        "risk_summary": {
            "latest": latest_risk,
            "trend": risk_summary.get(
                "trend"
            ),
            "highest_score": risk_summary.get(
                "highest_score"
            ),
            "lowest_score": risk_summary.get(
                "lowest_score"
            ),
            "assessment_count": risk_summary.get(
                "assessment_count",
                0,
            ),
        },

        "care_gaps": {
            "status": care_gaps.get(
                "status"
            ),
            "gap_count": care_gaps.get(
                "gap_count",
                0,
            ),
            "severity_counts": gap_counts,
            "items": care_gaps.get(
                "gaps",
                [],
            ),
        },

        "follow_up": {
            "status": follow_up.get(
                "follow_up_status"
            ),
            "count": follow_up.get(
                "follow_up_count",
                0,
            ),
            "counts": follow_up_counts,
            "items": follow_up.get(
                "items",
                [],
            ),
        },

        "clinical_records": (
            clinical_summary.get(
                "clinical_records",
                {},
            )
        ),

        "coordination_counts": coordination_counts,

        "recent_activity": recent_activity,
    }