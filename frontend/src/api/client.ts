import axios from "axios";

const apiBaseUrl =
  import.meta.env.VITE_API_BASE_URL?.trim();

if (!apiBaseUrl && import.meta.env.PROD) {
  throw new Error(
    "VITE_API_BASE_URL is missing from the production build."
  );
}

const api = axios.create({
  baseURL: apiBaseUrl || "http://127.0.0.1:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem("caresphere_token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

export default api;