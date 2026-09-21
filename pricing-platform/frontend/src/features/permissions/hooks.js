import { useQuery } from "@tanstack/react-query";

import { fetchPermissions } from "./api";

export function usePermissions() {
  return useQuery({
    queryKey: ["permissions"],
    queryFn: fetchPermissions,
  });
}
