from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.assessment_sessions import AssessmentSession
from app.models.clinician_reviews import ClinicianReview
from app.models.recommendations import Recommendation
from app.models.reports import Report
from app.models.user import User
from app.security.permissions import require_roles
from app.utils.audit import create_audit_log

from app.services.report_generator import (
    generate_assessment_report,
)

router = APIRouter(
    prefix="/assessments",
    tags=["Risk Assessment"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get("/{assessment_id}/risk-assessment")
def get_risk_assessment(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("administrator", "clinician")),
):
    from app.services.risk_assessment import (
        assess_assessment_risk,
    )

    try:
        return assess_assessment_risk(
            db=db,
            assessment_id=assessment_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@router.post(
    "/{assessment_id}/risk-assessment/recommendations"
)
def save_risk_recommendations(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("administrator", "clinician")),
):
    from app.services.risk_assessment import (
        generate_and_save_recommendations,
    )

    try:
        recommendations = (
            generate_and_save_recommendations(
                db=db,
                assessment_id=assessment_id,
                user_id=current_user.id,
            )
        )

        return {
            "assessment_id": assessment_id,
            "recommendation_count": len(
                recommendations
            ),
            "recommendations": recommendations,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@router.post(
    "/{assessment_id}/risk-assessment/"
    "recommendations/{recommendation_id}/submit-review"
)
def submit_recommendation_for_review(
    assessment_id: int,
    recommendation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("administrator", "clinician")),
):
    assessment = db.get(
        AssessmentSession,
        assessment_id,
    )

    if assessment is None:
        raise HTTPException(
            status_code=404,
            detail="Assessment not found",
        )

    recommendation = db.get(
        Recommendation,
        recommendation_id,
    )

    if recommendation is None:
        raise HTTPException(
            status_code=404,
            detail="Recommendation not found",
        )

    if recommendation.assessment_id != assessment_id:
        raise HTTPException(
            status_code=400,
            detail=(
                "Recommendation does not belong "
                "to this assessment"
            ),
        )

    existing_review = db.scalar(
        select(ClinicianReview)
        .where(
            ClinicianReview.assessment_id
            == assessment_id,
            ClinicianReview.recommendation_id
            == recommendation_id,
        )
    )

    if existing_review is not None:
        return existing_review

    review = ClinicianReview(
        assessment_id=assessment_id,
        recommendation_id=recommendation_id,
        clinician_id=current_user.id,
        review_status="pending",
        clinical_comment=None,
        modification_notes=None,
    )

    db.add(review)

    recommendation.clinician_review_required = True
    recommendation.status = "pending"

    db.commit()

    db.refresh(review)

    return review


@router.put(
    "/{assessment_id}/risk-assessment/"
    "recommendations/{recommendation_id}/review"
)
def update_recommendation_review(
    assessment_id: int,
    recommendation_id: int,
    review_status: str,
    clinical_comment: str | None = None,
    modification_notes: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("administrator", "clinician")),
):
    allowed_statuses = {
        "pending",
        "approved",
        "rejected",
        "completed",
    }

    if review_status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid review status. "
                "Use pending, approved, rejected, "
                "or completed."
            ),
        )

    assessment = db.get(
        AssessmentSession,
        assessment_id,
    )

    if assessment is None:
        raise HTTPException(
            status_code=404,
            detail="Assessment not found",
        )

    recommendation = db.get(
        Recommendation,
        recommendation_id,
    )

    if recommendation is None:
        raise HTTPException(
            status_code=404,
            detail="Recommendation not found",
        )

    if recommendation.assessment_id != assessment_id:
        raise HTTPException(
            status_code=400,
            detail=(
                "Recommendation does not belong "
                "to this assessment"
            ),
        )

    review = db.scalar(
        select(ClinicianReview)
        .where(
            ClinicianReview.assessment_id
            == assessment_id,
            ClinicianReview.recommendation_id
            == recommendation_id,
        )
    )

    if review is None:
        raise HTTPException(
            status_code=404,
            detail="Clinician review not found",
        )

    review.review_status = review_status
    review.clinical_comment = clinical_comment
    review.modification_notes = modification_notes

    if review_status in {
        "approved",
        "rejected",
        "completed",
    }:
        recommendation.status = review_status
        recommendation.clinician_review_required = False
    else:
        recommendation.status = "pending"
        recommendation.clinician_review_required = True

    db.commit()

    db.refresh(review)
    db.refresh(recommendation)

    return {
        "review": review,
        "recommendation": recommendation,
    }


# ============================================================
# REPORT GENERATION
# ============================================================


@router.post(
    "/{assessment_id}/risk-assessment/report"
)
def generate_risk_assessment_report(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("administrator", "clinician")),
):
    try:
        report = generate_assessment_report(
            db=db,
            assessment_id=assessment_id,
            user_id=current_user.id,
        )

        return report

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


# ============================================================
# REPORT REVIEW
# ============================================================


@router.post(
    "/{assessment_id}/risk-assessment/"
    "reports/{report_id}/submit-review"
)
def submit_report_for_review(
    assessment_id: int,
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("administrator", "clinician")),
):
    # --------------------------------------------------------
    # Validate assessment
    # --------------------------------------------------------

    assessment = db.get(
        AssessmentSession,
        assessment_id,
    )

    if assessment is None:
        raise HTTPException(
            status_code=404,
            detail="Assessment not found",
        )

    # --------------------------------------------------------
    # Validate report
    # --------------------------------------------------------

    report = db.get(
        Report,
        report_id,
    )

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    # --------------------------------------------------------
    # Validate report belongs to assessment
    # --------------------------------------------------------

    if report.assessment_id != assessment_id:
        raise HTTPException(
            status_code=400,
            detail=(
                "Report does not belong "
                "to this assessment"
            ),
        )

    # --------------------------------------------------------
    # Check for existing review
    # --------------------------------------------------------

    existing_review = db.scalar(
        select(ClinicianReview)
        .where(
            ClinicianReview.assessment_id
            == assessment_id,
            ClinicianReview.report_id
            == report_id,
        )
    )

    if existing_review is not None:
        return existing_review

    # --------------------------------------------------------
    # Create clinician review
    # --------------------------------------------------------

    review = ClinicianReview(
        assessment_id=assessment_id,
        report_id=report_id,
        clinician_id=current_user.id,
        review_status="pending",
        clinical_comment=None,
        modification_notes=None,
    )

    db.add(review)

    # --------------------------------------------------------
    # Update report status
    # --------------------------------------------------------

    report.status = "pending_review"
    report.updated_at = (
        __import__("datetime")
        .datetime.now(
            __import__("datetime").timezone.utc
        )
    )

    db.commit()

    db.refresh(review)
    db.refresh(report)

    return {
        "review": review,
        "report": report,
    }


@router.put(
    "/{assessment_id}/risk-assessment/"
    "reports/{report_id}/review"
)
def update_report_review(
    assessment_id: int,
    report_id: int,
    review_status: str,
    clinical_comment: str | None = None,
    modification_notes: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("administrator", "clinician")),
):
    allowed_statuses = {
        "pending",
        "reviewed",
        "approved",
        "rejected",
        "completed",
    }

    # --------------------------------------------------------
    # Validate review status
    # --------------------------------------------------------

    if review_status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid review status. "
                "Use pending, reviewed, approved, rejected, "
                "or completed."
            ),
        )

    # --------------------------------------------------------
    # Validate assessment
    # --------------------------------------------------------

    assessment = db.get(
        AssessmentSession,
        assessment_id,
    )

    if assessment is None:
        raise HTTPException(
            status_code=404,
            detail="Assessment not found",
        )

    # --------------------------------------------------------
    # Validate report
    # --------------------------------------------------------

    report = db.get(
        Report,
        report_id,
    )

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    # --------------------------------------------------------
    # Validate ownership
    # --------------------------------------------------------

    if report.assessment_id != assessment_id:
        raise HTTPException(
            status_code=400,
            detail=(
                "Report does not belong "
                "to this assessment"
            ),
        )

    # --------------------------------------------------------
    # Find clinician review
    # --------------------------------------------------------

    review = db.scalar(
        select(ClinicianReview)
        .where(
            ClinicianReview.assessment_id
            == assessment_id,
            ClinicianReview.report_id
            == report_id,
        )
    )

    if review is None:
        raise HTTPException(
            status_code=404,
            detail="Clinician review not found",
        )

    # --------------------------------------------------------
    # Update review
    # --------------------------------------------------------

    review.review_status = review_status
    review.clinical_comment = clinical_comment
    review.modification_notes = modification_notes

    now = __import__("datetime").datetime.now(
        __import__("datetime").timezone.utc
    )
    if review_status in {"reviewed", "approved", "rejected", "completed"}:
        review.reviewed_at = now
    review.updated_at = now

    # --------------------------------------------------------
    # Update report status
    # --------------------------------------------------------

    if review_status == "reviewed":
        report.status = "reviewed"

    elif review_status == "approved":
        report.status = "approved"

    elif review_status == "rejected":
        report.status = "rejected"

    elif review_status == "completed":
        report.status = "completed"

    else:
        report.status = "pending_review"

    report.updated_at = (
        __import__("datetime")
        .datetime.now(
            __import__("datetime").timezone.utc
        )
    )

    # --------------------------------------------------------
    # Audit review action
    # --------------------------------------------------------

    if review_status in {"reviewed", "approved", "rejected", "completed"}:
        create_audit_log(
            db=db,
            user_id=current_user.id,
            action="review",
            entity_type="Report",
            entity_id=report.id,
            description=f"Clinician marked clinical report {review_status}",
            log_metadata={
                "assessment_id": assessment_id,
                "review_status": review_status,
            },
        )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    db.commit()

    db.refresh(review)
    db.refresh(report)

    return {
        "review": review,
        "report": report,
    }