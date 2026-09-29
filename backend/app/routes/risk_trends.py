from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.patient import Patient
from app.models.user import User
from app.security.permissions import require_roles
from app.services.risk_trends import generate_patient_risk_trends


router = APIRouter(
    prefix="/patients",
    tags=["Risk Trends"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get("/{patient_id}/risk-trends")
def get_patient_risk_trends(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("administrator", "clinician")),
):
    patient = db.get(Patient, patient_id)

    if patient is None:
        raise HTTPException(
            status_code=404,
            detail="Patient not found",
        )

    return generate_patient_risk_trends(
        db=db,
        patient_id=patient_id,
    )