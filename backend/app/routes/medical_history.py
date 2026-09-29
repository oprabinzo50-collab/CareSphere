from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.medical_history import MedicalHistory
from app.models.patient import Patient
from app.models.user import User
from app.schemas.medical_history import (
    MedicalHistoryCreate,
    MedicalHistoryResponse,
    MedicalHistoryUpdate,
)
from app.security.permissions import require_roles


router = APIRouter(
    prefix="/patient",
    tags=["Medical History"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/{patient_id}/medical-history",
    response_model=MedicalHistoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_medical_history(
    patient_id: int,
    history_data: MedicalHistoryCreate,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    patient = db.get(Patient, patient_id)

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    history = MedicalHistory(
        patient_id=patient_id,
        **history_data.model_dump(),
        recorded_at=datetime.now(timezone.utc),
        recorded_by=current_user.id,
    )

    db.add(history)
    db.commit()
    db.refresh(history)

    return history


@router.get(
    "/{patient_id}/medical-history",
    response_model=list[MedicalHistoryResponse],
)
def list_medical_history(
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
        select(MedicalHistory)
        .where(MedicalHistory.patient_id == patient_id)
        .order_by(MedicalHistory.id.desc())
    )

    return db.scalars(statement).all()


@router.put(
    "/medical-history/{history_id}",
    response_model=MedicalHistoryResponse,
)
def update_medical_history(
    history_id: int,
    history_data: MedicalHistoryUpdate,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    history = db.get(MedicalHistory, history_id)

    if history is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical history record not found",
        )

    update_data = history_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(history, field, value)

    history.recorded_at = datetime.now(timezone.utc)
    history.recorded_by = current_user.id

    db.commit()
    db.refresh(history)

    return history