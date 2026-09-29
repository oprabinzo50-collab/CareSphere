import api from "./client";

export type AuthRole = "administrator" | "clinician" | "patient";

export interface AuthUser {
  id: number;
  username: string;
  full_name: string;
  role: AuthRole;
  status: string;
  permissions: string[];
  patient_id: number | null;
}

export interface LoginRequest {
  username: string;
  password: string;
  login_role?: AuthRole;
}

export interface LoginResponse {
  message: string;
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export async function login(payload: LoginRequest): Promise<LoginResponse> {
  const response = await api.post<LoginResponse>("/auth/login", payload);
  return response.data;
}

export async function getMe(): Promise<AuthUser> {
  const response = await api.get<AuthUser>("/auth/me");
  return response.data;
}
