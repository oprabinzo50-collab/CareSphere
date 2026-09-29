from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.clinician_assignments import ClinicianAssignment
from app.models.patient import Patient
from app.models.user import User
from app.schemas.care_team_intelligence import (
    AssignmentRoleUpdate,
    CareCoverageGap,
    CareCoverageOverview,
    CareTeamActivity,
    CareTeamMember,
    CareTeamOperationalStatus,
    ClinicianDirectoryEntry,
    ClinicianWorkloadSummary,
    PatientCareTeamSummary,
    PrimaryClinicianReplacement,
)
from app.security.permissions import require_roles


router = APIRouter(
    prefix="/care-team-intelligence",
    tags=["Care Team Intelligence"],
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


def build_patient_name(patient: Patient) -> str:
    return f"{patient.first_name} {patient.last_name}".strip()


def validate_clinician(
    clinician: User | None,
) -> None:
    if clinician is None:
        raise HTTPException(
            status_code=404,
            detail="Clinician user not found",
        )

    if str(clinician.status).lower() != "active":
        raise HTTPException(
            status_code=400,
            detail="Clinician account is not active",
        )

    clinician_role = str(clinician.role).strip().lower()

    if clinician_role not in ALLOWED_CLINICIAN_ROLES:
        raise HTTPException(
            status_code=400,
            detail="Selected user does not have a clinician-capable role",
        )


def get_active_assignments_for_patient(
    patient_id: int,
    db: Session,
) -> list[ClinicianAssignment]:
    statement = (
        select(ClinicianAssignment)
        .where(
            ClinicianAssignment.patient_id == patient_id,
            ClinicianAssignment.status == "active",
        )
        .order_by(
            ClinicianAssignment.care_role.asc(),
            ClinicianAssignment.assigned_at.asc(),
        )
    )

    return list(db.scalars(statement).all())


@router.get(
    "/patients/{patient_id}/summary",
    response_model=PatientCareTeamSummary,
)
def get_patient_care_team_summary(
    patient_id: int,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    patient = db.get(Patient, patient_id)

    if patient is None:
        raise HTTPException(
            status_code=404,
            detail="Patient not found",
        )

    statement = (
        select(ClinicianAssignment, User)
        .join(
            User,
            User.id == ClinicianAssignment.clinician_id,
        )
        .where(
            ClinicianAssignment.patient_id == patient_id,
            ClinicianAssignment.status == "active",
        )
        .order_by(
            ClinicianAssignment.care_role.asc(),
            ClinicianAssignment.assigned_at.asc(),
        )
    )

    results = db.execute(statement).all()

    members = [
        CareTeamMember(
            assignment_id=assignment.id,
            clinician_id=clinician.id,
            clinician_name=clinician.full_name,
            clinician_role=clinician.role,
            care_role=assignment.care_role,
            assigned_at=assignment.assigned_at,
        )
        for assignment, clinician in results
    ]

    primary_clinician = next(
        (
            member
            for member in members
            if member.care_role == "primary"
        ),
        None,
    )

    secondary_clinicians = [
        member
        for member in members
        if member.care_role == "secondary"
    ]

    if primary_clinician is not None:
        coverage_status = "covered"
    elif members:
        coverage_status = "partial"
    else:
        coverage_status = "uncovered"

    return PatientCareTeamSummary(
        patient_id=patient_id,
        active_clinician_count=len(members),
        has_primary_clinician=primary_clinician is not None,
        primary_clinician=primary_clinician,
        secondary_clinicians=secondary_clinicians,
        care_coverage_status=coverage_status,
    )


@router.get(
    "/patients/{patient_id}/operational-status",
    response_model=CareTeamOperationalStatus,
)
def get_patient_care_team_operational_status(
    patient_id: int,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    patient = db.get(Patient, patient_id)

    if patient is None:
        raise HTTPException(
            status_code=404,
            detail="Patient not found",
        )

    assignments = get_active_assignments_for_patient(
        patient_id,
        db,
    )

    has_primary = any(
        assignment.care_role == "primary"
        for assignment in assignments
    )

    has_secondary = any(
        assignment.care_role == "secondary"
        for assignment in assignments
    )

    if has_primary:
        coverage_status = "covered"
        operational_status = "ready"
        action_required = False
    elif has_secondary:
        coverage_status = "partial"
        operational_status = "primary_clinician_required"
        action_required = True
    else:
        coverage_status = "uncovered"
        operational_status = "care_team_required"
        action_required = True

    return CareTeamOperationalStatus(
        patient_id=patient_id,
        active_clinician_count=len(assignments),
        has_primary_clinician=has_primary,
        has_secondary_clinicians=has_secondary,
        care_coverage_status=coverage_status,
        operational_status=operational_status,
        action_required=action_required,
    )


@router.get(
    "/clinicians/directory",
    response_model=list[ClinicianDirectoryEntry],
)
def get_clinician_directory(
    active_only: bool = True,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    statement = select(User)

    if active_only:
        statement = statement.where(
            User.status == "active"
        )

    statement = statement.order_by(User.full_name.asc())

    users = db.scalars(statement).all()

    clinicians = [
        user
        for user in users
        if str(user.role).strip().lower()
        in ALLOWED_CLINICIAN_ROLES
    ]

    if not clinicians:
        return []

    clinician_ids = [
        clinician.id
        for clinician in clinicians
    ]

    assignments = db.scalars(
        select(ClinicianAssignment).where(
            ClinicianAssignment.clinician_id.in_(clinician_ids),
            ClinicianAssignment.status == "active",
        )
    ).all()

    assignments_by_clinician: dict[
        int,
        list[ClinicianAssignment],
    ] = {}

    for assignment in assignments:
        assignments_by_clinician.setdefault(
            assignment.clinician_id,
            [],
        ).append(assignment)

    return [
        ClinicianDirectoryEntry(
            clinician_id=clinician.id,
            clinician_name=clinician.full_name,
            role=clinician.role,
            status=clinician.status,
            active_patient_count=len(
                assignments_by_clinician.get(
                    clinician.id,
                    [],
                )
            ),
            primary_patient_count=sum(
                assignment.care_role == "primary"
                for assignment in assignments_by_clinician.get(
                    clinician.id,
                    [],
                )
            ),
            secondary_patient_count=sum(
                assignment.care_role == "secondary"
                for assignment in assignments_by_clinician.get(
                    clinician.id,
                    [],
                )
            ),
        )
        for clinician in clinicians
    ]


@router.patch(
    "/assignments/{assignment_id}/role",
    response_model=PatientCareTeamSummary,
)
def update_assignment_role(
    assignment_id: int,
    role_data: AssignmentRoleUpdate,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    assignment = db.get(
        ClinicianAssignment,
        assignment_id,
    )

    if assignment is None:
        raise HTTPException(
            status_code=404,
            detail="Clinician assignment not found",
        )

    if assignment.status != "active":
        raise HTTPException(
            status_code=400,
            detail="Only active assignments can have their role changed",
        )

    care_role = role_data.care_role.strip().lower()

    if care_role not in ALLOWED_CARE_ROLES:
        raise HTTPException(
            status_code=400,
            detail="care_role must be either 'primary' or 'secondary'",
        )

    if care_role == assignment.care_role:
        return get_patient_care_team_summary(
            patient_id=assignment.patient_id,
            current_user=current_user,
            db=db,
        )

    if care_role == "primary":
        existing_primary = db.scalar(
            select(ClinicianAssignment).where(
                ClinicianAssignment.patient_id
                == assignment.patient_id,
                ClinicianAssignment.care_role == "primary",
                ClinicianAssignment.status == "active",
                ClinicianAssignment.id != assignment.id,
            )
        )

        if existing_primary is not None:
            raise HTTPException(
                status_code=409,
                detail="Patient already has an active primary clinician",
            )

    assignment.care_role = care_role
    assignment.updated_at = datetime.now(timezone.utc)

    db.commit()

    return get_patient_care_team_summary(
        patient_id=assignment.patient_id,
        current_user=current_user,
        db=db,
    )


@router.post(
    "/patients/{patient_id}/replace-primary",
    response_model=PatientCareTeamSummary,
)
def replace_primary_clinician(
    patient_id: int,
    replacement: PrimaryClinicianReplacement,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    patient = db.get(Patient, patient_id)

    if patient is None:
        raise HTTPException(
            status_code=404,
            detail="Patient not found",
        )

    if str(patient.status).lower() != "active":
        raise HTTPException(
            status_code=400,
            detail="Clinician cannot be assigned to an inactive patient",
        )

    clinician = db.get(
        User,
        replacement.clinician_id,
    )

    validate_clinician(clinician)

    existing_assignment = db.scalar(
        select(ClinicianAssignment).where(
            ClinicianAssignment.patient_id == patient_id,
            ClinicianAssignment.clinician_id
            == replacement.clinician_id,
            ClinicianAssignment.status == "active",
        )
    )

    now = datetime.now(timezone.utc)

    if existing_assignment is not None:
        if existing_assignment.care_role == "primary":
            return get_patient_care_team_summary(
                patient_id=patient_id,
                current_user=current_user,
                db=db,
            )

        existing_assignment.care_role = "primary"
        existing_assignment.updated_at = now

        existing_primary = db.scalars(
            select(ClinicianAssignment).where(
                ClinicianAssignment.patient_id == patient_id,
                ClinicianAssignment.care_role == "primary",
                ClinicianAssignment.status == "active",
                ClinicianAssignment.id != existing_assignment.id,
            )
        ).all()

        for assignment in existing_primary:
            assignment.care_role = "secondary"
            assignment.updated_at = now

    else:
        existing_primary = db.scalars(
            select(ClinicianAssignment).where(
                ClinicianAssignment.patient_id == patient_id,
                ClinicianAssignment.care_role == "primary",
                ClinicianAssignment.status == "active",
            )
        ).all()

        for assignment in existing_primary:
            assignment.care_role = "secondary"
            assignment.updated_at = now

        new_assignment = ClinicianAssignment(
            patient_id=patient_id,
            clinician_id=replacement.clinician_id,
            assigned_by=current_user.id,
            care_role="primary",
            status="active",
            assigned_at=now,
            ended_at=None,
            created_at=now,
            updated_at=now,
        )

        db.add(new_assignment)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="The primary clinician replacement conflicts with an existing assignment",
        )

    return get_patient_care_team_summary(
        patient_id=patient_id,
        current_user=current_user,
        db=db,
    )


@router.get(
    "/coverage",
    response_model=CareCoverageOverview,
)
def get_care_coverage_overview(
    include_partially_covered: bool = True,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    patients = db.scalars(
        select(Patient)
        .where(Patient.status == "active")
        .order_by(Patient.id.asc())
    ).all()

    total_active_patients = len(patients)

    if total_active_patients == 0:
        return CareCoverageOverview(
            total_active_patients=0,
            covered_patients=0,
            partially_covered_patients=0,
            uncovered_patients=0,
            coverage_rate=0.0,
            gaps=[],
        )

    patient_ids = [patient.id for patient in patients]

    assignments = db.scalars(
        select(ClinicianAssignment).where(
            ClinicianAssignment.patient_id.in_(patient_ids),
            ClinicianAssignment.status == "active",
        )
    ).all()

    assignments_by_patient: dict[
        int,
        list[ClinicianAssignment],
    ] = {}

    for assignment in assignments:
        assignments_by_patient.setdefault(
            assignment.patient_id,
            [],
        ).append(assignment)

    covered_patients = 0
    partially_covered_patients = 0
    uncovered_patients = 0

    gaps: list[CareCoverageGap] = []

    for patient in patients:
        patient_assignments = assignments_by_patient.get(
            patient.id,
            [],
        )

        has_primary = any(
            assignment.care_role == "primary"
            for assignment in patient_assignments
        )

        active_count = len(patient_assignments)

        if has_primary:
            covered_patients += 1
            continue

        if active_count > 0:
            partially_covered_patients += 1

            if include_partially_covered:
                gaps.append(
                    CareCoverageGap(
                        patient_id=patient.id,
                        patient_number=patient.patient_number,
                        patient_name=build_patient_name(patient),
                        patient_status=patient.status,
                        active_clinician_count=active_count,
                        has_primary_clinician=False,
                        gap_type="missing_primary_clinician",
                    )
                )

        else:
            uncovered_patients += 1

            gaps.append(
                CareCoverageGap(
                    patient_id=patient.id,
                    patient_number=patient.patient_number,
                    patient_name=build_patient_name(patient),
                    patient_status=patient.status,
                    active_clinician_count=0,
                    has_primary_clinician=False,
                    gap_type="no_active_clinician",
                )
            )

    coverage_rate = round(
        (
            covered_patients
            / total_active_patients
        )
        * 100,
        2,
    )

    return CareCoverageOverview(
        total_active_patients=total_active_patients,
        covered_patients=covered_patients,
        partially_covered_patients=partially_covered_patients,
        uncovered_patients=uncovered_patients,
        coverage_rate=coverage_rate,
        gaps=gaps,
    )


@router.get(
    "/clinicians/workload",
    response_model=list[ClinicianWorkloadSummary],
)
def get_clinician_workload(
    active_only: bool = True,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    clinicians = db.scalars(
        select(User)
        .where(User.status == "active")
        .order_by(User.full_name.asc())
    ).all()

    clinician_ids = [
        clinician.id
        for clinician in clinicians
    ]

    if not clinician_ids:
        return []

    statement = select(ClinicianAssignment).where(
        ClinicianAssignment.clinician_id.in_(
            clinician_ids
        )
    )

    if active_only:
        statement = statement.where(
            ClinicianAssignment.status == "active"
        )

    assignments = db.scalars(statement).all()

    assignments_by_clinician: dict[
        int,
        list[ClinicianAssignment],
    ] = {}

    for assignment in assignments:
        assignments_by_clinician.setdefault(
            assignment.clinician_id,
            [],
        ).append(assignment)

    results = []

    for clinician in clinicians:
        clinician_assignments = (
            assignments_by_clinician.get(
                clinician.id,
                [],
            )
        )

        results.append(
            ClinicianWorkloadSummary(
                clinician_id=clinician.id,
                clinician_name=clinician.full_name,
                clinician_role=clinician.role,
                active_patient_count=len(
                    clinician_assignments
                ),
                primary_patient_count=sum(
                    assignment.care_role == "primary"
                    for assignment in clinician_assignments
                ),
                secondary_patient_count=sum(
                    assignment.care_role == "secondary"
                    for assignment in clinician_assignments
                ),
            )
        )

    return results


@router.get(
    "/activity",
    response_model=list[CareTeamActivity],
)
def get_care_team_activity(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    statement = (
        select(
            ClinicianAssignment,
            Patient,
            User,
        )
        .join(
            Patient,
            Patient.id == ClinicianAssignment.patient_id,
        )
        .join(
            User,
            User.id == ClinicianAssignment.clinician_id,
        )
        .order_by(
            ClinicianAssignment.updated_at.desc(),
            ClinicianAssignment.id.desc(),
        )
        .limit(limit)
    )

    results = db.execute(statement).all()

    return [
        CareTeamActivity(
            assignment_id=assignment.id,
            patient_id=patient.id,
            patient_name=build_patient_name(patient),
            clinician_id=clinician.id,
            clinician_name=clinician.full_name,
            care_role=assignment.care_role,
            status=assignment.status,
            assigned_at=assignment.assigned_at,
            ended_at=assignment.ended_at,
            updated_at=assignment.updated_at,
        )
        for assignment, patient, clinician in results
    ]