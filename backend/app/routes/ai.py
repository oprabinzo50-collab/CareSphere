import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.clinical_context import ClinicalContext
from app.ai.config import get_ai_config
from app.ai.prompts import (
    CLINICAL_DECISION_SUPPORT_INSTRUCTIONS,
    CLINICAL_SUMMARY_INSTRUCTIONS,
    CLINICIAN_BRIEFING_INSTRUCTIONS,
    CARE_PLAN_REVIEW_INSTRUCTIONS,
    LONGITUDINAL_PATIENT_SUMMARY_INSTRUCTIONS,
    RECOMMENDATION_EXPLANATION_INSTRUCTIONS,
    RECOMMENDATION_PRIORITIZATION_INSTRUCTIONS,
    RISK_EXPLANATION_INSTRUCTIONS,
    RISK_TREND_ANALYSIS_INSTRUCTIONS,
)
from app.ai.provider import (
    AIProviderError,
    AIProviderUnavailable,
    get_ai_provider,
)

from app.models.allergies import Allergy
from app.models.assessment_answers import AssessmentAnswer
from app.models.assessment_sessions import AssessmentSession
from app.models.lifestyle import Lifestyle
from app.models.medical_history import MedicalHistory
from app.models.medications import Medication
from app.models.patient import Patient
from app.models.recommendations import Recommendation
from app.models.reports import Report
from app.models.vital_signs import VitalSign

from app.schemas.ai import (
    AIClinicalDecisionSupportRequest,
    AIClinicalDecisionSupportResponse,
    AIClinicalSummaryRequest,
    AIClinicalSummaryResponse,
    AIClinicianBriefingRequest,
    AIClinicianBriefingResponse,
    AICarePlanReviewRequest,
    AICarePlanReviewResponse,
    AILongitudinalPatientSummaryRequest,
    AILongitudinalPatientSummaryResponse,
    AIProviderHealthResponse,
    AIRecommendationExplanationRequest,
    AIRecommendationExplanationResponse,
    AIRecommendationPrioritizationRequest,
    AIRecommendationPrioritizationResponse,
    AIRiskExplanationRequest,
    AIRiskExplanationResponse,
    AIRiskTrendAnalysisRequest,
    AIRiskTrendAnalysisResponse,
    AIStatusResponse,
)

from app.security.permissions import require_roles
from app.database import SessionLocal


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)


# =========================================================
# AI STATUS
# =========================================================

@router.get(
    "/status",
    response_model=AIStatusResponse,
)
def get_ai_status(
    current_user=Depends(require_roles("administrator", "clinician")),
):
    config = get_ai_config()

    return AIStatusResponse(
        enabled=config.enabled,
        provider=config.provider,
        model_configured=bool(config.model),
        api_key_configured=bool(config.api_key),
        base_url_configured=bool(config.base_url),
    )


# =========================================================
# AI HEALTH
# =========================================================

@router.get(
    "/health",
    response_model=AIProviderHealthResponse,
)
def get_ai_health(
    current_user=Depends(require_roles("administrator", "clinician")),
):
    config = get_ai_config()

    if not config.enabled:
        return AIProviderHealthResponse(
            available=False,
            provider=config.provider,
            model=config.model or None,
            message="AI integration is disabled",
        )

    try:
        get_ai_provider()
    except AIProviderUnavailable as exc:
        return AIProviderHealthResponse(
            available=False,
            provider=config.provider,
            model=config.model or None,
            message=str(exc),
        )

    return AIProviderHealthResponse(
        available=True,
        provider=config.provider,
        model=config.model or None,
        message="AI provider is configured",
    )


# =========================================================
# SHARED PATIENT CONTEXT BUILDER
# =========================================================

def _build_patient_context(
    db: Session,
    patient: Patient,
    request: AIClinicalSummaryRequest,
) -> ClinicalContext:
    context = ClinicalContext(
        patient_id=patient.id,
    )

    # -----------------------------------------------------
    # Patient Overview
    # -----------------------------------------------------

    context.add_section(
        "Patient Overview",
        {
            "patient_number": patient.patient_number,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "date_of_birth": patient.date_of_birth,
            "sex": patient.sex,
            "marital_status": patient.marital_status,
            "occupation": patient.occupation,
            "preferred_language": patient.preferred_language,
            "district": patient.district,
            "country": patient.country,
            "status": patient.status,
        },
    )

    # -----------------------------------------------------
    # Medical History
    # -----------------------------------------------------

    medical_history = list(
        db.scalars(
            select(MedicalHistory)
            .where(
                MedicalHistory.patient_id == patient.id
            )
            .order_by(
                MedicalHistory.recorded_at.desc()
            )
        ).all()
    )

    context.add_section(
        "Medical History",
        [
            {
                "condition_name": item.condition_name,
                "description": item.description,
                "diagnosed_date": item.diagnosed_date,
                "status": item.status,
                "notes": item.notes,
                "recorded_at": item.recorded_at,
            }
            for item in medical_history
        ],
    )

    # -----------------------------------------------------
    # Allergies
    # -----------------------------------------------------

    allergies = list(
        db.scalars(
            select(Allergy)
            .where(
                Allergy.patient_id == patient.id
            )
            .order_by(
                Allergy.recorded_at.desc()
            )
        ).all()
    )

    context.add_section(
        "Allergies",
        [
            {
                "allergen": item.allergen,
                "reaction": item.reaction,
                "severity": item.severity,
                "notes": item.notes,
                "recorded_at": item.recorded_at,
            }
            for item in allergies
        ],
    )

    # -----------------------------------------------------
    # Medications
    # -----------------------------------------------------

    medications = list(
        db.scalars(
            select(Medication)
            .where(
                Medication.patient_id == patient.id
            )
            .order_by(
                Medication.recorded_at.desc()
            )
        ).all()
    )

    context.add_section(
        "Medications",
        [
            {
                "medication_name": item.medication_name,
                "dose": item.dose,
                "frequency": item.frequency,
                "route": item.route,
                "start_date": item.start_date,
                "end_date": item.end_date,
                "status": item.status,
                "prescribed_by": item.prescribed_by,
                "notes": item.notes,
                "recorded_at": item.recorded_at,
            }
            for item in medications
        ],
    )

    # -----------------------------------------------------
    # Recent Vital Signs
    # -----------------------------------------------------

    vital_signs = list(
        db.scalars(
            select(VitalSign)
            .where(
                VitalSign.patient_id == patient.id
            )
            .order_by(
                VitalSign.recorded_at.desc()
            )
            .limit(10)
        ).all()
    )

    context.add_section(
        "Recent Vital Signs",
        [
            {
                "recorded_at": item.recorded_at,
                "height": item.height,
                "weight": item.weight,
                "bmi": item.bmi,
                "blood_pressure_systolic": (
                    item.blood_pressure_systolic
                ),
                "blood_pressure_diastolic": (
                    item.blood_pressure_diastolic
                ),
                "pulse": item.pulse,
                "temperature": item.temperature,
                "oxygen_saturation": (
                    item.oxygen_saturation
                ),
                "assessment_id": item.assessment_id,
            }
            for item in vital_signs
        ],
    )

    # -----------------------------------------------------
    # Lifestyle
    # -----------------------------------------------------

    lifestyle = list(
        db.scalars(
            select(Lifestyle)
            .where(
                Lifestyle.patient_id == patient.id
            )
            .order_by(
                Lifestyle.recorded_at.desc()
            )
            .limit(5)
        ).all()
    )

    context.add_section(
        "Lifestyle",
        [
            {
                "smoking_status": item.smoking_status,
                "alcohol_use": item.alcohol_use,
                "physical_activity_level": (
                    item.physical_activity_level
                ),
                "exercise_frequency": (
                    item.exercise_frequency
                ),
                "diet_pattern": item.diet_pattern,
                "sleep_duration_hours": (
                    item.sleep_duration_hours
                ),
                "sleep_quality": item.sleep_quality,
                "stress_level": item.stress_level,
                "additional_notes": (
                    item.additional_notes
                ),
                "recorded_at": item.recorded_at,
            }
            for item in lifestyle
        ],
    )

    # -----------------------------------------------------
    # Assessments
    # -----------------------------------------------------

    if not request.include_assessments:
        return context

    assessments = list(
        db.scalars(
            select(AssessmentSession)
            .where(
                AssessmentSession.patient_id == patient.id
            )
            .order_by(
                AssessmentSession.started_at.desc()
            )
        ).all()
    )

    assessment_data = []

    for assessment in assessments:
        answers = list(
            db.scalars(
                select(AssessmentAnswer)
                .where(
                    AssessmentAnswer.assessment_id
                    == assessment.id
                )
                .order_by(
                    AssessmentAnswer.answered_at.asc()
                )
            ).all()
        )

        assessment_data.append(
            {
                "assessment_id": assessment.id,
                "assessment_type": assessment.assessment_type,
                "status": assessment.status,
                "started_at": assessment.started_at,
                "completed_at": assessment.completed_at,
                "summary": assessment.summary,
                "notes": assessment.notes,
                "answers": [
                    {
                        "question_id": answer.question_id,
                        "health_concern_id": (
                            answer.health_concern_id
                        ),
                        "answer_text": answer.answer_text,
                        "answer_number": answer.answer_number,
                        "answer_boolean": (
                            answer.answer_boolean
                        ),
                        "answer_json": answer.answer_json,
                        "answered_at": answer.answered_at,
                    }
                    for answer in answers
                ],
            }
        )

    context.add_section(
        "Assessment Findings",
        assessment_data,
    )

    # -----------------------------------------------------
    # Existing Recommendations
    # -----------------------------------------------------

    if request.include_recommendations:
        assessment_ids = [
            assessment.id
            for assessment in assessments
        ]

        if assessment_ids:
            recommendations = list(
                db.scalars(
                    select(Recommendation)
                    .where(
                        Recommendation.assessment_id.in_(
                            assessment_ids
                        )
                    )
                    .order_by(
                        Recommendation.created_at.desc()
                    )
                ).all()
            )
        else:
            recommendations = []

        context.add_section(
            "Existing Recommendations",
            [
                {
                    "assessment_id": item.assessment_id,
                    "health_concern_id": (
                        item.health_concern_id
                    ),
                    "recommendation_type": (
                        item.recommendation_type
                    ),
                    "title": item.title,
                    "recommendation_text": (
                        item.recommendation_text
                    ),
                    "rationale": item.rationale,
                    "priority": item.priority,
                    "source_type": item.source_type,
                    "ai_generated": item.ai_generated,
                    "clinician_review_required": (
                        item.clinician_review_required
                    ),
                    "status": item.status,
                    "created_at": item.created_at,
                }
                for item in recommendations
            ],
        )

    # -----------------------------------------------------
    # Existing Reports
    # -----------------------------------------------------

    if request.include_reports:
        assessment_ids = [
            assessment.id
            for assessment in assessments
        ]

        if assessment_ids:
            reports = list(
                db.scalars(
                    select(Report)
                    .where(
                        Report.assessment_id.in_(
                            assessment_ids
                        )
                    )
                    .order_by(
                        Report.generated_at.desc()
                    )
                ).all()
            )
        else:
            reports = []

        context.add_section(
            "Existing Reports",
            [
                {
                    "assessment_id": item.assessment_id,
                    "report_type": item.report_type,
                    "report_title": item.report_title,
                    "report_content": item.report_content,
                    "executive_summary": (
                        item.executive_summary
                    ),
                    "recommendations_summary": (
                        item.recommendations_summary
                    ),
                    "limitations": item.limitations,
                    "generated_by": item.generated_by,
                    "ai_generated": item.ai_generated,
                    "version": item.version,
                    "status": item.status,
                    "generated_at": item.generated_at,
                }
                for item in reports
            ],
        )

    return context


# =========================================================
# 15A — CLINICAL SUMMARY
# =========================================================

@router.post(
    "/patients/{patient_id}/summary",
    response_model=AIClinicalSummaryResponse,
)
def generate_patient_clinical_summary(
    patient_id: int,
    request: AIClinicalSummaryRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("administrator", "clinician")),
):
    patient = db.scalar(
        select(Patient).where(
            Patient.id == patient_id
        )
    )

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    config = get_ai_config()

    if not config.enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI integration is disabled",
        )

    try:
        provider = get_ai_provider()
    except AIProviderUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    context = _build_patient_context(
        db=db,
        patient=patient,
        request=request,
    )

    try:
        response = provider.generate(
            instructions=CLINICAL_SUMMARY_INSTRUCTIONS,
            input_text=context.to_text(),
        )
    except AIProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI provider request failed: {exc}",
        ) from exc

    return AIClinicalSummaryResponse(
        success=True,
        patient_id=patient.id,
        provider=response.provider,
        model=response.model,
        summary=response.output,
    )


# =========================================================
# 15B — RISK EXPLANATION
# =========================================================

@router.post(
    "/assessments/{assessment_id}/risk-explanation",
    response_model=AIRiskExplanationResponse,
)
def explain_assessment_risk(
    assessment_id: int,
    request: AIRiskExplanationRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("administrator", "clinician")),
):
    from app.services.risk_assessment import (
        assess_assessment_risk,
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

    config = get_ai_config()

    if not config.enabled:
        raise HTTPException(
            status_code=503,
            detail="AI integration is disabled",
        )

    try:
        risk_result = assess_assessment_risk(
            db=db,
            assessment_id=assessment_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    try:
        provider = get_ai_provider()
    except AIProviderUnavailable as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    risk_context = {
        "assessment_id": assessment_id,
        "risk_assessment": risk_result,
    }

    if request.include_context:
        risk_context["assessment_type"] = (
            assessment.assessment_type
        )
        risk_context["assessment_status"] = (
            assessment.status
        )

    input_text = json.dumps(
        risk_context,
        default=str,
        ensure_ascii=False,
        indent=2,
    )

    try:
        ai_response = provider.generate(
            instructions=RISK_EXPLANATION_INSTRUCTIONS,
            input_text=input_text,
        )
    except AIProviderError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"AI provider request failed: {exc}",
        ) from exc

    return AIRiskExplanationResponse(
        success=True,
        assessment_id=assessment_id,
        provider=ai_response.provider,
        model=ai_response.model,
        explanation=ai_response.output,
    )


# =========================================================
# 15C — RECOMMENDATION EXPLANATION
# =========================================================

@router.post(
    "/assessments/{assessment_id}/recommendations/"
    "{recommendation_id}/explanation",
    response_model=AIRecommendationExplanationResponse,
)
def explain_recommendation(
    assessment_id: int,
    recommendation_id: int,
    request: AIRecommendationExplanationRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("administrator", "clinician")),
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

    config = get_ai_config()

    if not config.enabled:
        raise HTTPException(
            status_code=503,
            detail="AI integration is disabled",
        )

    try:
        provider = get_ai_provider()
    except AIProviderUnavailable as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    recommendation_context = {
        "assessment_id": assessment_id,
        "recommendation_id": recommendation_id,
        "recommendation": {
            "recommendation_type": (
                recommendation.recommendation_type
            ),
            "title": recommendation.title,
            "recommendation_text": (
                recommendation.recommendation_text
            ),
            "rationale": recommendation.rationale,
            "priority": recommendation.priority,
            "source_type": recommendation.source_type,
            "ai_generated": recommendation.ai_generated,
            "clinician_review_required": (
                recommendation.clinician_review_required
            ),
            "status": recommendation.status,
        },
    }

    if request.include_assessment_context:
        recommendation_context["assessment"] = {
            "assessment_type": (
                assessment.assessment_type
            ),
            "status": assessment.status,
        }

    input_text = json.dumps(
        recommendation_context,
        default=str,
        ensure_ascii=False,
        indent=2,
    )

    try:
        ai_response = provider.generate(
            instructions=RECOMMENDATION_EXPLANATION_INSTRUCTIONS,
            input_text=input_text,
        )
    except AIProviderError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"AI provider request failed: {exc}",
        ) from exc

    return AIRecommendationExplanationResponse(
        success=True,
        assessment_id=assessment_id,
        recommendation_id=recommendation_id,
        provider=ai_response.provider,
        model=ai_response.model,
        explanation=ai_response.output,
    )


# =========================================================
# 15S — CLINICAL DECISION SUPPORT
# =========================================================

@router.post(
    "/patients/{patient_id}/clinical-decision-support",
    response_model=AIClinicalDecisionSupportResponse,
)
def clinical_decision_support(
    patient_id: int,
    request: AIClinicalDecisionSupportRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("administrator", "clinician")),
):
    patient = db.get(
        Patient,
        patient_id,
    )

    if patient is None:
        raise HTTPException(
            status_code=404,
            detail="Patient not found",
        )

    config = get_ai_config()

    if not config.enabled:
        raise HTTPException(
            status_code=503,
            detail="AI integration is disabled",
        )

    try:
        provider = get_ai_provider()
    except AIProviderUnavailable as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    # IMPORTANT:
    # AIClinicalSummaryRequest does NOT contain
    # include_medical_history, include_medications,
    # or include_vitals.
    context_request = AIClinicalSummaryRequest(
        include_assessments=request.include_assessments,
        include_recommendations=(
            request.include_recommendations
        ),
        include_reports=request.include_reports,
    )

    context = _build_patient_context(
        db=db,
        patient=patient,
        request=context_request,
    )

    input_data = {
        "patient_id": patient_id,
        "clinical_context": context.to_text(),
        "include_risk_assessment": (
            request.include_risk_assessment
        ),
        "include_medical_history": (
            request.include_medical_history
        ),
        "include_medications": (
            request.include_medications
        ),
        "include_vitals": (
            request.include_vitals
        ),
    }

    input_text = json.dumps(
        input_data,
        default=str,
        ensure_ascii=False,
        indent=2,
    )

    try:
        ai_response = provider.generate(
            instructions=(
                CLINICAL_DECISION_SUPPORT_INSTRUCTIONS
            ),
            input_text=input_text,
        )
    except AIProviderError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"AI provider request failed: {exc}",
        ) from exc

    return AIClinicalDecisionSupportResponse(
        success=True,
        patient_id=patient_id,
        provider=ai_response.provider,
        model=ai_response.model,
        decision_support=ai_response.output,
        disclaimer=(
            "AI-generated clinical decision support is "
            "informational and must be reviewed by a "
            "qualified clinician."
        ),
    )


# =========================================================
# 15T — RISK TREND ANALYSIS
# =========================================================

@router.post(
    "/patients/{patient_id}/risk-trend-analysis",
    response_model=AIRiskTrendAnalysisResponse,
)
def risk_trend_analysis(
    patient_id: int,
    request: AIRiskTrendAnalysisRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("administrator", "clinician")),
):
    patient = db.get(
        Patient,
        patient_id,
    )

    if patient is None:
        raise HTTPException(
            status_code=404,
            detail="Patient not found",
        )

    config = get_ai_config()

    if not config.enabled:
        raise HTTPException(
            status_code=503,
            detail="AI integration is disabled",
        )

    try:
        provider = get_ai_provider()
    except AIProviderUnavailable as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    context_request = AIClinicalSummaryRequest(
        include_assessments=request.include_assessments,
        include_recommendations=(
            request.include_recommendations
        ),
        include_reports=False,
    )

    context = _build_patient_context(
        db=db,
        patient=patient,
        request=context_request,
    )

    input_data = {
        "patient_id": patient_id,
        "clinical_context": context.to_text(),
        "include_risk_assessment": (
            request.include_risk_assessment
        ),
    }

    input_text = json.dumps(
        input_data,
        default=str,
        ensure_ascii=False,
        indent=2,
    )

    try:
        ai_response = provider.generate(
            instructions=RISK_TREND_ANALYSIS_INSTRUCTIONS,
            input_text=input_text,
        )
    except AIProviderError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"AI provider request failed: {exc}",
        ) from exc

    return AIRiskTrendAnalysisResponse(
        success=True,
        patient_id=patient_id,
        provider=ai_response.provider,
        model=ai_response.model,
        risk_trend_analysis=ai_response.output,
        disclaimer=(
            "AI-generated risk trend analysis is "
            "informational and must be reviewed by a "
            "qualified clinician."
        ),
    )


# =========================================================
# 15U — RECOMMENDATION PRIORITIZATION
# =========================================================

@router.post(
    "/patients/{patient_id}/recommendation-prioritization",
    response_model=AIRecommendationPrioritizationResponse,
)
def recommendation_prioritization(
    patient_id: int,
    request: AIRecommendationPrioritizationRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("administrator", "clinician")),
):
    patient = db.get(
        Patient,
        patient_id,
    )

    if patient is None:
        raise HTTPException(
            status_code=404,
            detail="Patient not found",
        )

    config = get_ai_config()

    if not config.enabled:
        raise HTTPException(
            status_code=503,
            detail="AI integration is disabled",
        )

    try:
        provider = get_ai_provider()
    except AIProviderUnavailable as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    context_request = AIClinicalSummaryRequest(
        include_assessments=request.include_assessments,
        include_recommendations=(
            request.include_recommendations
        ),
        include_reports=request.include_reports,
    )

    context = _build_patient_context(
        db=db,
        patient=patient,
        request=context_request,
    )

    input_data = {
        "patient_id": patient_id,
        "clinical_context": context.to_text(),
        "include_risk_assessment": (
            request.include_risk_assessment
        ),
    }

    input_text = json.dumps(
        input_data,
        default=str,
        ensure_ascii=False,
        indent=2,
    )

    try:
        ai_response = provider.generate(
            instructions=(
                RECOMMENDATION_PRIORITIZATION_INSTRUCTIONS
            ),
            input_text=input_text,
        )
    except AIProviderError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"AI provider request failed: {exc}",
        ) from exc

    return AIRecommendationPrioritizationResponse(
        success=True,
        patient_id=patient_id,
        provider=ai_response.provider,
        model=ai_response.model,
        recommendation_prioritization=(
            ai_response.output
        ),
        disclaimer=(
            "AI-generated recommendation prioritization "
            "does not change existing recommendation "
            "priority values and must be reviewed by a "
            "qualified clinician."
        ),
    )


# =========================================================
# 15V — LONGITUDINAL PATIENT SUMMARY
# =========================================================

@router.post(
    "/patients/{patient_id}/longitudinal-summary",
    response_model=AILongitudinalPatientSummaryResponse,
)
def longitudinal_patient_summary(
    patient_id: int,
    request: AILongitudinalPatientSummaryRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("administrator", "clinician")),
):
    patient = db.get(
        Patient,
        patient_id,
    )

    if patient is None:
        raise HTTPException(
            status_code=404,
            detail="Patient not found",
        )

    config = get_ai_config()

    if not config.enabled:
        raise HTTPException(
            status_code=503,
            detail="AI integration is disabled",
        )

    try:
        provider = get_ai_provider()
    except AIProviderUnavailable as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    context_request = AIClinicalSummaryRequest(
        include_assessments=request.include_assessments,
        include_recommendations=(
            request.include_recommendations
        ),
        include_reports=request.include_reports,
    )

    context = _build_patient_context(
        db=db,
        patient=patient,
        request=context_request,
    )

    input_data = {
        "patient_id": patient_id,
        "clinical_context": context.to_text(),
        "include_risk_assessment": (
            request.include_risk_assessment
        ),
        "include_medical_history": (
            request.include_medical_history
        ),
        "include_medications": (
            request.include_medications
        ),
        "include_vitals": (
            request.include_vitals
        ),
    }

    input_text = json.dumps(
        input_data,
        default=str,
        ensure_ascii=False,
        indent=2,
    )

    try:
        ai_response = provider.generate(
            instructions=(
                LONGITUDINAL_PATIENT_SUMMARY_INSTRUCTIONS
            ),
            input_text=input_text,
        )
    except AIProviderError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"AI provider request failed: {exc}",
        ) from exc

    return AILongitudinalPatientSummaryResponse(
        success=True,
        patient_id=patient_id,
        provider=ai_response.provider,
        model=ai_response.model,
        longitudinal_summary=ai_response.output,
        disclaimer=(
            "AI-generated longitudinal summary is "
            "informational and must be reviewed by a "
            "qualified clinician."
        ),
    )


# =========================================================
# 15W — CARE PLAN REVIEW
# =========================================================

@router.post(
    "/patients/{patient_id}/care-plan-review",
    response_model=AICarePlanReviewResponse,
)
def care_plan_review(
    patient_id: int,
    request: AICarePlanReviewRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("administrator", "clinician")),
):
    patient = db.get(
        Patient,
        patient_id,
    )

    if patient is None:
        raise HTTPException(
            status_code=404,
            detail="Patient not found",
        )

    config = get_ai_config()

    if not config.enabled:
        raise HTTPException(
            status_code=503,
            detail="AI integration is disabled",
        )

    try:
        provider = get_ai_provider()
    except AIProviderUnavailable as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    context_request = AIClinicalSummaryRequest(
        include_assessments=request.include_assessments,
        include_recommendations=(
            request.include_recommendations
        ),
        include_reports=request.include_reports,
    )

    context = _build_patient_context(
        db=db,
        patient=patient,
        request=context_request,
    )

    # CareSphere currently does not have a dedicated
    # CarePlan model in the confirmed schema. Therefore
    # this endpoint reviews the available longitudinal
    # clinical documentation instead of inventing a
    # care-plan record.

    documentation_availability = {
        "assessments": False,
        "medical_history": False,
        "medications": False,
        "vitals": False,
        "recommendations": False,
        "reports": False,
        "dedicated_care_plan_model": False,
    }

    if request.include_assessments:
        documentation_availability["assessments"] = bool(
            db.scalar(
                select(AssessmentSession.id)
                .where(
                    AssessmentSession.patient_id
                    == patient_id
                )
                .limit(1)
            )
        )

    if request.include_recommendations:
        documentation_availability[
            "recommendations"
        ] = bool(
            db.scalar(
                select(Recommendation.id)
                .join(
                    AssessmentSession,
                    Recommendation.assessment_id
                    == AssessmentSession.id,
                )
                .where(
                    AssessmentSession.patient_id
                    == patient_id
                )
                .limit(1)
            )
        )

    if request.include_reports:
        documentation_availability["reports"] = bool(
            db.scalar(
                select(Report.id)
                .join(
                    AssessmentSession,
                    Report.assessment_id
                    == AssessmentSession.id,
                )
                .where(
                    AssessmentSession.patient_id
                    == patient_id
                )
                .limit(1)
            )
        )

    documentation_availability["medical_history"] = bool(
        db.scalar(
            select(MedicalHistory.id)
            .where(
                MedicalHistory.patient_id == patient_id
            )
            .limit(1)
        )
    )

    documentation_availability["medications"] = bool(
        db.scalar(
            select(Medication.id)
            .where(
                Medication.patient_id == patient_id
            )
            .limit(1)
        )
    )

    documentation_availability["vitals"] = bool(
        db.scalar(
            select(VitalSign.id)
            .where(
                VitalSign.patient_id == patient_id
            )
            .limit(1)
        )
    )

    input_data = {
        "patient_id": patient_id,
        "clinical_context": context.to_text(),
        "documentation_availability": (
            documentation_availability
        ),
        "include_risk_assessment": (
            request.include_risk_assessment
        ),
        "include_documentation_gaps": (
            request.include_documentation_gaps
        ),
    }

    input_text = json.dumps(
        input_data,
        default=str,
        ensure_ascii=False,
        indent=2,
    )

    try:
        ai_response = provider.generate(
            instructions=CARE_PLAN_REVIEW_INSTRUCTIONS,
            input_text=input_text,
        )
    except AIProviderError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"AI provider request failed: {exc}",
        ) from exc

    return AICarePlanReviewResponse(
        success=True,
        patient_id=patient_id,
        provider=ai_response.provider,
        model=ai_response.model,
        care_plan_review=ai_response.output,
        disclaimer=(
            "AI-generated care-plan review is "
            "informational. CareSphere does not use this "
            "endpoint to create or modify a care plan, "
            "and a qualified clinician must review the "
            "output."
        ),
    )


# =========================================================
# 15X — CLINICIAN BRIEFING
# =========================================================

@router.post(
    "/patients/{patient_id}/clinician-briefing",
    response_model=AIClinicianBriefingResponse,
)
def clinician_briefing(
    patient_id: int,
    request: AIClinicianBriefingRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("administrator", "clinician")),
):
    patient = db.get(
        Patient,
        patient_id,
    )

    if patient is None:
        raise HTTPException(
            status_code=404,
            detail="Patient not found",
        )

    config = get_ai_config()

    if not config.enabled:
        raise HTTPException(
            status_code=503,
            detail="AI integration is disabled",
        )

    try:
        provider = get_ai_provider()
    except AIProviderUnavailable as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    context_request = AIClinicalSummaryRequest(
        include_assessments=request.include_assessments,
        include_recommendations=(
            request.include_recommendations
        ),
        include_reports=request.include_reports,
    )

    context = _build_patient_context(
        db=db,
        patient=patient,
        request=context_request,
    )

    input_data = {
        "patient_id": patient_id,
        "clinical_context": context.to_text(),
        "include_risk_assessment": (
            request.include_risk_assessment
        ),
        "include_medical_history": (
            request.include_medical_history
        ),
        "include_medications": (
            request.include_medications
        ),
        "include_vitals": (
            request.include_vitals
        ),
        "include_documentation_gaps": (
            request.include_documentation_gaps
        ),
    }

    input_text = json.dumps(
        input_data,
        default=str,
        ensure_ascii=False,
        indent=2,
    )

    try:
        ai_response = provider.generate(
            instructions=CLINICIAN_BRIEFING_INSTRUCTIONS,
            input_text=input_text,
        )
    except AIProviderError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"AI provider request failed: {exc}",
        ) from exc

    return AIClinicianBriefingResponse(
        success=True,
        patient_id=patient_id,
        provider=ai_response.provider,
        model=ai_response.model,
        clinician_briefing=ai_response.output,
        disclaimer=(
            "AI-generated clinician briefing is "
            "informational and must be reviewed by a "
            "qualified clinician. It does not replace "
            "clinical judgment."
        ),
    )