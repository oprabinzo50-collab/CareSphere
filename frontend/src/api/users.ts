import api from "./client";

export type UserRole = "administrator" | "clinician" | "patient";
export type UserStatus = "active" | "inactive" | "suspended";

export interface CareUser {
  id: number;
  username: string;
  full_name: string;
  role: UserRole;
  status: UserStatus;
  created_at: string;
  updated_at: string;
  last_login_at: string | null;
  patient_id: number | null;
}

export interface UserCreateRequest {
  username: string;
  password: string;
  full_name: string;
  role: UserRole;
  patient_id?: number | null;
}

export interface UserUpdateRequest {
  username?: string;
  full_name?: string;
  role?: UserRole;
  password?: string;
  patient_id?: number | null;
}

export const listUsers = async (params: {
  role?: UserRole;
  status?: UserStatus;
  search?: string;
  limit?: number;
} = {}): Promise<CareUser[]> => {
  const response = await api.get<CareUser[]>("/users", {
    params: {
      role: params.role,
      status: params.status,
      search: params.search,
      limit: params.limit ?? 100,
    },
  });
  return response.data;
};

export const createUser = async (
  data: UserCreateRequest,
): Promise<CareUser> => {
  const response = await api.post<CareUser>("/users", data);
  return response.data;
};

export const updateUser = async (
  userId: number,
  data: UserUpdateRequest,
): Promise<CareUser> => {
  const response = await api.put<CareUser>(`/users/${userId}`, data);
  return response.data;
};

export const updateUserStatus = async (
  userId: number,
  status: UserStatus,
): Promise<CareUser> => {
  const response = await api.put<CareUser>(`/users/${userId}/status`, { status });
  return response.data;
};
