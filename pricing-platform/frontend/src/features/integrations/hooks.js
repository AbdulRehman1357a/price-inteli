import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createIntegration,
  deleteIntegration,
  discoverDevices,
  fetchIntegration,
  fetchIntegrations,
  fetchSyncStatus,
  importDevices,
  testConnection,
  testPriceUpdate,
  updateIntegration,
} from "./api";

export function useIntegrations(params) {
  return useQuery({
    queryKey: ["esl-integrations", params],
    queryFn: () => fetchIntegrations(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useIntegration(integrationId) {
  return useQuery({
    queryKey: ["esl-integrations", "detail", integrationId],
    queryFn: () => fetchIntegration(integrationId),
    enabled: Boolean(integrationId),
  });
}

export function useCreateIntegration() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createIntegration,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["esl-integrations"] }),
  });
}

export function useUpdateIntegration(integrationId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload) => updateIntegration(integrationId, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["esl-integrations"] }),
  });
}

export function useDeleteIntegration() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteIntegration,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["esl-integrations"] }),
  });
}

export function useTestConnection(integrationId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => testConnection(integrationId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["esl-integrations"] }),
  });
}

export function useDiscoverDevices(integrationId) {
  return useMutation({ mutationFn: () => discoverDevices(integrationId) });
}

export function useImportDevices(integrationId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (args) => importDevices(integrationId, args),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["devices"] }),
  });
}

export function useTestPriceUpdate(integrationId) {
  return useMutation({ mutationFn: (args) => testPriceUpdate(integrationId, args) });
}

export function useSyncStatus(integrationId, options = {}) {
  return useQuery({
    queryKey: ["esl-integrations", "sync-status", integrationId],
    queryFn: () => fetchSyncStatus(integrationId),
    enabled: Boolean(integrationId),
    ...options,
  });
}
