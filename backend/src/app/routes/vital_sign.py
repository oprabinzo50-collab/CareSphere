from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.assessment_sessions import AssessmentSession
from app.models.patient import Patient
from app.models.user import User
from app.models.vital_signs import VitalSign
from app.schemas.vital_sign import (
    VitalSignCreate,
    VitalSignResponse,
    VitalSignUpdate,
)
from app.security.permissions import require_roles


router = APIRouter(
    prefix="/patient",
    tags=["Vital Signs"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/{patient_id}/vital-signs",
    response_model=VitalSignResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_vital_sign(
    patient_id: int,
    vital_data: VitalSignCreate,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    patient = db.get(Patient, patient_id)

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    if vital_data.assessment_id is not None:
        assessment = db.get(
            AssessmentSession,
            vital_data.assessment_id,
        )

        if assessment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment session not found",
            )

        if assessment.patient_id != patient_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assessment does not belong to this patient",
            )

    now = datetime.now(timezone.utc)

    vital_sign = VitalSign(
        patient_id=patient_id,
        **vital_data.model_dump(),
        recorded_at=now,
        recorded_by=current_user.id,
    )

    db.add(vital_sign)
    db.commit()
    db.refresh(vital_sign)

    return vital_sign


@router.get(
    "/{patient_id}/vital-signs",
    response_model=list[VitalSignResponse],
)
def list_vital_signs(
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
        select(VitalSign)
        .where(VitalSign.patient_id == patient_id)
        .order_by(VitalSign.id.desc())
    )

    return db.scalars(statement).all()


@router.put(
    "/vital-signs/{vital_sign_id}",
    response_model=VitalSignResponse,
)
def update_vital_sign(
    vital_sign_id: int,
    vital_data: VitalSignUpdate,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    vital_sign = db.get(VitalSign, vital_sign_id)

    if vital_sign is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vital sign record not found",
        )

    update_data = vital_data.model_dump(
        exclude_unset=True
    )

    if "assessment_id" in update_data:
        assessment_id = update_data["assessment_id"]

        if assessment_id is not None:
            assessment = db.get(
                AssessmentSession,
                assessment_id,
            )

            if assessment is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Assessment session not found",
                )

            if assessment.patient_id != vital_sign.patient_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Assessment does not belong to this patient",
                )

    for field, value in update_data.items():
        setattr(vital_sign, field, value)

    vital_sign.recorded_at = datetime.now(timezone.utc)
    vital_sign.recorded_by = current_user.id

    db.commit()
    db.refresh(vital_sign)

    return vital_sign