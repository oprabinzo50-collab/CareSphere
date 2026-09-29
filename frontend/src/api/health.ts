import api from "./client";

export interface HealthResponse {
  status: string;
  service: string;
}

export const getHealth = async (): Promise<HealthResponse> => {
  const response = await api.get<HealthResponse>("/health");
  return response.data;
};