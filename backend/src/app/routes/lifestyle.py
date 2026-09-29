from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.lifestyle import Lifestyle
from app.models.patient import Patient
from app.models.user import User
from app.schemas.lifestyle import (
    LifestyleCreate,
    LifestyleResponse,
    LifestyleUpdate,
)
from app.security.permissions import require_roles


router = APIRouter(
    prefix="/patient",
    tags=["Lifestyle"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/{patient_id}/lifestyle",
    response_model=LifestyleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_lifestyle(
    patient_id: int,
    lifestyle_data: LifestyleCreate,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    patient = db.get(Patient, patient_id)

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    lifestyle = Lifestyle(
        patient_id=patient_id,
        **lifestyle_data.model_dump(),
        recorded_at=datetime.now(timezone.utc),
        recorded_by=current_user.id,
    )

    db.add(lifestyle)
    db.commit()
    db.refresh(lifestyle)

    return lifestyle


@router.get(
    "/{patient_id}/lifestyle",
    response_model=list[LifestyleResponse],
)
def list_lifestyle(
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
        select(Lifestyle)
        .where(Lifestyle.patient_id == patient_id)
        .order_by(Lifestyle.id.desc())
    )

    return db.scalars(statement).all()


@router.put(
    "/lifestyle/{lifestyle_id}",
    response_model=LifestyleResponse,
)
def update_lifestyle(
    lifestyle_id: int,
    lifestyle_data: LifestyleUpdate,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    lifestyle = db.get(Lifestyle, lifestyle_id)

    if lifestyle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lifestyle record not found",
        )

    update_data = lifestyle_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(lifestyle, field, value)

    lifestyle.recorded_at = datetime.now(timezone.utc)
    lifestyle.recorded_by = current_user.id

    db.commit()
    db.refresh(lifestyle)

    return lifestyle