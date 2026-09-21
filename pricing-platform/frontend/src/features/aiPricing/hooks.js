import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  applyRecommendation,
  approveRecommendation,
  fetchRecommendation,
  fetchRecommendations,
  fetchSummary,
  generateRecommendation,
  modifyRecommendation,
  rejectRecommendation,
} from "./api";

const recommendationsKey = (params) => ["ai-recommendations", params];
const recommendationKey = (id) => ["ai-recommendations", "detail", id];

export function useRecommendations(params) {
  return useQuery({
    queryKey: recommendationsKey(params),
    queryFn: () => fetchRecommendations(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useRecommendation(recommendationId) {
  return useQuery({
    queryKey: recommendationKey(recommendationId),
    queryFn: () => fetchRecommendation(recommendationId),
    enabled: Boolean(recommendationId),
  });
}

export function useSummary() {
  return useQuery({
    queryKey: ["ai-recommendations", "summary"],
    queryFn: fetchSummary,
  });
}

export function useGenerateRecommendation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: generateRecommendation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ai-recommendations"] });
    },
  });
}

function useRecommendationAction(mutationFn) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ai-recommendations"] });
    },
  });
}

export function useApproveRecommendation() {
  return useRecommendationAction(approveRecommendation);
}

export function useRejectRecommendation() {
  return useRecommendationAction(rejectRecommendation);
}

export function useApplyRecommendation() {
  return useRecommendationAction(applyRecommendation);
}

export function useModifyRecommendation() {
  return useRecommendationAction(({ recommendationId, recommendedPrice }) =>
    modifyRecommendation(recommendationId, recommendedPrice)
  );
}
