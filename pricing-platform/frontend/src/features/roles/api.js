import { apiClient } from "../../api/client";

export function fetchRoles() {
  return apiClient.get("/roles").then((res) => res.data.data);
}

// Editing a role that's still the shared default (is_system_role: true)
// forks it into an organization-scoped copy on the backend — the response
// carries a new role id, which is why callers should treat this as
// "replace the role in the list" rather than "patch it in place".
export function updateRolePermissions(roleId, permissionIds) {
  return apiClient
    .put(`/roles/${roleId}/permissions`, { permission_ids: permissionIds })
    .then((res) => res.data.data);
}
