import api from "./client";
import type { Patient } from "./patients";

export interface FollowUpItem {
  follow_up_type: string;
  priority: string;
  assessment_id: number | null;
  record_id: number | null;
  title: string;
  description: string;
  action: string;
  status?: string;
  started_at?: string | null;
  completed_at?: string | null;
}

export interface PatientFollowUpResponse {
  patient_id: number;
  patient: Pick<Patient, "patient_number" | "first_name" | "last_name" | "status">;
  assessment_count: number;
  latest_assessment: {
    id: number;
    assessment_type: string;
    status: string;
    started_at: string | null;
    completed_at: string | null;
  } | null;
  follow_up_status: string;
  follow_up_count: number;
  counts: {
    incomplete_assessments: number;
    pending_recommendations: number;
    pending_reports: number;
    pending_reviews: number;
    completed_without_follow_up: number;
  };
  items: FollowUpItem[];
}

export interface CareGap {
  gap_type: string;
  severity: string;
  title: string;
  description: string;
  assessment_id: number | null;
  record_id?: number | null;
  action: string;
}

export interface PatientCareGapsResponse {
  patient_id: number;
  patient: Pick<Patient, "patient_number" | "first_name" | "last_name" | "status">;
  assessment_count: number;
  gap_count: number;
  severity_counts: {
    high: number;
    medium: number;
    low: number;
  };
  status: string;
  gaps: CareGap[];
}

export interface NotificationRecord {
  id: number;
  patient_id: number;
  assessment_id: number | null;
  record_id: number | null;
  notification_type: string;
  priority: string;
  title: string;
  message: string;
  source: string;
  is_read: boolean;
  created_at: string | null;
  read_at: string | null;
}

export interface PatientNotificationsResponse {
  patient_id: number;
  total_count: number;
  unread_count: number;
  limit: number;
  offset: number;
  returned_count: number;
  notifications: NotificationRecord[];
}

export interface AuditLogRecord {
  id: number;
  user_id: number | null;
  action: string;
  entity_type: string | null;
  entity_id: number | null;
  description: string | null;
  ip_address: string | null;
  user_agent: string | null;
  log_metadata: Record<string, unknown> | null;
  created_at: string;
}

export async function getPatientFollowUp(patientId: number): Promise<PatientFollowUpResponse> {
  const response = await api.get<PatientFollowUpResponse>(`/patients/${patientId}/follow-up`);
  return response.data;
}

export async function getPatientCareGaps(patientId: number): Promise<PatientCareGapsResponse> {
  const response = await api.get<PatientCareGapsResponse>(`/patients/${patientId}/care-gaps`);
  return response.data;
}

export async function synchronizePatientNotifications(patientId: number) {
  const response = await api.post(`/patients/${patientId}/notifications/synchronize`);
  return response.data;
}

export async function getPatientNotifications(
  patientId: number,
  params: { unreadOnly?: boolean; limit?: number; offset?: number } = {},
): Promise<PatientNotificationsResponse> {
  const response = await api.get<PatientNotificationsResponse>(
    `/patients/${patientId}/notifications/persistent`,
    {
      params: {
        unread_only: params.unreadOnly,
        limit: params.limit ?? 50,
        offset: params.offset ?? 0,
      },
    },
  );
  return response.data;
}

export async function markNotificationRead(notificationId: number) {
  const response = await api.put(`/patients/notifications/${notificationId}/read`);
  return response.data;
}

export async function markAllPatientNotificationsRead(patientId: number) {
  const response = await api.put(`/patients/${patientId}/notifications/read-all`);
  return response.data;
}

export async function listAuditLogs(params: {
  userId?: number;
  action?: string;
  entityType?: string;
  limit?: number;
} = {}): Promise<AuditLogRecord[]> {
  const response = await api.get<AuditLogRecord[]>("/audit-logs", {
    params: {
      user_id: params.userId,
      action: params.action || undefined,
      entity_type: params.entityType || undefined,
      limit: params.limit ?? 100,
    },
  });
  return response.data;
}
