from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.patient import Patient


def search_patients(
    db: Session,
    search: str | None = None,
    patient_number: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    district: str | None = None,
    sex: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:

    stmt = select(Patient)

    # ---------------------------------------------------------
    # General search
    # ---------------------------------------------------------

    if search:
        search_value = f"%{search.strip()}%"

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

    # ---------------------------------------------------------
    # Specific filters
    # ---------------------------------------------------------

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

    results: list[dict[str, Any]] = []

    for patient in patients:
        results.append(
            {
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
                "preferred_language": (
                    patient.preferred_language
                ),
                "residence": patient.residence,
                "district": patient.district,
                "country": patient.country,
                "status": patient.status,
                "created_at": (
                    patient.created_at.isoformat()
                    if patient.created_at
                    else None
                ),
                "updated_at": (
                    patient.updated_at.isoformat()
                    if patient.updated_at
                    else None
                ),
            }
        )

    return {
        "count": len(results),
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
        "patients": results,
    }