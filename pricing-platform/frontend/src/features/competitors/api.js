import { apiClient } from "../../api/client";

export function fetchDashboard() {
  return apiClient.get("/competitors/dashboard").then((res) => res.data.data);
}

export function fetchCompetitors() {
  return apiClient.get("/competitors").then((res) => res.data.data);
}

export function fetchCompetitor(competitorId) {
  return apiClient.get(`/competitors/${competitorId}`).then((res) => res.data.data);
}

export function createCompetitor(payload) {
  return apiClient
    .post("/competitors", { name: payload.name, website: payload.website || null, status: payload.status })
    .then((res) => res.data.data);
}

export function updateCompetitor(competitorId, payload) {
  return apiClient.put(`/competitors/${competitorId}`, payload).then((res) => res.data.data);
}

export function deleteCompetitor(competitorId) {
  return apiClient.delete(`/competitors/${competitorId}`).then((res) => res.data.data);
}

export function fetchCompetitorProducts(competitorId) {
  return apiClient.get(`/competitors/${competitorId}/products`).then((res) => res.data.data);
}

export function addCompetitorProduct(competitorId, payload) {
  return apiClient
    .post(`/competitors/${competitorId}/products`, {
      product_id: payload.productId,
      external_product_url: payload.externalProductUrl || null,
      match_confidence: payload.matchConfidence || null,
    })
    .then((res) => res.data.data);
}

export function updateCompetitorProduct(competitorProductId, payload) {
  return apiClient
    .put(`/competitors/products/${competitorProductId}`, payload)
    .then((res) => res.data.data);
}

export function deleteCompetitorProduct(competitorProductId) {
  return apiClient.delete(`/competitors/products/${competitorProductId}`).then((res) => res.data.data);
}

export function fetchPrices(competitorProductId) {
  return apiClient.get(`/competitors/products/${competitorProductId}/prices`).then((res) => res.data.data);
}

export function recordManualPrice(competitorProductId, payload) {
  return apiClient
    .post(`/competitors/products/${competitorProductId}/prices`, {
      price: payload.price,
      currency: payload.currency || "USD",
      availability: payload.availability || null,
    })
    .then((res) => res.data.data);
}

export function syncPrice(competitorProductId) {
  return apiClient
    .post(`/competitors/products/${competitorProductId}/prices/sync`)
    .then((res) => res.data.data);
}
