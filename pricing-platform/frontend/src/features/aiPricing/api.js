import { apiClient } from "../../api/client";

export function fetchRecommendations({ page = 1, pageSize = 20, status, productId, storeId } = {}) {
  const params = { page, page_size: pageSize };
  if (status) params.status = status;
  if (productId) params.product_id = productId;
  if (storeId) params.store_id = storeId;

  return apiClient.get("/ai-recommendations", { params }).then((res) => ({
    items: res.data.data,
    meta: res.data.meta,
  }));
}

export function fetchRecommendation(recommendationId) {
  return apiClient.get(`/ai-recommendations/${recommendationId}`).then((res) => res.data.data);
}

export function fetchSummary() {
  return apiClient.get("/ai-recommendations/summary").then((res) => res.data.data);
}

export function generateRecommendation({ productId, storeId, provider }) {
  return apiClient
    .post("/ai-recommendations/generate", {
      product_id: productId,
      store_id: storeId || undefined,
      provider: provider || undefined,
    })
    .then((res) => res.data.data);
}

export function approveRecommendation(recommendationId) {
  return apiClient.post(`/ai-recommendations/${recommendationId}/approve`).then((res) => res.data.data);
}

export function rejectRecommendation(recommendationId) {
  return apiClient.post(`/ai-recommendations/${recommendationId}/reject`).then((res) => res.data.data);
}

export function modifyRecommendation(recommendationId, recommendedPrice) {
  return apiClient
    .put(`/ai-recommendations/${recommendationId}/modify`, { recommended_price: recommendedPrice })
    .then((res) => res.data.data);
}

export function applyRecommendation(recommendationId) {
  return apiClient.post(`/ai-recommendations/${recommendationId}/apply`).then((res) => res.data.data);
}
