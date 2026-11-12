import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry && localStorage.getItem("refresh")) {
      original._retry = true;
      try {
        const refresh = localStorage.getItem("refresh");
        const { data } = await axios.post(
          `${import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api"}/auth/refresh/`,
          { refresh },
        );
        localStorage.setItem("access", data.access);
        original.headers.Authorization = `Bearer ${data.access}`;
        return api(original);
      } catch {
        localStorage.removeItem("access");
        localStorage.removeItem("refresh");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  },
);

export function apiMessage(error: unknown, fallback = "Request failed"): string {
  const err = error as { response?: { data?: { message?: string; detail?: string } } };
  return err.response?.data?.message || err.response?.data?.detail || fallback;
}

export default api;
