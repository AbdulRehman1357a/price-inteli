import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { createStore, deleteStore, fetchAllStores, fetchStore, fetchStores, updateStore } from "./api";

const storesKey = (params) => ["stores", params];
const storeKey = (id) => ["stores", "detail", id];

export function useAllStores() {
  return useQuery({
    queryKey: ["stores", "all"],
    queryFn: fetchAllStores,
  });
}

export function useStores(params) {
  return useQuery({
    queryKey: storesKey(params),
    queryFn: () => fetchStores(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useStore(storeId) {
  return useQuery({
    queryKey: storeKey(storeId),
    queryFn: () => fetchStore(storeId),
    enabled: Boolean(storeId),
  });
}

export function useCreateStore() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createStore,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["stores"] });
    },
  });
}

export function useUpdateStore(storeId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload) => updateStore(storeId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["stores"] });
    },
  });
}

export function useDeleteStore() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteStore,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["stores"] });
    },
  });
}
