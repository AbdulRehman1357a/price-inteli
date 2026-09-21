import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  addCompetitorProduct,
  createCompetitor,
  deleteCompetitor,
  deleteCompetitorProduct,
  fetchCompetitor,
  fetchCompetitorProducts,
  fetchCompetitors,
  fetchDashboard,
  fetchPrices,
  recordManualPrice,
  syncPrice,
  updateCompetitor,
  updateCompetitorProduct,
} from "./api";

export function useDashboard() {
  return useQuery({ queryKey: ["competitors", "dashboard"], queryFn: fetchDashboard });
}

export function useCompetitors() {
  return useQuery({ queryKey: ["competitors"], queryFn: fetchCompetitors });
}

export function useCompetitor(competitorId) {
  return useQuery({
    queryKey: ["competitors", "detail", competitorId],
    queryFn: () => fetchCompetitor(competitorId),
    enabled: Boolean(competitorId),
  });
}

export function useCreateCompetitor() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createCompetitor,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["competitors"] }),
  });
}

export function useUpdateCompetitor(competitorId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload) => updateCompetitor(competitorId, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["competitors"] }),
  });
}

export function useDeleteCompetitor() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteCompetitor,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["competitors"] }),
  });
}

export function useCompetitorProducts(competitorId) {
  return useQuery({
    queryKey: ["competitors", competitorId, "products"],
    queryFn: () => fetchCompetitorProducts(competitorId),
    enabled: Boolean(competitorId),
  });
}

export function useAddCompetitorProduct(competitorId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload) => addCompetitorProduct(competitorId, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["competitors", competitorId, "products"] }),
  });
}

function useCompetitorProductsInvalidator(competitorId) {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: ["competitors", competitorId, "products"] });
    queryClient.invalidateQueries({ queryKey: ["competitors", "dashboard"] });
  };
}

export function useUpdateCompetitorProduct(competitorId) {
  const invalidate = useCompetitorProductsInvalidator(competitorId);
  return useMutation({
    mutationFn: ({ competitorProductId, payload }) => updateCompetitorProduct(competitorProductId, payload),
    onSuccess: invalidate,
  });
}

export function useDeleteCompetitorProduct(competitorId) {
  const invalidate = useCompetitorProductsInvalidator(competitorId);
  return useMutation({
    mutationFn: deleteCompetitorProduct,
    onSuccess: invalidate,
  });
}

export function usePrices(competitorProductId) {
  return useQuery({
    queryKey: ["competitors", "prices", competitorProductId],
    queryFn: () => fetchPrices(competitorProductId),
    enabled: Boolean(competitorProductId),
  });
}

export function useRecordManualPrice(competitorId) {
  const queryClient = useQueryClient();
  const invalidate = useCompetitorProductsInvalidator(competitorId);
  return useMutation({
    mutationFn: ({ competitorProductId, payload }) => recordManualPrice(competitorProductId, payload),
    onSuccess: (_, variables) => {
      invalidate();
      queryClient.invalidateQueries({ queryKey: ["competitors", "prices", variables.competitorProductId] });
    },
  });
}

export function useSyncPrice(competitorId) {
  const queryClient = useQueryClient();
  const invalidate = useCompetitorProductsInvalidator(competitorId);
  return useMutation({
    mutationFn: syncPrice,
    onSuccess: (_, competitorProductId) => {
      invalidate();
      queryClient.invalidateQueries({ queryKey: ["competitors", "prices", competitorProductId] });
    },
  });
}
