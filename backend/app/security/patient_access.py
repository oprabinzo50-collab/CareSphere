from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.patient_user_links import PatientUserLink
from app.models.user import User
from app.security.roles import normalize_role


def ensure_patient_access(
    patient_id: int,
    current_user: User,
    db: Session,
) -> None:
    role = normalize_role(current_user.role)

    if role in {"administrator", "clinician"}:
        return

    if role != "patient":
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access patient records",
        )

    link = db.scalar(
        select(PatientUserLink).where(
            PatientUserLink.user_id == current_user.id
        )
    )

    if link is None or link.patient_id != patient_id:
        raise HTTPException(
            status_code=403,
            detail="You can only access your own patient record",
        )
