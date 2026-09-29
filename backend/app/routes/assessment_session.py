from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import SessionLocal
from app.models.assessment_sessions import AssessmentSession
from app.models.patient import Patient
from app.models.user import User
from app.schemas.assessment_detail import AssessmentDetailResponse
from app.schemas.assessment_session import (
    AssessmentSessionCreate,
    AssessmentSessionResponse,
    AssessmentSessionUpdate,
)
from app.security.permissions import require_roles
from app.services.notification_automation import (
    trigger_assessment_completion_notifications,
)


router = APIRouter(
    prefix="/patient",
    tags=["Assessment Sessions"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/{patient_id}/assessments",
    response_model=AssessmentSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_assessment_session(
    patient_id: int,
    assessment_data: AssessmentSessionCreate,
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

    assessment = AssessmentSession(
        patient_id=patient_id,
        assessment_type=assessment_data.assessment_type,
        status=assessment_data.status,
        started_at=now,
        completed_at=None,
        assessed_by=current_user.id,
        summary=assessment_data.summary,
        notes=assessment_data.notes,
        created_at=now,
        updated_at=now,
    )

    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    return assessment


@router.get(
    "/{patient_id}/assessments",
    response_model=list[AssessmentSessionResponse],
)
def list_assessment_sessions(
    patient_id: int,
    assessment_type: str | None = Query(default=None),
    assessment_status: str | None = Query(
        default=None,
        alias="status",
    ),
    assessed_by: int | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    patient = db.get(Patient, patient_id)

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    statement = select(AssessmentSession).where(
        AssessmentSession.patient_id == patient_id
    )

    if assessment_type:
        statement = statement.where(
            AssessmentSession.assessment_type
            == assessment_type
        )

    if assessment_status:
        statement = statement.where(
            AssessmentSession.status
            == assessment_status
        )

    if assessed_by is not None:
        statement = statement.where(
            AssessmentSession.assessed_by
            == assessed_by
        )

    statement = (
        statement
        .order_by(AssessmentSession.id.desc())
        .limit(limit)
    )

    return list(db.scalars(statement).all())


@router.get(
    "/assessment-sessions/{assessment_id}",
    response_model=AssessmentSessionResponse,
)
def get_assessment_session(
    assessment_id: int,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    assessment = db.get(
        AssessmentSession,
        assessment_id,
    )

    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment session not found",
        )

    return assessment


@router.get(
    "/assessment-sessions/{assessment_id}/detail",
    response_model=AssessmentDetailResponse,
)
def get_assessment_detail(
    assessment_id: int,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    statement = (
        select(AssessmentSession)
        .options(
            selectinload(AssessmentSession.answers),
            selectinload(AssessmentSession.health_concerns),
            selectinload(AssessmentSession.recommendations),
            selectinload(AssessmentSession.reports),
            selectinload(AssessmentSession.clinician_reviews),
            selectinload(AssessmentSession.vital_signs),
        )
        .where(AssessmentSession.id == assessment_id)
    )

    assessment = db.scalar(statement)

    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment session not found",
        )

    return {
        "assessment": jsonable_encoder(assessment),
        "answers": jsonable_encoder(assessment.answers),
        "health_concerns": jsonable_encoder(
            assessment.health_concerns
        ),
        "recommendations": jsonable_encoder(
            assessment.recommendations
        ),
        "reports": jsonable_encoder(
            assessment.reports
        ),
        "clinician_reviews": jsonable_encoder(
            assessment.clinician_reviews
        ),
        "vital_signs": jsonable_encoder(
            assessment.vital_signs
        ),
    }


@router.put(
    "/assessment-sessions/{assessment_id}",
    response_model=AssessmentSessionResponse,
)
def update_assessment_session(
    assessment_id: int,
    assessment_data: AssessmentSessionUpdate,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    assessment = db.get(
        AssessmentSession,
        assessment_id,
    )

    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment session not found",
        )

    update_data = assessment_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(assessment, field, value)

    assessment.assessed_by = current_user.id
    assessment.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(assessment)

    return assessment


@router.post(
    "/assessment-sessions/{assessment_id}/complete",
    response_model=AssessmentSessionResponse,
)
def complete_assessment_session(
    assessment_id: int,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    assessment = db.get(
        AssessmentSession,
        assessment_id,
    )

    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment session not found",
        )

    now = datetime.now(timezone.utc)

    assessment.status = "completed"
    assessment.completed_at = now
    assessment.assessed_by = current_user.id
    assessment.updated_at = now

    db.commit()
    db.refresh(assessment)

    # ---------------------------------------------------------
    # Phase 13F:
    # Automatically synchronize notifications after
    # assessment completion.
    # ---------------------------------------------------------

    trigger_assessment_completion_notifications(
        db=db,
        patient_id=assessment.patient_id,
    )

    return assessment