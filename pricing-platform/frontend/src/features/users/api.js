import { apiClient } from "../../api/client";

export function fetchUsers({ page = 1, pageSize = 20, search } = {}) {
  const params = { page, page_size: pageSize };
  if (search) params.search = search;

  return apiClient.get("/users", { params }).then((res) => ({
    items: res.data.data,
    meta: res.data.meta,
  }));
}

export function fetchUser(userId) {
  return apiClient.get(`/users/${userId}`).then((res) => res.data.data);
}

export function createUser(payload) {
  return apiClient
    .post("/users", {
      first_name: payload.firstName,
      last_name: payload.lastName,
      email: payload.email,
      password: payload.password,
      phone: payload.phone || null,
      role_ids: payload.roleIds,
    })
    .then((res) => res.data.data);
}

export function updateUser(userId, payload) {
  return apiClient
    .put(`/users/${userId}`, {
      first_name: payload.firstName,
      last_name: payload.lastName,
      phone: payload.phone || null,
      status: payload.status,
      role_ids: payload.roleIds,
    })
    .then((res) => res.data.data);
}

export function deleteUser(userId) {
  return apiClient.delete(`/users/${userId}`).then((res) => res.data.data);
}
