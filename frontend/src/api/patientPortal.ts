import api from "./client";
import type { Patient, PatientProfile } from "./patients";

export interface PatientProfileUpdate {
  first_name?: string;
  last_name?: string;
  date_of_birth?: string;
  sex?: string;
  marital_status?: string;
  occupation?: string;
  preferred_language?: string;
  residence?: string;
  district?: string;
  country?: string;
}

export interface ContactInput {
  phone?: string;
  email?: string;
  address?: string;
  next_of_kin?: string;
  next_of_kin_phone?: string;
  emergency_contact?: string;
  emergency_phone?: string;
  relationship?: string;
}

export interface MedicalHistoryInput {
  condition_name: string;
  description?: string;
  diagnosed_date?: string;
  status?: string;
  notes?: string;
}

export interface AllergyInput {
  allergen: string;
  reaction?: string;
  severity?: string;
  notes?: string;
}

export interface MedicationInput {
  medication_name: string;
  dose?: string;
  frequency?: string;
  route?: string;
  start_date?: string;
  end_date?: string;
  status?: string;
  prescribed_by?: string;
  notes?: string;
}

export interface LifestyleInput {
  smoking_status?: string;
  alcohol_use?: string;
  physical_activity_level?: string;
  exercise_frequency?: string;
  diet_pattern?: string;
  sleep_duration_hours?: number;
  sleep_quality?: string;
  stress_level?: string;
  additional_notes?: string;
}

export interface VitalSignInput {
  height?: number;
  weight?: number;
  bmi?: number;
  blood_pressure_systolic?: number;
  blood_pressure_diastolic?: number;
  pulse?: number;
  temperature?: number;
  oxygen_saturation?: number;
}

export interface PatientCareSummary {
  recommendations: Array<{
    id: number;
    title: string;
    recommendation_text: string;
    priority: string | null;
    source_type: string | null;
    ai_generated: boolean;
    status: string;
    updated_at: string;
  }>;
  reports: Array<{
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
    clinician_id: number | null;
    clinician_guidance: string | null;
    clinician_review_status: string | null;
    patient_reviewed_at: string | null;
  }>;
}

export async function registerPatient(data: {
  username: string;
  password: string;
  first_name: string;
  last_name: string;
  date_of_birth?: string;
  sex?: string;
  marital_status?: string;
  occupation?: string;
  preferred_language?: string;
  residence?: string;
  district?: string;
  country?: string;
}) {
  const response = await api.post("/auth/register/patient", data);
  return response.data as {
    access_token: string;
    token_type: string;
    user: {
      id: number;
      username: string;
      full_name: string;
      role: "patient";
      status: string;
      permissions: string[];
      patient_id: number | null;
    };
  };
}
export async function updateMyContact(
  contactId: number,
  data: ContactInput,
) {
  const response = await api.put(
    `/patient/me/contacts/${contactId}`,
    data,
  );
  return response.data;
}
export async function updateMyPatientProfile(data: PatientProfileUpdate): Promise<Patient> {
  const response = await api.put<Patient>("/patient/me/profile", data);
  return response.data;
}

export async function addMyContact(data: ContactInput) {
  const response = await api.post("/patient/me/contacts", data);
  return response.data;
}

export async function addMyMedicalHistory(data: MedicalHistoryInput) {
  const response = await api.post("/patient/me/medical-history", data);
  return response.data;
}

export async function addMyAllergy(data: AllergyInput) {
  const response = await api.post("/patient/me/allergies", data);
  return response.data;
}

export async function addMyMedication(data: MedicationInput) {
  const response = await api.post("/patient/me/medications", data);
  return response.data;
}

export async function addMyLifestyle(data: LifestyleInput) {
  const response = await api.post("/patient/me/lifestyle", data);
  return response.data;
}

export async function addMyVitalSigns(data: VitalSignInput) {
  const response = await api.post("/patient/me/vital-signs", data);
  return response.data;
}

export async function getMyCareSummary(): Promise<PatientCareSummary> {
  const response = await api.get<PatientCareSummary>("/patient/me/care-summary");
  return response.data;
}

export type { PatientProfile };


export async function markMyReportReviewed(reportId: number) {
  const response = await api.post<{ report_id: number; reviewed_at: string | null }>(`/patient/me/reports/${reportId}/reviewed`);
  return response.data;
}
