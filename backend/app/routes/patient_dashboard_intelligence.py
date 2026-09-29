from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User
from app.security.dependencies import get_current_user
from app.security.patient_access import ensure_patient_access
from app.services.patient_dashboard_intelligence import (
    generate_patient_dashboard_intelligence,
)


router = APIRouter(
    prefix="/patients",
    tags=["Patient Dashboard Intelligence"],
)


def get_db():
    ensure_patient_access(patient_id, current_user, db)
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get("/{patient_id}/dashboard-intelligence")
def get_patient_dashboard_intelligence(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return generate_patient_dashboard_intelligence(
            db=db,
            patient_id=patient_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )