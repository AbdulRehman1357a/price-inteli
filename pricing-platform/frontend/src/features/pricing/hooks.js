import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { createRule, fetchRule, fetchRules, runSimulation, testRule, updateRule } from "./api";

export function useRules(params) {
  return useQuery({
    queryKey: ["pricing-rules", params],
    queryFn: () => fetchRules(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useRule(ruleId) {
  return useQuery({
    queryKey: ["pricing-rules", "detail", ruleId],
    queryFn: () => fetchRule(ruleId),
    enabled: Boolean(ruleId),
  });
}

export function useCreateRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createRule,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["pricing-rules"] }),
  });
}

export function useUpdateRule(ruleId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload) => updateRule(ruleId, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["pricing-rules"] }),
  });
}

export function useTestRule(ruleId) {
  return useMutation({
    mutationFn: (args) => testRule(ruleId, args),
  });
}

export function useRunSimulation() {
  return useMutation({
    mutationFn: runSimulation,
  });
}
