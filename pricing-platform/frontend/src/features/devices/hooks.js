import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createAssignment,
  createDevice,
  deleteDevice,
  fetchActiveAssignment,
  fetchAssignments,
  fetchDevice,
  fetchDeviceHealth,
  fetchDevices,
  fetchModels,
  fetchSyncLogs,
  fetchVendors,
  syncDevice,
  unassignDevice,
  updateDevice,
} from "./api";

export function useVendors() {
  return useQuery({ queryKey: ["device-vendors"], queryFn: fetchVendors });
}

export function useModels(vendorId) {
  return useQuery({
    queryKey: ["device-models", vendorId],
    queryFn: () => fetchModels(vendorId),
    enabled: Boolean(vendorId),
  });
}

// Unfiltered — used where a lookup table of every model is needed (e.g.
// the Device List's "Model" column), as opposed to useModels(vendorId)'s
// vendor-dependent dropdown use in DeviceForm.
export function useAllModels() {
  return useQuery({ queryKey: ["device-models", "all"], queryFn: () => fetchModels() });
}

export function useDevices(params) {
  return useQuery({
    queryKey: ["devices", params],
    queryFn: () => fetchDevices(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useDevice(deviceId) {
  return useQuery({
    queryKey: ["devices", "detail", deviceId],
    queryFn: () => fetchDevice(deviceId),
    enabled: Boolean(deviceId),
  });
}

export function useCreateDevice() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createDevice,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["devices"] }),
  });
}

export function useUpdateDevice(deviceId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload) => updateDevice(deviceId, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["devices"] }),
  });
}

export function useDeleteDevice() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteDevice,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["devices"] }),
  });
}

export function useDeviceHealth(deviceId, options = {}) {
  return useQuery({
    queryKey: ["devices", "health", deviceId],
    queryFn: () => fetchDeviceHealth(deviceId),
    enabled: Boolean(deviceId),
    ...options,
  });
}

export function useSyncDevice(deviceId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => syncDevice(deviceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["devices"] });
      queryClient.invalidateQueries({ queryKey: ["device-sync-logs", deviceId] });
      // The React ESL simulator preview reads the public price endpoint
      // (features/outputs/hooks.js usePublicPrice) — refresh it too so a
      // resync visibly updates the simulated "screen".
      queryClient.invalidateQueries({ queryKey: ["public-price"] });
    },
  });
}

export function useActiveAssignment(deviceId) {
  return useQuery({
    queryKey: ["device-assignment", deviceId],
    queryFn: () => fetchActiveAssignment(deviceId),
    enabled: Boolean(deviceId),
  });
}

export function useAssignments(deviceId, params) {
  return useQuery({
    queryKey: ["device-assignments-history", deviceId, params],
    queryFn: () => fetchAssignments(deviceId, params),
    enabled: Boolean(deviceId),
    placeholderData: (previousData) => previousData,
  });
}

export function useSyncLogs(deviceId, params) {
  return useQuery({
    queryKey: ["device-sync-logs", deviceId, params],
    queryFn: () => fetchSyncLogs(deviceId, params),
    enabled: Boolean(deviceId),
    placeholderData: (previousData) => previousData,
  });
}

export function useCreateAssignment(deviceId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createAssignment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["device-assignment", deviceId] });
      queryClient.invalidateQueries({ queryKey: ["device-assignments-history", deviceId] });
      queryClient.invalidateQueries({ queryKey: ["devices"] });
      queryClient.invalidateQueries({ queryKey: ["device-sync-logs", deviceId] });
      queryClient.invalidateQueries({ queryKey: ["public-price"] });
    },
  });
}

export function useUnassignDevice(deviceId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: unassignDevice,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["device-assignment", deviceId] });
      queryClient.invalidateQueries({ queryKey: ["device-assignments-history", deviceId] });
      queryClient.invalidateQueries({ queryKey: ["devices"] });
    },
  });
}
