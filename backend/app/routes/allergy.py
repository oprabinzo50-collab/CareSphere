from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.allergies import Allergy
from app.models.patient import Patient
from app.models.user import User
from app.schemas.allergy import (
    AllergyCreate,
    AllergyResponse,
    AllergyUpdate,
)
from app.security.permissions import require_roles


router = APIRouter(
    prefix="/patient",
    tags=["Allergies"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/{patient_id}/allergies",
    response_model=AllergyResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_allergy(
    patient_id: int,
    allergy_data: AllergyCreate,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    patient = db.get(Patient, patient_id)

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    allergy = Allergy(
        patient_id=patient_id,
        **allergy_data.model_dump(),
        recorded_at=datetime.now(timezone.utc),
        recorded_by=current_user.id,
    )

    db.add(allergy)
    db.commit()
    db.refresh(allergy)

    return allergy


@router.get(
    "/{patient_id}/allergies",
    response_model=list[AllergyResponse],
)
def list_allergies(
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
        select(Allergy)
        .where(Allergy.patient_id == patient_id)
        .order_by(Allergy.id.desc())
    )

    return db.scalars(statement).all()


@router.put(
    "/allergies/{allergy_id}",
    response_model=AllergyResponse,
)
def update_allergy(
    allergy_id: int,
    allergy_data: AllergyUpdate,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    allergy = db.get(Allergy, allergy_id)

    if allergy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Allergy record not found",
        )

    update_data = allergy_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(allergy, field, value)

    allergy.recorded_at = datetime.now(timezone.utc)
    allergy.recorded_by = current_user.id

    db.commit()
    db.refresh(allergy)

    return allergy