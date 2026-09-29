from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.medications import Medication
from app.models.patient import Patient
from app.models.user import User
from app.schemas.medication import (
    MedicationCreate,
    MedicationResponse,
    MedicationUpdate,
)
from app.security.permissions import require_roles


router = APIRouter(
    prefix="/patient",
    tags=["Medications"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/{patient_id}/medications",
    response_model=MedicationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_medication(
    patient_id: int,
    medication_data: MedicationCreate,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    patient = db.get(Patient, patient_id)

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    medication = Medication(
        patient_id=patient_id,
        **medication_data.model_dump(),
        recorded_at=datetime.now(timezone.utc),
        recorded_by=current_user.id,
    )

    db.add(medication)
    db.commit()
    db.refresh(medication)

    return medication


@router.get(
    "/{patient_id}/medications",
    response_model=list[MedicationResponse],
)
def list_medications(
    patient_id: int,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    patient = db.get(Patient, patient_id)

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    statement = (
        select(Medication)
        .where(Medication.patient_id == patient_id)
        .order_by(Medication.id.desc())
    )

    return db.scalars(statement).all()


@router.put(
    "/medications/{medication_id}",
    response_model=MedicationResponse,
)
def update_medication(
    medication_id: int,
    medication_data: MedicationUpdate,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    medication = db.get(Medication, medication_id)

    if medication is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication record not found",
        )

    update_data = medication_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(medication, field, value)

    medication.recorded_at = datetime.now(timezone.utc)
    medication.recorded_by = current_user.id

    db.commit()
    db.refresh(medication)

    return medication