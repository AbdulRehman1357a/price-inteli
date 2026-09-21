import { apiClient } from "../../api/client";

export function registerOrganization(payload) {
  return apiClient
    .post("/auth/register", {
      organization_name: payload.organizationName,
      first_name: payload.firstName,
      last_name: payload.lastName,
      email: payload.email,
      password: payload.password,
      confirm_password: payload.confirmPassword,
      country: payload.country || null,
      timezone: payload.timezone,
      currency: payload.currency,
    })
    .then((res) => res.data.data);
}

export function login({ email, password, rememberMe }) {
  return apiClient
    .post("/auth/login", { email, password, remember_me: Boolean(rememberMe) })
    .then((res) => res.data.data);
}

export function refreshAccessToken(refreshToken) {
  return apiClient.post("/auth/refresh", { refresh_token: refreshToken }).then((res) => res.data.data);
}

export function fetchCurrentUser() {
  return apiClient.get("/auth/me").then((res) => res.data.data);
}

export function updateProfile({ firstName, lastName, phone }) {
  return apiClient
    .put("/auth/me", { first_name: firstName, last_name: lastName, phone: phone || null })
    .then((res) => res.data.data);
}

export function logoutRequest() {
  return apiClient.post("/auth/logout").then((res) => res.data.data);
}
