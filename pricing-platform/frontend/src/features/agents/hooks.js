import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createAgent,
  deleteAgent,
  fetchAgent,
  fetchAgents,
  fetchPolicies,
  fetchRun,
  fetchRuns,
  runAgent,
  updateAgent,
  updatePolicy,
} from "./api";

export function useAgents() {
  return useQuery({ queryKey: ["ai-agents"], queryFn: fetchAgents });
}

export function useAgent(agentId) {
  return useQuery({
    queryKey: ["ai-agents", "detail", agentId],
    queryFn: () => fetchAgent(agentId),
    enabled: Boolean(agentId),
  });
}

export function useCreateAgent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createAgent,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["ai-agents"] }),
  });
}

export function useUpdateAgent(agentId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload) => updateAgent(agentId, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["ai-agents"] }),
  });
}

export function useDeleteAgent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteAgent,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["ai-agents"] }),
  });
}

export function useRunAgent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: runAgent,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["ai-agent-runs"] }),
  });
}

export function useRuns(params) {
  return useQuery({
    queryKey: ["ai-agent-runs", params],
    queryFn: () => fetchRuns(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useRun(runId, { poll = false } = {}) {
  return useQuery({
    queryKey: ["ai-agent-runs", "detail", runId],
    queryFn: () => fetchRun(runId),
    enabled: Boolean(runId),
    refetchInterval: poll ? 2000 : false,
  });
}

export function usePolicies() {
  return useQuery({ queryKey: ["ai-policies"], queryFn: fetchPolicies });
}

export function useUpdatePolicy() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ agentType, payload }) => updatePolicy(agentType, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["ai-policies"] }),
  });
}
