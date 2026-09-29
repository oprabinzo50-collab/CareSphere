from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User
from app.security.dependencies import get_current_user
from app.security.patient_access import ensure_patient_access
from app.services.patient_activity_feed import (
    generate_patient_activity_feed,
)


router = APIRouter(
    prefix="/patients",
    tags=["Patient Activity Feed"],
)


def get_db():
    ensure_patient_access(patient_id, current_user, db)
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get("/{patient_id}/activity-feed")
def get_patient_activity_feed(
    patient_id: int,
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return generate_patient_activity_feed(
            db=db,
            patient_id=patient_id,
            limit=limit,
            offset=offset,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )