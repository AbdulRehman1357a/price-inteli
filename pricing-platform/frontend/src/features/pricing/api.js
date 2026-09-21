import { apiClient } from "../../api/client";

export function fetchRules({ page = 1, pageSize = 20, ruleType, status } = {}) {
  const params = { page, page_size: pageSize };
  if (ruleType) params.rule_type = ruleType;
  if (status) params.status = status;

  return apiClient.get("/pricing/rules", { params }).then((res) => ({
    items: res.data.data,
    meta: res.data.meta,
  }));
}

export function fetchRule(ruleId) {
  return apiClient.get(`/pricing/rules/${ruleId}`).then((res) => res.data.data);
}

export function createRule(payload) {
  return apiClient.post("/pricing/rules", payload).then((res) => res.data.data);
}

export function updateRule(ruleId, payload) {
  return apiClient.put(`/pricing/rules/${ruleId}`, payload).then((res) => res.data.data);
}

export function testRule(ruleId, { productId, storeId }) {
  return apiClient
    .post(`/pricing/rules/${ruleId}/test`, { product_id: productId, store_id: storeId || undefined })
    .then((res) => res.data.data);
}

export function runSimulation({
  productId,
  storeId,
  currentPrice,
  proposedPrice,
  expectedDemandChangePercent,
  cost,
  inventoryQuantity,
}) {
  return apiClient
    .post("/pricing/simulations", {
      product_id: productId,
      store_id: storeId || undefined,
      current_price: currentPrice || undefined,
      proposed_price: proposedPrice,
      expected_demand_change_percent: expectedDemandChangePercent || undefined,
      cost: cost || undefined,
      inventory_quantity: inventoryQuantity || undefined,
    })
    .then((res) => res.data.data);
}
