from datetime import datetime, timezone
from pathlib import Path
import os

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import FileResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import SessionLocal
from app.models.patient import Patient
from app.models.user import User
from app.models.patient_user_links import PatientUserLink
from app.schemas.patient import (
    PatientCreate,
    PatientResponse,
    PatientUpdate,
)
from app.schemas.patient_profile import PatientProfileResponse
from app.security.dependencies import get_current_user
from app.security.roles import normalize_role
from app.security.permissions import require_roles
from app.security.patient_access import ensure_patient_access
from app.utils.audit import create_audit_log


router = APIRouter(
    prefix="/patient",
    tags=["Patient"],
)

PROFILE_IMAGE_DIR = Path(__file__).resolve().parents[2] / "uploads" / "patient_profiles"
PROFILE_IMAGE_MAX_BYTES = 5 * 1024 * 1024
PROFILE_IMAGE_TYPES = {
    "image/jpeg": ("jpg", b"\xff\xd8\xff"),
    "image/png": ("png", b"\x89PNG\r\n\x1a\n"),
    "image/webp": ("webp", b"RIFF"),
}


def _profile_image_path(patient_id: int, extension: str) -> Path:
    return PROFILE_IMAGE_DIR / f"{patient_id}.{extension}"


def _validate_profile_image(content_type: str, data: bytes) -> str:
    normalized = (content_type or "").split(";", 1)[0].strip().lower()
    spec = PROFILE_IMAGE_TYPES.get(normalized)
    if spec is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Profile picture must be JPEG, PNG, or WebP.",
        )

    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded profile picture is empty.",
        )

    if len(data) > PROFILE_IMAGE_MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Profile picture must be 5 MB or smaller.",
        )

    extension, magic = spec
    if normalized == "image/webp":
        if len(data) < 12 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded file is not a valid WebP image.",
            )
    elif not data.startswith(magic):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file does not match its image type.",
        )

    return extension


def _delete_profile_image_files(patient_id: int) -> None:
    PROFILE_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    for extension in ("jpg", "png", "webp"):
        path = _profile_image_path(patient_id, extension)
        if path.exists():
            try:
                path.unlink()
            except OSError:
                pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_patient(
    patient_data: PatientCreate,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    last_patient = db.scalar(
        select(Patient)
        .order_by(Patient.id.desc())
    )

    next_number = (
        last_patient.id + 1
        if last_patient is not None
        else 1
    )

    patient_number = f"CS-{next_number:06d}"

    now = datetime.now(timezone.utc)

    patient = Patient(
        patient_number=patient_number,
        **patient_data.model_dump(),
        status="active",
        created_at=now,
        updated_at=now,
        created_by=current_user.id,
    )

    db.add(patient)
    db.flush()

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="create",
        entity_type="Patient",
        entity_id=patient.id,
        description="Patient created",
    )

    db.commit()
    db.refresh(patient)

    return patient

@router.put("/me/profile-picture")
async def upload_my_profile_picture(
    request: Request,
    current_user: User = Depends(require_roles("patient")),
    db: Session = Depends(get_db),
):
    link = db.scalar(
        select(PatientUserLink).where(PatientUserLink.user_id == current_user.id)
    )
    if link is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No patient record is linked to this account",
        )
    return await _upload_profile_picture(link.patient_id, request, current_user, db)


@router.put("/{patient_id}/profile-picture")
async def upload_patient_profile_picture(
    patient_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_patient_access(patient_id, current_user, db)
    return await _upload_profile_picture(patient_id, request, current_user, db)


async def _upload_profile_picture(
    patient_id: int,
    request: Request,
    current_user: User,
    db: Session,
):
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    data = await request.body()
    extension = _validate_profile_image(request.headers.get("content-type", ""), data)

    PROFILE_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    target = _profile_image_path(patient_id, extension)
    temp = PROFILE_IMAGE_DIR / f".{patient_id}.{extension}.uploading"
    temp.write_bytes(data)

    _delete_profile_image_files(patient_id)
    os.replace(temp, target)

    patient.updated_at = datetime.now(timezone.utc)
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="update",
        entity_type="Patient",
        entity_id=patient.id,
        description="Patient profile picture uploaded",
    )
    db.commit()

    return {
        "message": "Profile picture uploaded successfully",
        "patient_id": patient.id,
        "profile_picture_url": f"/patient/{patient.id}/profile-picture",
    }


@router.get("/me/profile-picture")
def get_my_profile_picture(
    current_user: User = Depends(require_roles("patient")),
    db: Session = Depends(get_db),
):
    link = db.scalar(
        select(PatientUserLink).where(PatientUserLink.user_id == current_user.id)
    )
    if link is None:
        raise HTTPException(status_code=404, detail="Patient record not linked")
    return _get_profile_picture(link.patient_id, current_user, db)


@router.get("/{patient_id}/profile-picture")
def get_patient_profile_picture(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_patient_access(patient_id, current_user, db)
    return _get_profile_picture(patient_id, current_user, db)


def _get_profile_picture(patient_id: int, current_user: User, db: Session):
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    candidates = [
        ("jpg", "image/jpeg"),
        ("png", "image/png"),
        ("webp", "image/webp"),
    ]
    for extension, media_type in candidates:
        path = _profile_image_path(patient_id, extension)
        if path.exists():
            return FileResponse(
                path,
                media_type=media_type,
                headers={"Cache-Control": "no-store"},
            )

    raise HTTPException(status_code=404, detail="Profile picture not found")


@router.delete("/me/profile-picture")
def delete_my_profile_picture(
    current_user: User = Depends(require_roles("patient")),
    db: Session = Depends(get_db),
):
    link = db.scalar(
        select(PatientUserLink).where(PatientUserLink.user_id == current_user.id)
    )
    if link is None:
        raise HTTPException(status_code=404, detail="Patient record not linked")
    return _delete_profile_picture(link.patient_id, current_user, db)


@router.delete("/{patient_id}/profile-picture")
def delete_patient_profile_picture(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_patient_access(patient_id, current_user, db)
    return _delete_profile_picture(patient_id, current_user, db)


def _delete_profile_picture(patient_id: int, current_user: User, db: Session):
    _delete_profile_image_files(patient_id)
    patient = db.get(Patient, patient_id)
    if patient is not None:
        patient.updated_at = datetime.now(timezone.utc)
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="update",
        entity_type="Patient",
        entity_id=patient_id,
        description="Patient profile picture removed",
    )
    db.commit()
    return {"message": "Profile picture removed successfully", "patient_id": patient_id}


@router.get(
    "/me/profile",
    response_model=PatientProfileResponse,
)
def get_my_patient_profile(
    current_user: User = Depends(require_roles("patient")),
    db: Session = Depends(get_db),
):
    link = db.scalar(
        select(PatientUserLink).where(
            PatientUserLink.user_id == current_user.id
        )
    )
    if link is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No patient record is linked to this account",
        )

    return get_patient_profile(link.patient_id, current_user, db)


@router.get(
    "/{patient_id}/profile",
    response_model=PatientProfileResponse,
)
def get_patient_profile(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_patient_access(patient_id, current_user, db)

    statement = (
        select(Patient)
        .options(
            selectinload(Patient.contacts),
            selectinload(Patient.medical_history),
            selectinload(Patient.allergies),
            selectinload(Patient.medications),
            selectinload(Patient.lifestyle),
            selectinload(Patient.vital_signs),
            selectinload(Patient.assessment_sessions),
        )
        .where(Patient.id == patient_id)
    )

    patient = db.scalar(statement)

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    return {
        "patient": jsonable_encoder(patient),
        "contacts": jsonable_encoder(patient.contacts),
        "medical_history": jsonable_encoder(
            patient.medical_history
        ),
        "allergies": jsonable_encoder(patient.allergies),
        "medications": jsonable_encoder(patient.medications),
        "lifestyle": jsonable_encoder(patient.lifestyle),
        "vital_signs": jsonable_encoder(patient.vital_signs),
        "assessments": jsonable_encoder(
            patient.assessment_sessions
        ),
    }


@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
)
def get_patient(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_patient_access(patient_id, current_user, db)

    patient = db.get(Patient, patient_id)

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    return patient


@router.get(
    "",
    response_model=list[PatientResponse],
)
def list_patients(
    search: str | None = Query(default=None),
    status_filter: str = Query(
        default="active",
        alias="status",
    ),
    district: str | None = Query(default=None),
    country: str | None = Query(default=None),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    statement = select(Patient)

    if status_filter:
        statement = statement.where(
            Patient.status == status_filter
        )

    if search:
        search_pattern = f"%{search}%"

        statement = statement.where(
            Patient.patient_number.ilike(search_pattern)
            | Patient.first_name.ilike(search_pattern)
            | Patient.last_name.ilike(search_pattern)
        )

    if district:
        statement = statement.where(
            Patient.district.ilike(district)
        )

    if country:
        statement = statement.where(
            Patient.country.ilike(country)
        )

    statement = (
        statement
        .order_by(Patient.id.desc())
        .limit(limit)
    )

    return list(db.scalars(statement).all())


@router.put(
    "/{patient_id}",
    response_model=PatientResponse,
)
def update_patient(
    patient_id: int,
    patient_data: PatientUpdate,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    patient = db.get(Patient, patient_id)

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    update_data = patient_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(patient, field, value)

    patient.updated_at = datetime.now(timezone.utc)

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="update",
        entity_type="Patient",
        entity_id=patient.id,
        description="Patient updated",
    )

    db.commit()
    db.refresh(patient)

    return patient


@router.delete(
    "/{patient_id}",
    response_model=PatientResponse,
)
def deactivate_patient(
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

    patient.status = "inactive"
    patient.updated_at = datetime.now(timezone.utc)

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="deactivate",
        entity_type="Patient",
        entity_id=patient.id,
        description="Patient deactivated",
    )

    db.commit()
    db.refresh(patient)

    return patient


@router.post(
    "/{patient_id}/reactivate",
    response_model=PatientResponse,
)
def reactivate_patient(
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

    patient.status = "active"
    patient.updated_at = datetime.now(timezone.utc)

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="reactivate",
        entity_type="Patient",
        entity_id=patient.id,
        description="Patient reactivated",
    )

    db.commit()
    db.refresh(patient)

    return patient