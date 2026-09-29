from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.clinician_assignments import ClinicianAssignment
from app.models.patient import Patient
from app.models.user import User
from app.schemas.clinician_assignments import (
    ClinicianAssignmentCreate,
    ClinicianAssignmentResponse,
    ClinicianAssignmentSummary,
)
from app.security.permissions import require_roles


router = APIRouter(
    prefix="/clinician-assignments",
    tags=["Clinician Assignments"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


ALLOWED_CARE_ROLES = {
    "primary",
    "secondary",
}


ALLOWED_CLINICIAN_ROLES = {
    "clinician",
    "doctor",
    "medical_officer",
    "nurse",
    "administrator",
}


@router.post(
    "/patients/{patient_id}",
    response_model=ClinicianAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_clinician(
    patient_id: int,
    assignment_data: ClinicianAssignmentCreate,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    patient = db.get(
        Patient,
        patient_id,
    )

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    if str(patient.status).lower() != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Clinician cannot be assigned to an inactive patient",
        )

    care_role = assignment_data.care_role.strip().lower()

    if care_role not in ALLOWED_CARE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="care_role must be either 'primary' or 'secondary'",
        )

    clinician = db.get(
        User,
        assignment_data.clinician_id,
    )

    if clinician is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinician user not found",
        )

    if str(clinician.status).lower() != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Clinician account is not active",
        )

    clinician_role = str(
        clinician.role
    ).strip().lower()

    if clinician_role not in ALLOWED_CLINICIAN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected user does not have a clinician-capable role",
        )

    existing_assignment = db.scalar(
        select(ClinicianAssignment).where(
            ClinicianAssignment.patient_id == patient_id,
            ClinicianAssignment.clinician_id
            == assignment_data.clinician_id,
            ClinicianAssignment.status == "active",
        )
    )

    if existing_assignment is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This clinician is already actively assigned to the patient",
        )

    if care_role == "primary":
        existing_primary = db.scalar(
            select(ClinicianAssignment).where(
                ClinicianAssignment.patient_id == patient_id,
                ClinicianAssignment.care_role == "primary",
                ClinicianAssignment.status == "active",
            )
        )

        if existing_primary is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Patient already has an active primary clinician",
            )

    now = datetime.now(timezone.utc)

    assignment = ClinicianAssignment(
        patient_id=patient_id,
        clinician_id=assignment_data.clinician_id,
        assigned_by=current_user.id,
        care_role=care_role,
        status="active",
        assigned_at=now,
        ended_at=None,
        created_at=now,
        updated_at=now,
    )

    db.add(assignment)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The clinician assignment conflicts with an existing active assignment",
        )

    db.refresh(assignment)

    return assignment


@router.get(
    "/patients/{patient_id}",
    response_model=list[ClinicianAssignmentSummary],
)
def list_patient_clinicians(
    patient_id: int,
    active_only: bool = True,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    patient = db.get(
        Patient,
        patient_id,
    )

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    statement = select(
        ClinicianAssignment
    ).where(
        ClinicianAssignment.patient_id == patient_id
    )

    if active_only:
        statement = statement.where(
            ClinicianAssignment.status == "active"
        )

    statement = statement.order_by(
        ClinicianAssignment.care_role.asc(),
        ClinicianAssignment.assigned_at.desc(),
    )

    return db.scalars(statement).all()


@router.get(
    "/clinicians/{clinician_id}/patients",
    response_model=list[ClinicianAssignmentSummary],
)
def list_clinician_patients(
    clinician_id: int,
    active_only: bool = True,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    clinician = db.get(
        User,
        clinician_id,
    )

    if clinician is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinician user not found",
        )

    statement = select(
        ClinicianAssignment
    ).where(
        ClinicianAssignment.clinician_id == clinician_id
    )

    if active_only:
        statement = statement.where(
            ClinicianAssignment.status == "active"
        )

    statement = statement.order_by(
        ClinicianAssignment.assigned_at.desc()
    )

    return db.scalars(statement).all()


@router.get(
    "/{assignment_id}",
    response_model=ClinicianAssignmentResponse,
)
def get_clinician_assignment(
    assignment_id: int,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    assignment = db.get(
        ClinicianAssignment,
        assignment_id,
    )

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinician assignment not found",
        )

    return assignment


@router.patch(
    "/{assignment_id}/deactivate",
    response_model=ClinicianAssignmentResponse,
)
def deactivate_clinician_assignment(
    assignment_id: int,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    assignment = db.get(
        ClinicianAssignment,
        assignment_id,
    )

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinician assignment not found",
        )

    if assignment.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Clinician assignment is already inactive",
        )

    now = datetime.now(timezone.utc)

    assignment.status = "inactive"
    assignment.ended_at = now
    assignment.updated_at = now

    db.commit()
    db.refresh(assignment)

    return assignment