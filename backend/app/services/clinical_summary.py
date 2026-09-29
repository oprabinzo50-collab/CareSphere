from typing import Any

from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.services.patient_timeline import generate_patient_timeline
from app.services.risk_trends import generate_patient_risk_trends


def generate_patient_clinical_summary(
    db: Session,
    patient_id: int,
) -> dict[str, Any]:

    patient = db.get(Patient, patient_id)

    if patient is None:
        raise ValueError("Patient not found")

    timeline_result = generate_patient_timeline(
        db=db,
        patient_id=patient_id,
    )

    risk_result = generate_patient_risk_trends(
        db=db,
        patient_id=patient_id,
    )

    timeline = timeline_result.get(
        "timeline",
        [],
    )

    # ---------------------------------------------------------
    # Group timeline events
    # ---------------------------------------------------------

    grouped: dict[str, list[dict[str, Any]]] = {}

    for event in timeline:
        event_type = event.get(
            "event_type",
            "unknown",
        )

        grouped.setdefault(
            event_type,
            [],
        ).append(event)

    # ---------------------------------------------------------
    # Latest record helper
    # ---------------------------------------------------------

    def latest_event(
        event_type: str,
    ) -> dict[str, Any] | None:

        events = grouped.get(event_type, [])

        if not events:
            return None

        return events[0]

    # ---------------------------------------------------------
    # Active/current clinical information
    # ---------------------------------------------------------

    assessments = grouped.get(
        "assessment",
        [],
    )

    health_concerns = grouped.get(
        "health_concern",
        []
    )

    recommendations = grouped.get(
        "recommendation",
        []
    )

    reports = grouped.get(
        "report",
        []
    )

    clinician_reviews = grouped.get(
        "clinician_review",
        []
    )

    medications = grouped.get(
        "medication",
        []
    )

    allergies = grouped.get(
        "allergy",
        []
    )

    medical_history = grouped.get(
        "medical_history",
        []
    )

    vital_signs = grouped.get(
        "vital_sign",
        []
    )

    lifestyles = grouped.get(
        "lifestyle",
        []
    )

    # ---------------------------------------------------------
    # Latest assessment
    # ---------------------------------------------------------

    latest_assessment = (
        assessments[0]
        if assessments
        else None
    )

    # ---------------------------------------------------------
    # Latest risk result
    # ---------------------------------------------------------

    latest_risk = risk_result.get(
        "latest"
    )

    # ---------------------------------------------------------
    # Counts
    # ---------------------------------------------------------

    counts = {
        "assessments": len(assessments),
        "health_concerns": len(health_concerns),
        "recommendations": len(recommendations),
        "reports": len(reports),
        "clinician_reviews": len(
            clinician_reviews
        ),
        "medications": len(medications),
        "allergies": len(allergies),
        "medical_history": len(
            medical_history
        ),
        "vital_sign_records": len(
            vital_signs
        ),
        "lifestyle_records": len(
            lifestyles
        ),
    }

    return {
        "patient": {
            "id": patient.id,
            "patient_number": patient.patient_number,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "date_of_birth": (
                patient.date_of_birth.isoformat()
                if patient.date_of_birth
                else None
            ),
            "sex": patient.sex,
            "marital_status": patient.marital_status,
            "occupation": patient.occupation,
            "preferred_language": patient.preferred_language,
            "residence": patient.residence,
            "district": patient.district,
            "country": patient.country,
            "status": patient.status,
        },

        "latest_assessment": latest_assessment,

        "risk_summary": {
            "latest": latest_risk,
            "trend": risk_result.get(
                "trend"
            ),
            "highest_score": risk_result.get(
                "highest_risk_score"
            ),
            "lowest_score": risk_result.get(
                "lowest_risk_score"
            ),
            "assessment_count": risk_result.get(
                "assessment_count",
                0,
            ),
        },

        "current_clinical_information": {
            "latest_vital_signs": latest_event(
                "vital_sign"
            ),
            "latest_lifestyle": latest_event(
                "lifestyle"
            ),
            "latest_medication": latest_event(
                "medication"
            ),
            "latest_allergy": latest_event(
                "allergy"
            ),
            "latest_medical_history": latest_event(
                "medical_history"
            ),
        },

        "clinical_records": {
            "health_concerns": health_concerns,
            "recommendations": recommendations,
            "reports": reports,
            "clinician_reviews": clinician_reviews,
        },

        "counts": counts,

        "timeline": timeline,
    }