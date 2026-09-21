import { useQuery } from "@tanstack/react-query";

import { fetchDashboardMetrics } from "./api";

export function useDashboardMetrics(filters = {}, options = {}) {
  return useQuery({
    queryKey: ["analytics", "dashboard", filters],
    queryFn: () => fetchDashboardMetrics(filters),
    placeholderData: (previousData) => previousData,
    ...options,
  });
}
