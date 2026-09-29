from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.assessment_sessions import AssessmentSession
from app.models.clinician_reviews import ClinicianReview
from app.models.health_concerns import HealthConcern
from app.models.recommendations import Recommendation
from app.models.reports import Report
from app.models.user import User
from app.security.permissions import require_roles
from app.services.risk_assessment import (
    assess_assessment_risk,
)

router = APIRouter(
    prefix="/assessments",
    tags=["Assessment Intelligence"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get("/{assessment_id}/intelligence")
def get_assessment_intelligence(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("administrator", "clinician")),
):
    # ---------------------------------------------------------
    # Get assessment
    # ---------------------------------------------------------

    assessment = db.get(
        AssessmentSession,
        assessment_id,
    )

    if assessment is None:
        raise HTTPException(
            status_code=404,
            detail="Assessment not found",
        )

    # ---------------------------------------------------------
    # Calculate current risk assessment
    # ---------------------------------------------------------

    risk_result = assess_assessment_risk(
        db=db,
        assessment_id=assessment_id,
    )

    # ---------------------------------------------------------
    # Get health concerns
    # ---------------------------------------------------------

    health_concerns = list(
        db.scalars(
            select(HealthConcern)
            .where(
                HealthConcern.assessment_id
                == assessment_id
            )
            .order_by(
                HealthConcern.created_at.desc()
            )
        ).all()
    )

    # ---------------------------------------------------------
    # Get recommendations
    # ---------------------------------------------------------

    recommendations = list(
        db.scalars(
            select(Recommendation)
            .where(
                Recommendation.assessment_id
                == assessment_id
            )
            .order_by(
                Recommendation.created_at.desc()
            )
        ).all()
    )

    # ---------------------------------------------------------
    # Get reports
    # ---------------------------------------------------------

    reports = list(
        db.scalars(
            select(Report)
            .where(
                Report.assessment_id
                == assessment_id
            )
            .order_by(
                Report.generated_at.desc()
            )
        ).all()
    )

    # ---------------------------------------------------------
    # Get clinician reviews
    # ---------------------------------------------------------

    reviews = list(
        db.scalars(
            select(ClinicianReview)
            .where(
                ClinicianReview.assessment_id
                == assessment_id
            )
            .order_by(
                ClinicianReview.created_at.desc()
            )
        ).all()
    )

    # ---------------------------------------------------------
    # Build response
    # ---------------------------------------------------------

    return {
        "assessment": {
            "id": assessment.id,
            "patient_id": assessment.patient_id,
            "assessment_type": (
                assessment.assessment_type
            ),
            "status": assessment.status,
            "started_at": assessment.started_at,
            "completed_at": assessment.completed_at,
            "assessed_by": assessment.assessed_by,
            "summary": assessment.summary,
            "notes": assessment.notes,
            "created_at": assessment.created_at,
            "updated_at": assessment.updated_at,
        },

        "risk_assessment": {
            "risk_factors": risk_result.get(
                "risk_factors",
                {},
            ),
            "risk_score": risk_result.get(
                "risk_score",
                {},
            ),
            "assessment_summary": (
                risk_result.get(
                    "assessment_summary",
                    {},
                )
            ),
        },

        "health_concerns": health_concerns,

        "recommendations": recommendations,

        "reports": reports,

        "clinician_reviews": reviews,

        "counts": {
            "health_concerns": len(
                health_concerns
            ),
            "recommendations": len(
                recommendations
            ),
            "reports": len(reports),
            "clinician_reviews": len(reviews),
        },
    }