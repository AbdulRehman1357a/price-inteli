import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  cancelJob,
  createBulkJobs,
  createChannel,
  createJob,
  createLabelTemplate,
  createRoutingRule,
  deleteLabelTemplate,
  fetchChannel,
  fetchChannels,
  fetchJob,
  fetchJobs,
  fetchJobsSummary,
  fetchLabelTemplates,
  fetchPublicPrice,
  fetchRoutingRule,
  fetchRoutingRules,
  retryJob,
  updateChannel,
  updateLabelTemplate,
  updateRoutingRule,
  uploadTemplateBackgroundImage,
} from "./api";

export function useChannels(params) {
  return useQuery({
    queryKey: ["output-channels", params],
    queryFn: () => fetchChannels(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useChannel(channelId) {
  return useQuery({
    queryKey: ["output-channels", "detail", channelId],
    queryFn: () => fetchChannel(channelId),
    enabled: Boolean(channelId),
  });
}

export function useCreateChannel() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createChannel,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["output-channels"] }),
  });
}

export function useUpdateChannel(channelId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload) => updateChannel(channelId, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["output-channels"] }),
  });
}

export function useJobs(params) {
  return useQuery({
    queryKey: ["output-jobs", params],
    queryFn: () => fetchJobs(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useJob(jobId, options = {}) {
  return useQuery({
    queryKey: ["output-jobs", "detail", jobId],
    queryFn: () => fetchJob(jobId),
    enabled: Boolean(jobId),
    ...options,
  });
}

export function useCreateJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createJob,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["output-jobs"] }),
  });
}

export function useCreateBulkJobs() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createBulkJobs,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["output-jobs"] }),
  });
}

export function useRetryJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: retryJob,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["output-jobs"] }),
  });
}

export function useCancelJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: cancelJob,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["output-jobs"] }),
  });
}

export function useJobsSummary() {
  return useQuery({
    queryKey: ["output-jobs", "summary"],
    queryFn: fetchJobsSummary,
  });
}

export function usePublicPrice(productId, storeId) {
  return useQuery({
    queryKey: ["public-price", productId, storeId],
    queryFn: () => fetchPublicPrice(productId, storeId),
    enabled: Boolean(productId),
    retry: false,
  });
}

export function useRoutingRules(params) {
  return useQuery({
    queryKey: ["output-routing-rules", params],
    queryFn: () => fetchRoutingRules(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useRoutingRule(ruleId) {
  return useQuery({
    queryKey: ["output-routing-rules", "detail", ruleId],
    queryFn: () => fetchRoutingRule(ruleId),
    enabled: Boolean(ruleId),
  });
}

export function useCreateRoutingRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createRoutingRule,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["output-routing-rules"] }),
  });
}

export function useUpdateRoutingRule(ruleId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload) => updateRoutingRule(ruleId, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["output-routing-rules"] }),
  });
}

// ── Label Templates ───────────────────────────────────────────

export function useLabelTemplates() {
  return useQuery({
    queryKey: ["label-templates"],
    queryFn: fetchLabelTemplates,
  });
}

export function useCreateLabelTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createLabelTemplate,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["label-templates"] }),
  });
}

export function useUpdateLabelTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...payload }) => updateLabelTemplate(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["label-templates"] }),
  });
}

export function useDeleteLabelTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteLabelTemplate,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["label-templates"] }),
  });
}

export function useUploadTemplateBackgroundImage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ templateId, file }) => uploadTemplateBackgroundImage(templateId, file),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["label-templates"] }),
  });
}
