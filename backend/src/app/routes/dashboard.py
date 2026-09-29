from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.assessment_sessions import AssessmentSession
from app.models.clinician_reviews import ClinicianReview
from app.models.health_concerns import HealthConcern
from app.models.patient import Patient
from app.models.recommendations import Recommendation
from app.models.reports import Report
from app.models.user import User
from app.security.permissions import require_roles


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/summary")
def dashboard_summary(
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    return {
        "patients": {
            "total": db.scalar(
                select(func.count(Patient.id))
            ),
            "active": db.scalar(
                select(func.count(Patient.id)).where(
                    Patient.status == "active"
                )
            ),
            "inactive": db.scalar(
                select(func.count(Patient.id)).where(
                    Patient.status == "inactive"
                )
            ),
        },
        "assessments": {
            "total": db.scalar(
                select(func.count(AssessmentSession.id))
            ),
            "in_progress": db.scalar(
                select(func.count(AssessmentSession.id)).where(
                    AssessmentSession.status == "in_progress"
                )
            ),
            "completed": db.scalar(
                select(func.count(AssessmentSession.id)).where(
                    AssessmentSession.status == "completed"
                )
            ),
        },
        "health_concerns": db.scalar(
            select(func.count(HealthConcern.id))
        ),
        "recommendations": db.scalar(
            select(func.count(Recommendation.id))
        ),
        "reports": db.scalar(
            select(func.count(Report.id))
        ),
        "clinician_reviews": {
            "total": db.scalar(
                select(func.count(ClinicianReview.id))
            ),
            "pending": db.scalar(
                select(func.count(ClinicianReview.id)).where(
                    ClinicianReview.review_status == "pending"
                )
            ),
            "approved": db.scalar(
                select(func.count(ClinicianReview.id)).where(
                    ClinicianReview.review_status == "approved"
                )
            ),
        },
    }