from pydantic import BaseModel, Field


class AIStatusResponse(BaseModel):
    enabled: bool
    provider: str
    model_configured: bool
    api_key_configured: bool
    base_url_configured: bool


class AIProviderHealthResponse(BaseModel):
    available: bool
    provider: str
    model: str | None
    message: str


class AIResponse(BaseModel):
    success: bool
    provider: str
    model: str
    output: str
    disclaimer: str


# ============================================================
# 15B — CLINICAL SUMMARY AI
# ============================================================

class AIClinicalSummaryRequest(BaseModel):
    include_assessments: bool = True
    include_recommendations: bool = True
    include_reports: bool = True


class AIClinicalSummaryResponse(BaseModel):
    success: bool
    patient_id: int
    provider: str
    model: str
    summary: str
    disclaimer: str = Field(
        default=(
            "AI-generated clinical support content. "
            "Review against the patient's documented record "
            "before making clinical decisions."
        )
    )


# ============================================================
# 15C — RISK EXPLANATION AI
# ============================================================

class AIRiskExplanationRequest(BaseModel):
    include_context: bool = True


class AIRiskExplanationResponse(BaseModel):
    success: bool
    assessment_id: int
    provider: str
    model: str
    explanation: str
    disclaimer: str = Field(
        default=(
            "AI-generated explanation of a deterministic risk assessment. "
            "The underlying risk assessment is produced by CareSphere's "
            "deterministic clinical engine. Review the documented assessment "
            "and patient record before making clinical decisions."
        )
    )


# ============================================================
# 15D — RECOMMENDATION EXPLANATION AI
# ============================================================

class AIRecommendationExplanationRequest(BaseModel):
    include_assessment_context: bool = True


class AIRecommendationExplanationResponse(BaseModel):
    success: bool
    assessment_id: int
    recommendation_id: int
    provider: str
    model: str
    explanation: str
    disclaimer: str = Field(
        default=(
            "AI-generated explanation of an existing clinical "
            "recommendation. Review the documented recommendation "
            "and patient record before making clinical decisions."
        )
    )


# ============================================================
# 15E — REPORT EXPLANATION AI
# ============================================================

class AIReportExplanationRequest(BaseModel):
    include_assessment_context: bool = True


class AIReportExplanationResponse(BaseModel):
    success: bool
    assessment_id: int
    report_id: int
    provider: str
    model: str
    explanation: str
    disclaimer: str = Field(
        default=(
            "AI-generated explanation of an existing clinical report. "
            "Review the documented report and patient record before "
            "making clinical decisions."
        )
    )
    # 15F
class AIDecisionSupportOverviewRequest(BaseModel):
    include_assessments: bool = True
    include_recommendations: bool = True
    include_reports: bool = True
    include_risk_assessment: bool = True


class AIDecisionSupportOverviewResponse(BaseModel):
    success: bool
    patient_id: int
    provider: str
    model: str
    overview: str
    disclaimer: str = Field(
        default=(
            "AI-generated clinical decision-support content based on "
            "documented CareSphere clinical information and existing "
            "deterministic outputs. Review the documented patient record "
            "and clinical findings before making clinical decisions."
        )
    )
    # 15G
class AIPatientTimelineSynthesisRequest(BaseModel):
    include_assessments: bool = True
    include_vitals: bool = True
    include_medications: bool = True
    include_medical_history: bool = True
    include_recommendations: bool = True
    include_reports: bool = True


class AIPatientTimelineSynthesisResponse(BaseModel):
    success: bool
    patient_id: int
    provider: str
    model: str
    synthesis: str
    disclaimer: str = Field(
        default=(
            "AI-generated synthesis of documented patient timeline "
            "information. Review the underlying clinical record "
            "before making clinical decisions."
        )
    )
    # 15H
class AIFollowUpPlanningRequest(BaseModel):
    include_assessments: bool = True
    include_risk_assessment: bool = True
    include_recommendations: bool = True
    include_reports: bool = True


class AIFollowUpPlanningResponse(BaseModel):
    success: bool
    patient_id: int
    provider: str
    model: str
    follow_up_plan: str
    disclaimer: str = Field(
        default=(
            "AI-generated clinical follow-up planning based on "
            "documented CareSphere information and existing clinical "
            "outputs. This content does not create or modify treatment "
            "plans. Review the underlying clinical record before making "
            "clinical decisions."
        )
    )
    # 15I
class AIClinicalQuestionRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=2000,
    )
    include_assessments: bool = True
    include_recommendations: bool = True
    include_reports: bool = True
    include_risk_assessment: bool = True


class AIClinicalQuestionResponse(BaseModel):
    success: bool
    patient_id: int
    provider: str
    model: str
    answer: str
    disclaimer: str = Field(
        default=(
            "AI-generated answer based only on documented CareSphere "
            "clinical information and existing deterministic outputs. "
            "Review the underlying clinical record before making "
            "clinical decisions."
        )
    )
# 15J
class AIClinicalRecordGapRequest(BaseModel):
    include_assessments: bool = True
    include_risk_assessment: bool = True
    include_recommendations: bool = True
    include_reports: bool = True


class AIClinicalRecordGapResponse(BaseModel):
    success: bool
    patient_id: int
    provider: str
    model: str
    gaps: str
    disclaimer: str = Field(
        default=(
            "AI-generated identification of potentially missing, "
            "incomplete, or unclear documented information based on "
            "the supplied CareSphere record. A documentation gap does "
            "not indicate that a clinical condition or event exists. "
            "Review the underlying clinical record before making "
            "clinical decisions."
        )
    )
    # 15K
class AIClinicalHandoffRequest(BaseModel):
    include_assessments: bool = True
    include_risk_assessment: bool = True
    include_recommendations: bool = True
    include_reports: bool = True
    include_documentation_gaps: bool = True


class AIClinicalHandoffResponse(BaseModel):
    success: bool
    patient_id: int
    provider: str
    model: str
    handoff_summary: str
    disclaimer: str = Field(
        default=(
            "AI-generated clinical handoff summary based only on "
            "documented CareSphere information and existing clinical "
            "outputs. Review the underlying clinical record before "
            "making clinical decisions."
        )
    )
    # 15L
class AICarePlanReviewRequest(BaseModel):
    include_assessments: bool = True
    include_risk_assessment: bool = True
    include_recommendations: bool = True
    include_reports: bool = True
    include_documentation_gaps: bool = True


class AICarePlanReviewResponse(BaseModel):
    success: bool
    patient_id: int
    provider: str
    model: str
    care_plan_review: str
    disclaimer: str = Field(
        default=(
            "AI-generated care-plan review based only on the "
            "supplied CareSphere record. It does not create or "
            "modify clinical decisions, diagnoses, risk scores, "
            "recommendations, or treatment plans. Clinician review "
            "is required."
        )
    )
    # 15M
class AICareCoordinationRequest(BaseModel):
    include_assessments: bool = True
    include_risk_assessment: bool = True
    include_recommendations: bool = True
    include_reports: bool = True
    include_care_plan_review: bool = True


class AICareCoordinationResponse(BaseModel):
    success: bool
    patient_id: int
    provider: str
    model: str
    coordination_summary: str
    disclaimer: str = Field(
        default=(
            "AI-generated care-coordination summary based only on "
            "the supplied CareSphere record. It does not create or "
            "modify diagnoses, risk scores, recommendations, "
            "treatments, or care plans. Clinician review is required."
        )
    )


# 15N
class AIMedicationReviewRequest(BaseModel):
    include_assessments: bool = True
    include_risk_assessment: bool = True
    include_recommendations: bool = True
    include_reports: bool = True
    include_medical_history: bool = True


class AIMedicationReviewResponse(BaseModel):
    success: bool
    patient_id: int
    provider: str
    model: str
    medication_review: str
    disclaimer: str = Field(
        default=(
            "AI-generated medication review based only on the "
            "supplied CareSphere record. It does not prescribe, "
            "discontinue, modify, or recommend medication changes. "
            "Clinician review is required."
        )
    )


# 15O
class AIPreventiveCareReviewRequest(BaseModel):
    include_assessments: bool = True
    include_risk_assessment: bool = True
    include_recommendations: bool = True
    include_reports: bool = True
    include_medical_history: bool = True
    include_vitals: bool = True


class AIPreventiveCareReviewResponse(BaseModel):
    success: bool
    patient_id: int
    provider: str
    model: str
    preventive_care_review: str
    disclaimer: str = Field(
        default=(
            "AI-generated preventive-care review based only on "
            "the supplied CareSphere record. It does not establish "
            "eligibility, create diagnoses, or prescribe preventive "
            "interventions. Clinician review is required."
        )
    )


# 15P
class AIPatientEducationRequest(BaseModel):
    topic: str | None = Field(
        default=None,
        max_length=500,
    )
    include_assessments: bool = True
    include_risk_assessment: bool = True
    include_recommendations: bool = True
    include_reports: bool = True


class AIPatientEducationResponse(BaseModel):
    success: bool
    patient_id: int
    provider: str
    model: str
    education: str
    disclaimer: str = Field(
        default=(
            "AI-generated patient education based only on the "
            "supplied CareSphere record. Educational content does "
            "not replace individualized clinical advice, diagnosis, "
            "or treatment. Clinician review is recommended."
        )
    )


# 15Q
class AIClinicalDocumentationSummaryRequest(BaseModel):
    include_assessments: bool = True
    include_risk_assessment: bool = True
    include_recommendations: bool = True
    include_reports: bool = True
    include_documentation_gaps: bool = True


class AIClinicalDocumentationSummaryResponse(BaseModel):
    success: bool
    patient_id: int
    provider: str
    model: str
    documentation_summary: str
    disclaimer: str = Field(
        default=(
            "AI-generated documentation summary based only on "
            "the supplied CareSphere record. It does not create, "
            "alter, or replace clinical documentation or clinical "
            "decisions. Clinician review is required."
        )
    )


# 15R
class AIEncounterPreparationRequest(BaseModel):
    include_assessments: bool = True
    include_risk_assessment: bool = True
    include_recommendations: bool = True
    include_reports: bool = True
    include_documentation_gaps: bool = True
    include_medical_history: bool = True
    include_medications: bool = True
    include_vitals: bool = True


class AIEncounterPreparationResponse(BaseModel):
    success: bool
    patient_id: int
    provider: str
    model: str
    encounter_preparation: str
    disclaimer: str = Field(
        default=(
            "AI-generated encounter-preparation summary based only "
            "on the supplied CareSphere record. It does not create "
            "diagnoses, risk scores, treatment plans, prescriptions, "
            "or new clinical recommendations. Clinician review is "
            "required."
        )
    )
# =========================================================
# 15S — Clinical Decision Support
# =========================================================

class AIClinicalDecisionSupportRequest(BaseModel):
    include_assessments: bool = True
    include_risk_assessment: bool = True
    include_medical_history: bool = True
    include_medications: bool = True
    include_vitals: bool = True
    include_recommendations: bool = True
    include_reports: bool = True


class AIClinicalDecisionSupportResponse(BaseModel):
    success: bool
    patient_id: int
    provider: str
    model: str
    decision_support: str
    disclaimer: str


# =========================================================
# 15T — Risk Trend Analysis
# =========================================================

class AIRiskTrendAnalysisRequest(BaseModel):
    include_assessments: bool = True
    include_risk_assessment: bool = True
    include_recommendations: bool = True


class AIRiskTrendAnalysisResponse(BaseModel):
    success: bool
    patient_id: int
    provider: str
    model: str
    risk_trend_analysis: str
    disclaimer: str


# =========================================================
# 15U — Recommendation Prioritization
# =========================================================

class AIRecommendationPrioritizationRequest(BaseModel):
    include_assessments: bool = True
    include_risk_assessment: bool = True
    include_recommendations: bool = True
    include_reports: bool = True


class AIRecommendationPrioritizationResponse(BaseModel):
    success: bool
    patient_id: int
    provider: str
    model: str
    recommendation_prioritization: str
    disclaimer: str


# =========================================================
# 15V — Longitudinal Patient Summary
# =========================================================

class AILongitudinalPatientSummaryRequest(BaseModel):
    include_assessments: bool = True
    include_risk_assessment: bool = True
    include_medical_history: bool = True
    include_medications: bool = True
    include_vitals: bool = True
    include_recommendations: bool = True
    include_reports: bool = True


class AILongitudinalPatientSummaryResponse(BaseModel):
    success: bool
    patient_id: int
    provider: str
    model: str
    longitudinal_summary: str
    disclaimer: str

# =========================================================
# 15X — Clinician Briefing
# =========================================================

class AIClinicianBriefingRequest(BaseModel):
    include_assessments: bool = True
    include_risk_assessment: bool = True
    include_medical_history: bool = True
    include_medications: bool = True
    include_vitals: bool = True
    include_recommendations: bool = True
    include_reports: bool = True
    include_documentation_gaps: bool = True


class AIClinicianBriefingResponse(BaseModel):
    success: bool
    patient_id: int
    provider: str
    model: str
    clinician_briefing: str
    disclaimer: str
    