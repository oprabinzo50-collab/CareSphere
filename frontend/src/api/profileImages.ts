import api from "./client";

export async function uploadPatientProfilePicture(
  patientId: number,
  file: File,
): Promise<void> {
  await api.put(`/patient/${patientId}/profile-picture?ts=${Date.now()}`, file, {
    headers: {
      "Content-Type": file.type,
    },
  });
}

export async function uploadMyProfilePicture(file: File): Promise<void> {
  await api.put("/patient/me/profile-picture", file, {
    headers: {
      "Content-Type": file.type,
    },
  });
}

export async function deletePatientProfilePicture(
  patientId: number,
): Promise<void> {
  await api.delete(`/patient/${patientId}/profile-picture`);
}

export async function fetchPatientProfilePicture(
  patientId: number,
): Promise<string | null> {
  try {
    const response = await api.get(`/patient/${patientId}/profile-picture`, {
      responseType: "blob",
    });
    return URL.createObjectURL(response.data);
  } catch (error: any) {
    if (error?.response?.status === 404) {
      return null;
    }
    throw error;
  }
}
