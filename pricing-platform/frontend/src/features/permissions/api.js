import { apiClient } from "../../api/client";

export function fetchPermissions() {
  return apiClient.get("/permissions").then((res) => res.data.data);
}
