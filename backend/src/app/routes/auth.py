from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.patient_user_links import PatientUserLink
from app.models.user import User
from app.models.patient import Patient
from app.schemas.auth import LoginRequest, LoginResponse, PatientRegistrationRequest, UserResponse
from app.security.dependencies import get_current_user
from app.security.password import hash_password, verify_password
from app.security.permissions import permissions_for_role
from app.security.roles import normalize_role
from app.security.token import create_access_token
from app.utils.audit import create_audit_log


router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def user_patient_id(db: Session, user_id: int) -> int | None:
    link = db.scalar(
        select(PatientUserLink).where(PatientUserLink.user_id == user_id)
    )
    return link.patient_id if link else None


def serialize_user(user: User, db: Session) -> UserResponse:
    role = normalize_role(user.role)
    return UserResponse(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        role=role,
        status=user.status,
        permissions=permissions_for_role(role),
        patient_id=user_patient_id(db, user.id),
    )


@router.post("/login", response_model=LoginResponse)
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db),
):
    user = db.scalar(select(User).where(User.username == credentials.username))

    if user is None or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active",
        )

    actual_role = normalize_role(user.role)
    if credentials.login_role is not None:
        requested_role = normalize_role(credentials.login_role)
        if requested_role != actual_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This account is not registered as a {requested_role} account",
            )

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    access_token = create_access_token(
        user_id=user.id,
        username=user.username,
        role=actual_role,
    )

    return LoginResponse(
        message="Login successful",
        access_token=access_token,
        token_type="bearer",
        user=serialize_user(user, db),
    )


@router.post("/register/patient", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
def register_patient(
    payload: PatientRegistrationRequest,
    db: Session = Depends(get_db),
):
    username = payload.username.strip()
    first_name = payload.first_name.strip()
    last_name = payload.last_name.strip()

    if not username or not first_name or not last_name:
        raise HTTPException(status_code=400, detail="Username, first name, and last name are required")

    existing = db.scalar(select(User).where(User.username == username))
    if existing is not None:
        raise HTTPException(status_code=409, detail="Username already exists")

    now = datetime.now(timezone.utc)
    user = User(
        username=username,
        password_hash=hash_password(payload.password),
        full_name=f"{first_name} {last_name}",
        role="patient",
        status="active",
        created_at=now,
        updated_at=now,
        last_login_at=None,
    )
    db.add(user)
    db.flush()

    patient = Patient(
        patient_number="",
        first_name=first_name,
        last_name=last_name,
        date_of_birth=payload.date_of_birth,
        sex=payload.sex,
        marital_status=payload.marital_status,
        occupation=payload.occupation,
        preferred_language=payload.preferred_language,
        residence=payload.residence,
        district=payload.district,
        country=payload.country,
        status="active",
        created_at=now,
        updated_at=now,
        created_by=user.id,
    )
    db.add(patient)
    db.flush()
    patient.patient_number = f"CS-{patient.id:06d}"

    db.add(PatientUserLink(user_id=user.id, patient_id=patient.id, created_at=now))

    create_audit_log(
        db=db,
        user_id=user.id,
        action="register",
        entity_type="Patient",
        entity_id=patient.id,
        description="Patient self-registration completed",
    )

    user.last_login_at = now
    db.commit()
    db.refresh(user)

    actual_role = "patient"
    access_token = create_access_token(
        user_id=user.id,
        username=user.username,
        role=actual_role,
    )

    return LoginResponse(
        message="Patient registration successful",
        access_token=access_token,
        token_type="bearer",
        user=serialize_user(user, db),
    )


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return serialize_user(current_user, db)
