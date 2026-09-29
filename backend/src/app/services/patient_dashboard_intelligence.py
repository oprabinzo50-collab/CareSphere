from typing import Any

from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.services.care_coordination import (
    generate_patient_care_coordination,
)
from app.services.clinical_summary import (
    generate_patient_clinical_summary,
)
from app.services.patient_timeline import (
    generate_patient_timeline,
)
from app.services.risk_trends import (
    generate_patient_risk_trends,
)


def generate_patient_dashboard_intelligence(
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

    coordination = generate_patient_care_coordination(
        db=db,
        patient_id=patient_id,
    )

    timeline_result = generate_patient_timeline(
        db=db,
        patient_id=patient_id,
    )

    timeline = timeline_result.get(
        "timeline",
        [],
    )

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

    # ---------------------------------------------------------
    # Clinical records
    # ---------------------------------------------------------

    clinical_records = clinical_summary.get(
        "clinical_records",
        {},
    )

    # ---------------------------------------------------------
    # Care gaps
    # ---------------------------------------------------------

    care_gaps = coordination.get(
        "care_gaps",
        {},
    )

    # ---------------------------------------------------------
    # Follow-up
    # ---------------------------------------------------------

    follow_up = coordination.get(
        "follow_up",
        {},
    )

    # ---------------------------------------------------------
    # Recent activity
    # ---------------------------------------------------------

    recent_activity = timeline[:10]

    # ---------------------------------------------------------
    # Dashboard counts
    # ---------------------------------------------------------

    counts = clinical_summary.get(
        "counts",
        {},
    )

    coordination_counts = coordination.get(
        "coordination_counts",
        {},
    )

    dashboard_counts = {
        "assessments": counts.get(
            "assessments",
            0,
        ),
        "health_concerns": counts.get(
            "health_concerns",
            0,
        ),
        "recommendations": counts.get(
            "recommendations",
            0,
        ),
        "reports": counts.get(
            "reports",
            0,
        ),
        "clinician_reviews": counts.get(
            "clinician_reviews",
            0,
        ),
        "medications": counts.get(
            "medications",
            0,
        ),
        "allergies": counts.get(
            "allergies",
            0,
        ),
        "medical_history": counts.get(
            "medical_history",
            0,
        ),
        "vital_sign_records": counts.get(
            "vital_sign_records",
            0,
        ),
        "lifestyle_records": counts.get(
            "lifestyle_records",
            0,
        ),
        "care_gaps": care_gaps.get(
            "gap_count",
            0,
        ),
        "follow_up_items": follow_up.get(
            "count",
            0,
        ),
        "pending_recommendations": (
            coordination_counts.get(
                "pending_recommendations",
                0,
            )
        ),
        "pending_reports": (
            coordination_counts.get(
                "pending_reports",
                0,
            )
        ),
        "pending_reviews": (
            coordination_counts.get(
                "pending_reviews",
                0,
            )
        ),
    }

    # ---------------------------------------------------------
    # Dashboard status
    # ---------------------------------------------------------

    dashboard_status = coordination.get(
        "coordination_status",
        "no_outstanding_items",
    )

    return {
        "patient": clinical_summary.get(
            "patient"
        ),

        "dashboard_status": dashboard_status,

        "overview": {
            "latest_assessment": latest_assessment,
            "latest_risk": latest_risk,
            "risk_trend": risk_summary.get(
                "trend"
            ),
            "assessment_count": risk_summary.get(
                "assessment_count",
                0,
            ),
        },

        "care_coordination": {
            "status": dashboard_status,
            "care_gaps": care_gaps,
            "follow_up": follow_up,
        },

        "clinical_information": {
            "latest_vital_signs": (
                clinical_summary
                .get(
                    "current_clinical_information",
                    {},
                )
                .get(
                    "latest_vital_signs"
                )
            ),
            "latest_lifestyle": (
                clinical_summary
                .get(
                    "current_clinical_information",
                    {},
                )
                .get(
                    "latest_lifestyle"
                )
            ),
            "latest_medication": (
                clinical_summary
                .get(
                    "current_clinical_information",
                    {},
                )
                .get(
                    "latest_medication"
                )
            ),
            "latest_allergy": (
                clinical_summary
                .get(
                    "current_clinical_information",
                    {},
                )
                .get(
                    "latest_allergy"
                )
            ),
            "latest_medical_history": (
                clinical_summary
                .get(
                    "current_clinical_information",
                    {},
                )
                .get(
                    "latest_medical_history"
                )
            ),
        },

        "clinical_records": clinical_records,

        "risk_history": {
            "assessment_count": risk_trends.get(
                "assessment_count",
                0,
            ),
            "trend": risk_trends.get(
                "trend"
            ),
            "highest_risk_score": (
                risk_trends.get(
                    "highest_risk_score"
                )
            ),
            "lowest_risk_score": (
                risk_trends.get(
                    "lowest_risk_score"
                )
            ),
            "assessments": risk_trends.get(
                "assessments",
                [],
            ),
        },

        "counts": dashboard_counts,

        "recent_activity": recent_activity,
    }