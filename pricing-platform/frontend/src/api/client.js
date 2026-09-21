import axios from "axios";

import { env } from "../config/env";
import { clearTokens, getAccessToken, getRefreshToken, setAccessToken } from "../features/auth/tokenStorage";

export const apiClient = axios.create({
  baseURL: env.apiUrl,
  headers: { "Content-Type": "application/json" },
});

// Attach the access token to every request that has one.
apiClient.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Requests that must never trigger a refresh-and-retry (a 401 from these is
// a real auth failure, not an expired access token).
const AUTH_EXEMPT_PATHS = ["/auth/login", "/auth/register", "/auth/refresh"];

let onAuthExpired = null;
// Registered by AuthContext so a failed refresh can clear app state without
// this module depending on React.
export function setOnAuthExpired(handler) {
  onAuthExpired = handler;
}

let refreshPromise = null;

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { config, response } = error;
    const isExempt = !config || AUTH_EXEMPT_PATHS.some((path) => config.url?.includes(path));

    if (response?.status !== 401 || isExempt || config._retry) {
      return Promise.reject(error);
    }

    const refreshToken = getRefreshToken();
    if (!refreshToken) {
      clearTokens();
      onAuthExpired?.();
      return Promise.reject(error);
    }

    config._retry = true;
    try {
      refreshPromise ??= apiClient
        .post("/auth/refresh", { refresh_token: refreshToken })
        .finally(() => {
          refreshPromise = null;
        });
      const { data } = await refreshPromise;
      const newAccessToken = data.data.access_token;
      setAccessToken(newAccessToken);
      config.headers.Authorization = `Bearer ${newAccessToken}`;
      return apiClient(config);
    } catch (refreshError) {
      clearTokens();
      onAuthExpired?.();
      return Promise.reject(refreshError);
    }
  }
);
