from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.assessment_sessions import AssessmentSession
from app.models.health_concerns import HealthConcern
from app.models.user import User
from app.schemas.health_concern import (
    HealthConcernCreate,
    HealthConcernResponse,
    HealthConcernUpdate,
)
from app.security.permissions import require_roles


router = APIRouter(
    prefix="/assessments",
    tags=["Health Concerns"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/{assessment_id}/health-concerns",
    response_model=HealthConcernResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_health_concern(
    assessment_id: int,
    concern_data: HealthConcernCreate,
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

    concern = HealthConcern(
        assessment_id=assessment_id,
        **concern_data.model_dump(),
        created_at=datetime.now(timezone.utc),
    )

    db.add(concern)
    db.commit()
    db.refresh(concern)

    return concern


@router.get(
    "/{assessment_id}/health-concerns",
    response_model=list[HealthConcernResponse],
)
def list_health_concerns(
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

    statement = (
        select(HealthConcern)
        .where(
            HealthConcern.assessment_id == assessment_id
        )
        .order_by(HealthConcern.id.desc())
    )

    return db.scalars(statement).all()


@router.put(
    "/health-concerns/{concern_id}",
    response_model=HealthConcernResponse,
)
def update_health_concern(
    concern_id: int,
    concern_data: HealthConcernUpdate,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    concern = db.get(
        HealthConcern,
        concern_id,
    )

    if concern is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Health concern not found",
        )

    update_data = concern_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(concern, field, value)

    db.commit()
    db.refresh(concern)

    return concern