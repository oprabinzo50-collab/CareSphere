import api from "./client";

export interface Patient {
  id: number;
  patient_number: string;
  first_name: string;
  last_name: string;
  date_of_birth: string | null;
  sex: string | null;
  marital_status: string | null;
  occupation: string | null;
  preferred_language: string | null;
  residence: string | null;
  district: string | null;
  country: string | null;
  status: string | null;
}

export interface PatientSearchParams {
  search?: string;
  patient_number?: string;
  first_name?: string;
  last_name?: string;
  district?: string;
  sex?: string;
  status?: string;
  limit?: number;
  offset?: number;
}

export interface PatientCreateRequest {
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
}

export interface PatientProfile {
  patient: Patient;
  contacts: unknown[];
  medical_history: unknown[];
  allergies: unknown[];
  medications: unknown[];
  lifestyle: unknown[];
  vital_signs: unknown[];
  assessments: unknown[];
}

export const searchPatients = async (
  params: PatientSearchParams = {},
): Promise<Patient[]> => {
  const response = await api.get<Patient[]>("/patient", {
    params: {
      search: params.search,
      district: params.district,
      status: params.status,
      limit: params.limit ?? 50,
    },
  });
  return response.data;
};

export const createPatient = async (
  patientData: PatientCreateRequest,
): Promise<Patient> => {
  const response = await api.post<Patient>("/patient", patientData);
  return response.data;
};

export const getPatientProfile = async (patientId: number): Promise<PatientProfile> => {
  const response = await api.get<PatientProfile>(`/patient/${patientId}/profile`);
  return response.data;
};

export const getMyPatientProfile = async (): Promise<PatientProfile> => {
  const response = await api.get<PatientProfile>("/patient/me/profile");
  return response.data;
};
