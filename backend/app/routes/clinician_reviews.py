from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.assessment_sessions import AssessmentSession
from app.models.clinician_reviews import ClinicianReview
from app.models.recommendations import Recommendation
from app.models.reports import Report
from app.models.user import User
from app.schemas.clinician_reviews import (
    ClinicianReviewCreate,
    ClinicianReviewResponse,
    ClinicianReviewUpdate,
)
from app.security.permissions import require_roles
from app.services.clinician_review_notification_automation import (
    trigger_clinician_review_notifications,
)


router = APIRouter(
    prefix="/assessments",
    tags=["Clinician Reviews"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/{assessment_id}/clinician-reviews",
    response_model=ClinicianReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_clinician_review(
    assessment_id: int,
    review_data: ClinicianReviewCreate,
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

    clinician = db.get(
        User,
        review_data.clinician_id,
    )

    if clinician is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinician user not found",
        )

    if review_data.recommendation_id is not None:
        recommendation = db.get(
            Recommendation,
            review_data.recommendation_id,
        )

        if recommendation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recommendation not found",
            )

        if recommendation.assessment_id != assessment_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Recommendation does not belong to this assessment",
            )

    if review_data.report_id is not None:
        report = db.get(
            Report,
            review_data.report_id,
        )

        if report is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found",
            )

        if report.assessment_id != assessment_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Report does not belong to this assessment",
            )

    now = datetime.now(timezone.utc)

    review = ClinicianReview(
        assessment_id=assessment_id,
        **review_data.model_dump(),
        reviewed_at=None,
        created_at=now,
        updated_at=now,
    )

    db.add(review)
    db.commit()
    db.refresh(review)

    trigger_clinician_review_notifications(
        db=db,
        review=review,
    )

    return review


@router.get(
    "/{assessment_id}/clinician-reviews",
    response_model=list[ClinicianReviewResponse],
)
def list_clinician_reviews(
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
        select(ClinicianReview)
        .where(
            ClinicianReview.assessment_id == assessment_id
        )
        .order_by(ClinicianReview.id.desc())
    )

    return db.scalars(statement).all()


@router.put(
    "/clinician-reviews/{review_id}",
    response_model=ClinicianReviewResponse,
)
def update_clinician_review(
    review_id: int,
    review_data: ClinicianReviewUpdate,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    review = db.get(
        ClinicianReview,
        review_id,
    )

    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinician review not found",
        )

    previous_status = str(
        getattr(
            review,
            "review_status",
            "",
        )
    ).lower()

    update_data = review_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(
            review,
            field,
            value,
        )

    if "review_status" in update_data:
        if update_data["review_status"] in {
            "approved",
            "rejected",
            "completed",
        }:
            review.reviewed_at = datetime.now(
                timezone.utc
            )

    review.updated_at = datetime.now(
        timezone.utc
    )

    db.commit()
    db.refresh(review)

    current_status = str(
        getattr(
            review,
            "review_status",
            "",
        )
    ).lower()

    entered_pending_state = (
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

    if entered_pending_state:
        trigger_clinician_review_notifications(
            db=db,
            review=review,
        )

    return review