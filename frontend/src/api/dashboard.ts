import api from "./client";

export interface DashboardSummary {
  patients: {
    total: number;
    active: number;
    inactive: number;
  };
  assessments: {
    total: number;
    in_progress: number;
    completed: number;
  };
  health_concerns: number;
  recommendations: number;
  reports: number;
  clinician_reviews: {
    total: number;
    pending: number;
    approved: number;
  };
}

export const getDashboardSummary =
  async (): Promise<DashboardSummary> => {
    const response = await api.get<DashboardSummary>(
      "/dashboard/summary",
    );

    return response.data;
  };