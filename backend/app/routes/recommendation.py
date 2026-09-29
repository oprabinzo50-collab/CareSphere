from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import SessionLocal
from app.models.assessment_sessions import AssessmentSession
from app.models.health_concerns import HealthConcern
from app.models.recommendations import Recommendation
from app.models.user import User
from app.schemas.recommendation import (
    RecommendationCreate,
    RecommendationResponse,
    RecommendationUpdate,
)
from app.security.permissions import require_roles
from app.services.recommendation_notification_automation import (
    trigger_recommendation_notifications,
)


router = APIRouter(
    prefix="/assessments",
    tags=["Recommendations"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/{assessment_id}/recommendations",
    response_model=RecommendationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_recommendation(
    assessment_id: int,
    recommendation_data: RecommendationCreate,
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

    if recommendation_data.health_concern_id is not None:
        concern = db.get(
            HealthConcern,
            recommendation_data.health_concern_id,
        )

        if concern is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Health concern not found",
            )

        if concern.assessment_id != assessment_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Health concern does not belong to this assessment",
            )

    now = datetime.now(timezone.utc)

    recommendation = Recommendation(
        assessment_id=assessment_id,
        **recommendation_data.model_dump(),
        created_at=now,
        updated_at=now,
        created_by=current_user.id,
    )

    db.add(recommendation)
    db.commit()
    db.refresh(recommendation)

    trigger_recommendation_notifications(
        db=db,
        recommendation=recommendation,
    )

    return recommendation


@router.get(
    "/{assessment_id}/recommendations",
    response_model=list[RecommendationResponse],
)
def list_recommendations(
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
        select(Recommendation)
        .where(
            Recommendation.assessment_id == assessment_id
        )
        .order_by(Recommendation.id.desc())
    )

    return db.scalars(statement).all()


@router.put(
    "/recommendations/{recommendation_id}",
    response_model=RecommendationResponse,
)
def update_recommendation(
    recommendation_id: int,
    recommendation_data: RecommendationUpdate,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    statement = (
        select(Recommendation)
        .options(
            selectinload(
                Recommendation.assessment
            )
        )
        .where(
            Recommendation.id == recommendation_id
        )
    )

    recommendation = db.scalar(statement)

    if recommendation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found",
        )

    previous_status = str(
        getattr(
            recommendation,
            "status",
            "",
        )
    ).lower()

    update_data = recommendation_data.model_dump(
        exclude_unset=True
    )

    if "health_concern_id" in update_data:
        concern_id = update_data["health_concern_id"]

        if concern_id is not None:
            concern = db.get(
                HealthConcern,
                concern_id,
            )

            if concern is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Health concern not found",
                )

            if concern.assessment_id != recommendation.assessment_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Health concern does not belong to this assessment",
                )

    for field, value in update_data.items():
        setattr(
            recommendation,
            field,
            value,
        )

    recommendation.updated_at = datetime.now(
        timezone.utc
    )

    db.commit()
    db.refresh(recommendation)

    current_status = str(
        getattr(
            recommendation,
            "status",
            "",
        )
    ).lower()

    entered_review_required_state = (
        current_status
        in {
            "pending",
            "pending_review",
            "awaiting_review",
        }
        and previous_status
        not in {
            "pending",
            "pending_review",
            "awaiting_review",
        }
    )

    if entered_review_required_state:
        trigger_recommendation_notifications(
            db=db,
            recommendation=recommendation,
        )

    return recommendation