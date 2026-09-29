from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.services.care_coordination import (
    generate_patient_care_coordination,
)
from app.services.patient_timeline import (
    generate_patient_timeline,
)
from app.services.risk_trends import (
    generate_patient_risk_trends,
)


def generate_patient_dashboard(
    db: Session,
    search: str | None = None,
    patient_number: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    district: str | None = None,
    sex: str | None = None,
    status: str | None = None,
    limit: int = 25,
    offset: int = 0,
) -> dict[str, Any]:

    stmt = select(Patient)

    # ---------------------------------------------------------
    # Filters
    # ---------------------------------------------------------

    if search:
        search_value = f"%{search.strip()}%"

        from sqlalchemy import or_

        stmt = stmt.where(
            or_(
                Patient.patient_number.ilike(
                    search_value
                ),
                Patient.first_name.ilike(
                    search_value
                ),
                Patient.last_name.ilike(
                    search_value
                ),
            )
        )

    if patient_number:
        stmt = stmt.where(
            Patient.patient_number.ilike(
                f"%{patient_number.strip()}%"
            )
        )

    if first_name:
        stmt = stmt.where(
            Patient.first_name.ilike(
                f"%{first_name.strip()}%"
            )
        )

    if last_name:
        stmt = stmt.where(
            Patient.last_name.ilike(
                f"%{last_name.strip()}%"
            )
        )

    if district:
        stmt = stmt.where(
            Patient.district.ilike(
                f"%{district.strip()}%"
            )
        )

    if sex:
        stmt = stmt.where(
            Patient.sex.ilike(
                sex.strip()
            )
        )

    if status:
        stmt = stmt.where(
            Patient.status.ilike(
                status.strip()
            )
        )

    # ---------------------------------------------------------
    # Ordering and pagination
    # ---------------------------------------------------------

    stmt = (
        stmt
        .order_by(
            Patient.last_name.asc(),
            Patient.first_name.asc(),
        )
        .offset(offset)
        .limit(limit)
    )

    patients = list(
        db.scalars(stmt).all()
    )

    dashboard_patients: list[dict[str, Any]] = []

    # ---------------------------------------------------------
    # Build dashboard information
    # ---------------------------------------------------------

    for patient in patients:

        timeline_result = generate_patient_timeline(
            db=db,
            patient_id=patient.id,
        )

        timeline = timeline_result.get(
            "timeline",
            [],
        )

        risk_result = generate_patient_risk_trends(
            db=db,
            patient_id=patient.id,
        )

        coordination_result = (
            generate_patient_care_coordination(
                db=db,
                patient_id=patient.id,
            )
        )

        latest_activity = (
            timeline[0]
            if timeline
            else None
        )

        latest_assessment = (
            risk_result.get("latest")
        )

        care_gaps = coordination_result.get(
            "care_gaps",
            {},
        )

        follow_up = coordination_result.get(
            "follow_up",
            {},
        )

        dashboard_patients.append(
            {
                "patient": {
                    "id": patient.id,
                    "patient_number": (
                        patient.patient_number
                    ),
                    "first_name": patient.first_name,
                    "last_name": patient.last_name,
                    "date_of_birth": (
                        patient.date_of_birth.isoformat()
                        if patient.date_of_birth
                        else None
                    ),
                    "sex": patient.sex,
                    "district": patient.district,
                    "status": patient.status,
                },

                "latest_assessment": (
                    latest_assessment
                ),

                "risk": {
                    "latest": latest_assessment,
                    "trend": risk_result.get(
                        "trend"
                    ),
                    "highest_score": (
                        risk_result.get(
                            "highest_risk_score"
                        )
                    ),
                    "lowest_score": (
                        risk_result.get(
                            "lowest_risk_score"
                        )
                    ),
                },

                "care_coordination": {
                    "status": (
                        coordination_result.get(
                            "coordination_status"
                        )
                    ),
                    "care_gap_count": (
                        care_gaps.get(
                            "gap_count",
                            0,
                        )
                    ),
                    "follow_up_count": (
                        follow_up.get(
                            "count",
                            0,
                        )
                    ),
                    "follow_up_status": (
                        follow_up.get(
                            "status"
                        )
                    ),
                },

                "latest_activity": (
                    latest_activity
                ),
            }
        )

    return {
        "count": len(
            dashboard_patients
        ),
        "limit": limit,
        "offset": offset,

        "filters": {
            "search": search,
            "patient_number": patient_number,
            "first_name": first_name,
            "last_name": last_name,
            "district": district,
            "sex": sex,
            "status": status,
        },

        "patients": dashboard_patients,
    }