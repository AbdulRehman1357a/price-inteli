import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createAuthority,
  createIntegration,
  createMapping,
  createSchedule,
  deleteAuthority,
  deleteMapping,
  discoverLocations,
  fetchAuthorities,
  fetchErrors,
  fetchHealth,
  fetchIntegration,
  fetchIntegrations,
  fetchLocations,
  fetchMappings,
  fetchReconciliation,
  fetchSchedules,
  fetchSyncJobs,
  fetchWebhookEvents,
  pushPrices,
  resolveError,
  resolveReconciliation,
  retrySyncJob,
  rotateWebhookSecret,
  runReconciliation,
  startSync,
  testConnection,
  updateIntegration,
  updateLocation,
  updateSchedule,
} from "./api";

export function useIntegrations(params) {
  return useQuery({
    queryKey: ["integration-hub", params],
    queryFn: () => fetchIntegrations(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useIntegration(integrationId) {
  return useQuery({
    queryKey: ["integration-hub", "detail", integrationId],
    queryFn: () => fetchIntegration(integrationId),
    enabled: Boolean(integrationId),
  });
}

export function useCreateIntegration() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createIntegration,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["integration-hub"] }),
  });
}

export function useUpdateIntegration(integrationId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload) => updateIntegration(integrationId, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["integration-hub"] }),
  });
}

export function useTestConnection(integrationId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => testConnection(integrationId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["integration-hub"] }),
  });
}

export function useStartSync(integrationId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (args) => startSync(integrationId, args),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["integration-hub-jobs", integrationId] }),
  });
}

export function useSyncJobs(integrationId, params) {
  return useQuery({
    queryKey: ["integration-hub-jobs", integrationId, params],
    queryFn: () => fetchSyncJobs(integrationId, params),
    enabled: Boolean(integrationId),
    placeholderData: (previousData) => previousData,
  });
}

export function useRetrySyncJob(integrationId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (jobId) => retrySyncJob(integrationId, jobId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["integration-hub-jobs", integrationId] }),
  });
}

export function useMappings(integrationId) {
  return useQuery({
    queryKey: ["integration-hub-mappings", integrationId],
    queryFn: () => fetchMappings(integrationId),
    enabled: Boolean(integrationId),
  });
}

export function useCreateMapping(integrationId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload) => createMapping(integrationId, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["integration-hub-mappings", integrationId] }),
  });
}

export function useDeleteMapping(integrationId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (mappingId) => deleteMapping(integrationId, mappingId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["integration-hub-mappings", integrationId] }),
  });
}

// --- Phase 10 upgrade ---

export function useLocations(integrationId) {
  return useQuery({
    queryKey: ["integration-hub-locations", integrationId],
    queryFn: () => fetchLocations(integrationId),
    enabled: Boolean(integrationId),
  });
}

export function useDiscoverLocations(integrationId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => discoverLocations(integrationId),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["integration-hub-locations", integrationId] }),
  });
}

export function useUpdateLocation(integrationId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ locationId, payload }) => updateLocation(integrationId, locationId, payload),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["integration-hub-locations", integrationId] }),
  });
}

export function useAuthorities(integrationId) {
  return useQuery({
    queryKey: ["integration-hub-authorities", integrationId],
    queryFn: () => fetchAuthorities(integrationId),
    enabled: Boolean(integrationId),
  });
}

export function useCreateAuthority(integrationId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload) => createAuthority(integrationId, payload),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["integration-hub-authorities", integrationId] }),
  });
}

export function useDeleteAuthority(integrationId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (authorityId) => deleteAuthority(integrationId, authorityId),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["integration-hub-authorities", integrationId] }),
  });
}

export function useSchedules(integrationId) {
  return useQuery({
    queryKey: ["integration-hub-schedules", integrationId],
    queryFn: () => fetchSchedules(integrationId),
    enabled: Boolean(integrationId),
  });
}

export function useCreateSchedule(integrationId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload) => createSchedule(integrationId, payload),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["integration-hub-schedules", integrationId] }),
  });
}

export function useUpdateSchedule(integrationId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ scheduleId, payload }) => updateSchedule(integrationId, scheduleId, payload),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["integration-hub-schedules", integrationId] }),
  });
}

export function useWebhookEvents(integrationId, params) {
  return useQuery({
    queryKey: ["integration-hub-webhook-events", integrationId, params],
    queryFn: () => fetchWebhookEvents(integrationId, params),
    enabled: Boolean(integrationId),
    placeholderData: (previousData) => previousData,
  });
}

export function useRotateWebhookSecret(integrationId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => rotateWebhookSecret(integrationId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["integration-hub", "detail", integrationId] }),
  });
}

export function useErrors(integrationId, params) {
  return useQuery({
    queryKey: ["integration-hub-errors", integrationId, params],
    queryFn: () => fetchErrors(integrationId, params),
    enabled: Boolean(integrationId),
    placeholderData: (previousData) => previousData,
  });
}

export function useResolveError(integrationId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (errorId) => resolveError(integrationId, errorId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["integration-hub-errors", integrationId] }),
  });
}

export function useReconciliation(integrationId, params) {
  return useQuery({
    queryKey: ["integration-hub-reconciliation", integrationId, params],
    queryFn: () => fetchReconciliation(integrationId, params),
    enabled: Boolean(integrationId),
    placeholderData: (previousData) => previousData,
  });
}

export function useRunReconciliation(integrationId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (entityType) => runReconciliation(integrationId, entityType),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["integration-hub-reconciliation", integrationId] }),
  });
}

export function useResolveReconciliation(integrationId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ reconciliationId, resolution }) =>
      resolveReconciliation(integrationId, reconciliationId, resolution),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["integration-hub-reconciliation", integrationId] }),
  });
}

export function usePushIntegration(integrationId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (priceIds) => pushPrices(integrationId, priceIds),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["integration-hub-jobs", integrationId] }),
  });
}

export function useIntegrationHealth(integrationId) {
  return useQuery({
    queryKey: ["integration-hub-health", integrationId],
    queryFn: () => fetchHealth(integrationId),
    enabled: Boolean(integrationId),
    refetchInterval: 30_000,
  });
}
