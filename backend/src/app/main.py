from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine

from app.models.clinician_assignments import ClinicianAssignment
from app.models.patient_user_links import PatientUserLink

from app.routes.auth import router as auth_router
from app.routes.patient import router as patient_router
from app.routes.patient_portal import router as patient_portal_router
from app.routes.patient_contact import router as patient_contact_router
from app.routes.medical_history import router as medical_history_router
from app.routes.allergy import router as allergy_router
from app.routes.medication import router as medication_router
from app.routes.lifestyle import router as lifestyle_router
from app.routes.vital_sign import router as vital_sign_router
from app.routes.assessment_question import router as assessment_question_router
from app.routes.assessment_session import router as assessment_session_router
from app.routes.assessment_answers import router as assessment_answer_router
from app.routes.health_concerns import router as health_concern_router
from app.routes.recommendation import router as recommendation_router
from app.routes.report import router as report_router
from app.routes.clinician_reviews import router as clinician_review_router
from app.routes.audit_log import router as audit_log_router
from app.routes.user import router as user_router
from app.routes.dashboard import router as dashboard_router

from app.routes.risk_assessment import router as risk_assessment_router

from app.routes.assessment_intelligence import (
    router as assessment_intelligence_router,
)

from app.routes.patient_timeline import (
    router as patient_timeline_router,
)

from app.routes.risk_trends import (
    router as risk_trends_router,
)

from app.routes.clinical_summary import (
    router as clinical_summary_router,
)

from app.routes.care_gaps import (
    router as care_gaps_router,
)

from app.routes.patient_follow_up import (
    router as patient_follow_up_router,
)

from app.routes.care_coordination import (
    router as care_coordination_router,
)

from app.routes.patient_dashboard_intelligence import (
    router as patient_dashboard_intelligence_router,
)

from app.routes.patient_search import (
    router as patient_search_router,
)

from app.routes.patient_activity_feed import (
    router as patient_activity_feed_router,
)

from app.routes.patient_dashboard import (
    router as patient_dashboard_router,
)

from app.routes.patient_notifications import (
    router as patient_notifications_router,
)

from app.routes.notifications import (
    router as notifications_router,
)

from app.routes.notification_summary import (
    router as notification_summary_router,
)

from app.routes.notification_dashboard import (
    router as notification_dashboard_router,
)

from app.routes.notification_analytics import (
    router as notification_analytics_router,
)

from app.routes.notification_trends import (
    router as notification_trends_router,
)

from app.routes.notification_performance import (
    router as notification_performance_router,
)

from app.routes.notification_intelligence import (
    router as notification_intelligence_router,
)

from app.routes.notification_filter import (
    router as notification_filter_router,
)

from app.routes.notification_search import (
    router as notification_search_router,
)

from app.routes.notification_reporting import (
    router as notification_reporting_router,
)

from app.routes.notification_intelligence_audit import (
    router as notification_intelligence_audit_router,
)

from app.routes.clinician_assignments import (
    router as clinician_assignment_router,
)

from app.routes.care_team_intelligence import (
    router as care_team_intelligence_router,
)

from app.routes.ai import router as ai_router


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="CareSphere",
    description="Professional healthcare patient intelligence system",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
allow_origin_regex=r"https?://(localhost|127\.0\.0\.1):\d+$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
def root():
    return {
        "message": "CareSphere API is running",
        "version": "0.1.0",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "CareSphere API",
    }


app.include_router(auth_router)

app.include_router(patient_router)
app.include_router(patient_portal_router)

app.include_router(patient_contact_router)

app.include_router(medical_history_router)

app.include_router(allergy_router)

app.include_router(medication_router)

app.include_router(lifestyle_router)

app.include_router(vital_sign_router)

app.include_router(assessment_question_router)

app.include_router(assessment_session_router)

app.include_router(assessment_answer_router)

app.include_router(health_concern_router)

app.include_router(recommendation_router)

app.include_router(report_router)

app.include_router(clinician_review_router)

app.include_router(audit_log_router)

app.include_router(user_router)

app.include_router(dashboard_router)

app.include_router(risk_assessment_router)

app.include_router(assessment_intelligence_router)

app.include_router(patient_timeline_router)

app.include_router(risk_trends_router)

app.include_router(clinical_summary_router)

app.include_router(care_gaps_router)

app.include_router(patient_follow_up_router)

app.include_router(care_coordination_router)

app.include_router(patient_dashboard_intelligence_router)

app.include_router(patient_search_router)

app.include_router(patient_activity_feed_router)

app.include_router(patient_dashboard_router)

app.include_router(patient_notifications_router)

app.include_router(notifications_router)

app.include_router(notification_summary_router)

app.include_router(notification_dashboard_router)

app.include_router(notification_analytics_router)

app.include_router(notification_trends_router)

app.include_router(notification_performance_router)

app.include_router(notification_intelligence_router)

app.include_router(notification_filter_router)

app.include_router(notification_search_router)

app.include_router(notification_reporting_router)

app.include_router(notification_intelligence_audit_router)

app.include_router(clinician_assignment_router)

app.include_router(care_team_intelligence_router)

app.include_router(ai_router)