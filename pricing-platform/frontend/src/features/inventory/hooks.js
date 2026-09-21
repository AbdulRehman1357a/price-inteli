import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  bulkUpdateInventory,
  createInventory,
  fetchInventory,
  fetchInventoryRecord,
  fetchInventorySummary,
  updateInventory,
} from "./api";

const inventoryKey = (params) => ["inventory", params];
const inventoryRecordKey = (id) => ["inventory", "detail", id];
const summaryKey = (params) => ["inventory", "summary", params];

export function useInventoryList(params) {
  return useQuery({
    queryKey: inventoryKey(params),
    queryFn: () => fetchInventory(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useInventoryRecord(inventoryId) {
  return useQuery({
    queryKey: inventoryRecordKey(inventoryId),
    queryFn: () => fetchInventoryRecord(inventoryId),
    enabled: Boolean(inventoryId),
  });
}

export function useInventorySummary(params) {
  return useQuery({
    queryKey: summaryKey(params),
    queryFn: () => fetchInventorySummary(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useCreateInventory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createInventory,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["inventory"] }),
  });
}

export function useUpdateInventory(inventoryId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload) => updateInventory(inventoryId, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["inventory"] }),
  });
}

export function useBulkUpdateInventory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: bulkUpdateInventory,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["inventory"] }),
  });
}
