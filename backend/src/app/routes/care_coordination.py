from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User
from app.security.permissions import require_roles
from app.services.care_coordination import (
    generate_patient_care_coordination,
)


router = APIRouter(
    prefix="/patients",
    tags=["Care Coordination"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get("/{patient_id}/care-coordination")
def get_patient_care_coordination(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("administrator", "clinician")),
):
    try:
        return generate_patient_care_coordination(
            db=db,
            patient_id=patient_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )