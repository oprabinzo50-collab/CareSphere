from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.patient import Patient
from app.models.user import User
from app.security.permissions import require_roles
from app.services.notification_intelligence_audit import (
    get_notification_intelligence_audit_logs,
    serialize_notification_intelligence_audit,
)


router = APIRouter(
    prefix="/patients",
    tags=["Notification Intelligence Audit"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get(
    "/{patient_id}/notification-intelligence-audit"
)
def get_notification_intelligence_audit(
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
    current_user: User = Depends(require_roles("administrator", "clinician")),
):
    patient = db.get(
        Patient,
        patient_id,
    )

    if patient is None:
        raise HTTPException(
            status_code=404,
            detail="Patient not found",
        )

    audit_logs = (
        get_notification_intelligence_audit_logs(
            db=db,
            patient_id=patient_id,
            limit=limit,
            offset=offset,
        )
    )

    return {
        "patient": {
            "id": patient.id,
            "patient_number": (
                patient.patient_number
            ),
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "status": patient.status,
        },
        "pagination": {
            "limit": limit,
            "offset": offset,
            "returned_count": len(
                audit_logs
            ),
        },
        "audit_logs": [
            serialize_notification_intelligence_audit(
                audit_log
            )
            for audit_log in audit_logs
        ],
    }