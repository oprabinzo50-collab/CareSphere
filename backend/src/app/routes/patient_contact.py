from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.patient_contacts import PatientContact
from app.models.patient import Patient
from app.models.user import User
from app.schemas.patient_contact import (
    PatientContactCreate,
    PatientContactResponse,
    PatientContactUpdate,
)
from app.security.permissions import require_roles


router = APIRouter(
    prefix="/patients",
    tags=["Patient Contacts"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/{patient_id}/contacts",
    response_model=PatientContactResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_patient_contact(
    patient_id: int,
    contact_data: PatientContactCreate,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    patient = db.get(Patient, patient_id)

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    now = datetime.now(timezone.utc)

    contact = PatientContact(
        patient_id=patient_id,
        **contact_data.model_dump(),
        created_at=now,
        updated_at=now,
    )

    db.add(contact)
    db.commit()
    db.refresh(contact)

    return contact


@router.get(
    "/{patient_id}/contacts",
    response_model=list[PatientContactResponse],
)
def list_patient_contacts(
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
        select(PatientContact)
        .where(PatientContact.patient_id == patient_id)
        .order_by(PatientContact.id.desc())
    )

    return db.scalars(statement).all()


@router.put(
    "/contacts/{contact_id}",
    response_model=PatientContactResponse,
)
def update_patient_contact(
    contact_id: int,
    contact_data: PatientContactUpdate,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    contact = db.get(PatientContact, contact_id)

    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient contact not found",
        )

    update_data = contact_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(contact, field, value)

    contact.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(contact)

    return contact
@router.delete(
    "/contacts/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_patient_contact(
    contact_id: int,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    contact = db.get(PatientContact, contact_id)

    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient contact not found",
        )

    db.delete(contact)
    db.commit()

    return None