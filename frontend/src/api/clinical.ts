import api from "./client";
import type { Patient } from "./patients";

export interface AssessmentSession {
  id: number;
  patient_id: number;
  assessment_type: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  assessed_by: number | null;
  summary: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface Recommendation {
  id: number;
  assessment_id: number;
  health_concern_id: number | null;
  recommendation_type: string;
  title: string;
  recommendation_text: string;
  rationale: string | null;
  priority: string | null;
  source_type: string | null;
  ai_generated: boolean;
  clinician_review_required: boolean;
  status: string;
  created_at: string;
  updated_at: string;
  created_by: number | null;
}

export interface Report {
  id: number;
  assessment_id: number;
  report_type: string;
  report_title: string;
  report_content: unknown;
  executive_summary: string | null;
  recommendations_summary: string | null;
  limitations: string | null;
  generated_by: string | null;
  ai_generated: boolean;
  version: number;
  status: string;
  generated_at: string;
  created_by: number | null;
  updated_at: string;
  clinician_id?: number | null;
  clinician_guidance?: string | null;
  clinician_review_status?: string | null;
  clinician_reviewed_at?: string | null;
  released_to_patient?: boolean;
  patient_reviewed_at?: string | null;
  last_viewed_at?: string | null;
}

export interface ClinicianReview {
  id: number;
  assessment_id: number;
  recommendation_id: number | null;
  report_id: number | null;
  clinician_id: number;
  review_status: string;
  clinical_comment: string | null;
  modification_notes: string | null;
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface RiskAssessmentResult {
  assessment_id: number;
  patient_id: number;
  risk_factors: {
    factor_count: number;
    factors: Array<{
      factor: string;
      severity: string;
      value: unknown;
    }>;
  };
  risk_score: {
    score: number;
    risk_level: string;
    factor_count: number;
  };
  recommendations: Array<{
    recommendation_type: string;
    title: string;
    recommendation_text: string;
    priority: string;
    source_type: string;
    ai_generated: boolean;
    clinician_review_required: boolean;
  }>;
  assessment_summary: {
    summary?: string;
    urgent_concerns?: unknown[];
    [key: string]: unknown;
  };
}

export interface ReportPatientAccess {
  report_id: number;
  patient_id: number;
  released_to_patient: boolean;
  patient_reviewed_at: string | null;
  last_viewed_at: string | null;
}

export interface AdminReviewedReport {
  report: Report;
  patient: Patient;
  clinician: {
    id: number;
    full_name: string;
    username: string;
  };
  review_status: string;
  reviewed_at: string;
  released_to_patient: boolean;
  patient_reviewed_at: string | null;
  last_viewed_at: string | null;
}

export interface AIClinicalSummaryResponse {
  success: boolean;
  patient_id: number;
  provider: string;
  model: string;
  summary: string;
  disclaimer: string;
}

export interface AIClinicalDecisionSupportResponse {
  success: boolean;
  patient_id: number;
  provider: string;
  model: string;
  decision_support: string;
  disclaimer: string;
}

export async function listAssessments(patientId: number, limit = 50) {
  const response = await api.get<AssessmentSession[]>(
    `/patient/${patientId}/assessments`,
    { params: { limit } },
  );
  return response.data;
}

export async function createAssessment(
  patientId: number,
  data: {
    assessment_type: string;
    status?: string;
    summary?: string;
    notes?: string;
  },
) {
  const response = await api.post<AssessmentSession>(
    `/patient/${patientId}/assessments`,
    data,
  );
  return response.data;
}

export async function completeAssessment(assessmentId: number) {
  const response = await api.post<AssessmentSession>(
    `/patient/assessment-sessions/${assessmentId}/complete`,
  );
  return response.data;
}

export async function getRiskAssessment(assessmentId: number) {
  const response = await api.get<RiskAssessmentResult>(
    `/assessments/${assessmentId}/risk-assessment`,
  );
  return response.data;
}

export async function generateRiskRecommendations(assessmentId: number) {
  const response = await api.post<{
    assessment_id: number;
    recommendation_count: number;
    recommendations: Recommendation[];
  }>(`/assessments/${assessmentId}/risk-assessment/recommendations`);
  return response.data;
}

export async function listRecommendations(assessmentId: number) {
  const response = await api.get<Recommendation[]>(
    `/assessments/${assessmentId}/recommendations`,
  );
  return response.data;
}

export async function submitRecommendationForReview(
  assessmentId: number,
  recommendationId: number,
) {
  const response = await api.post<ClinicianReview>(
    `/assessments/${assessmentId}/risk-assessment/recommendations/${recommendationId}/submit-review`,
  );
  return response.data;
}

export async function updateRecommendationReview(
  assessmentId: number,
  recommendationId: number,
  reviewStatus: "pending" | "approved" | "rejected" | "completed",
  clinicalComment?: string,
  modificationNotes?: string,
) {
  const response = await api.put<{
    review: ClinicianReview;
    recommendation: Recommendation;
  }>(
    `/assessments/${assessmentId}/risk-assessment/recommendations/${recommendationId}/review`,
    undefined,
    {
      params: {
        review_status: reviewStatus,
        clinical_comment: clinicalComment,
        modification_notes: modificationNotes,
      },
    },
  );
  return response.data;
}

export async function listReports(assessmentId: number) {
  const response = await api.get<Report[]>(
    `/assessments/${assessmentId}/reports`,
  );
  return response.data;
}

export async function generateAssessmentReport(assessmentId: number) {
  const response = await api.post<Report>(
    `/assessments/${assessmentId}/risk-assessment/report`,
  );
  return response.data;
}

export async function submitReportForReview(
  assessmentId: number,
  reportId: number,
) {
  const response = await api.post<{
    review: ClinicianReview;
    report: Report;
  }>(
    `/assessments/${assessmentId}/risk-assessment/reports/${reportId}/submit-review`,
  );
  return response.data;
}

export async function updateReportReview(
  assessmentId: number,
  reportId: number,
  reviewStatus: "pending" | "reviewed" | "approved" | "rejected" | "completed",
  clinicalComment?: string,
  modificationNotes?: string,
) {
  const response = await api.put<{
    review: ClinicianReview;
    report: Report;
  }>(
    `/assessments/${assessmentId}/risk-assessment/reports/${reportId}/review`,
    undefined,
    {
      params: {
        review_status: reviewStatus,
        clinical_comment: clinicalComment,
        modification_notes: modificationNotes,
      },
    },
  );
  return response.data;
}

export async function listClinicianReviews(
  assessmentId: number,
): Promise<ClinicianReview[]> {
  const response = await api.get<ClinicianReview[]>(
    `/assessments/${assessmentId}/risk-assessment/reviews`,
  );

  return response.data;
}

export async function getReportPatientAccess(reportId: number) {
  const response = await api.get<ReportPatientAccess>(`/assessments/reports/${reportId}/patient-access`);
  return response.data;
}

export async function releaseReportToPatient(
  assessmentId: number,
  reportId: number,
  clinicalComment?: string,
) {
  const response = await api.post<{
    review: ClinicianReview;
    report: Report;
    patient_access: ReportPatientAccess;
  }>(
    `/assessments/${assessmentId}/reports/${reportId}/release-to-patient`,
    undefined,
    clinicalComment
      ? { params: { clinical_comment: clinicalComment } }
      : undefined,
  );
  return response.data;
}


export async function listAdminReviewedReports(limit = 50) {
  const response = await api.get<AdminReviewedReport[]>("/assessments/reports/reviewed", {
    params: { limit },
  });
  return response.data;
}

export async function deleteReport(reportId: number) {
  const response = await api.delete<{ deleted: boolean; report_id: number }>(
    `/assessments/reports/${reportId}`,
  );
  return response.data;
}

export async function generatePatientClinicalSummary(
  patientId: number,
  data = {
    include_assessments: true,
    include_recommendations: true,
    include_reports: true,
  },
) {
  const response = await api.post<AIClinicalSummaryResponse>(
    `/ai/patients/${patientId}/summary`,
    data,
  );
  return response.data;
}

export async function runClinicalDecisionSupport(
  patientId: number,
  data = {
    include_assessments: true,
    include_risk_assessment: true,
    include_medical_history: true,
    include_medications: true,
    include_vitals: true,
    include_recommendations: true,
    include_reports: true,
  },
) {
  const response = await api.post<AIClinicalDecisionSupportResponse>(
    `/ai/patients/${patientId}/clinical-decision-support`,
    data,
  );
  return response.data;
}
export async function getAIProviderStatus(): Promise<{
  enabled: boolean;
  provider: string;
  model_configured: boolean;
  api_key_configured: boolean;
  base_url_configured: boolean;
}> {
  const response = await api.get<{
    enabled: boolean;
    provider: string;
    model_configured: boolean;
    api_key_configured: boolean;
    base_url_configured: boolean;
  }>("/ai/status");

  return response.data;
}

export async function getAIProviderHealth(): Promise<{
  available: boolean;
  provider: string;
  model: string | null;
  message: string;
}> {
  const response = await api.get<{
    available: boolean;
    provider: string;
    model: string | null;
    message: string;
  }>("/ai/health");

  return response.data;
}