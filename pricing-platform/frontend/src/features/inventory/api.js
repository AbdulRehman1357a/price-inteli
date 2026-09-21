import { apiClient } from "../../api/client";

export function fetchInventory({
  page = 1,
  pageSize = 20,
  storeId,
  categoryId,
  productId,
  lowStock,
  outOfStock,
} = {}) {
  const params = { page, page_size: pageSize };
  if (storeId) params.store_id = storeId;
  if (categoryId) params.category_id = categoryId;
  if (productId) params.product_id = productId;
  if (lowStock) params.low_stock = true;
  if (outOfStock) params.out_of_stock = true;

  return apiClient.get("/inventory", { params }).then((res) => ({
    items: res.data.data,
    meta: res.data.meta,
  }));
}

export function fetchInventoryRecord(inventoryId) {
  return apiClient.get(`/inventory/${inventoryId}`).then((res) => res.data.data);
}

export function fetchInventorySummary({ storeId, categoryId, productId } = {}) {
  const params = {};
  if (storeId) params.store_id = storeId;
  if (categoryId) params.category_id = categoryId;
  if (productId) params.product_id = productId;

  return apiClient.get("/inventory/summary", { params }).then((res) => res.data.data);
}

export function createInventory(payload) {
  return apiClient.post("/inventory", toApiPayload(payload)).then((res) => res.data.data);
}

export function updateInventory(inventoryId, payload) {
  return apiClient
    .put(`/inventory/${inventoryId}`, toApiPayload(payload))
    .then((res) => res.data.data);
}

export function bulkUpdateInventory(items) {
  return apiClient
    .post("/inventory/bulk-update", { items: items.map(toApiPayload) })
    .then((res) => res.data.data);
}

function toApiPayload(values) {
  const payload = { ...values };
  for (const key of Object.keys(payload)) {
    if (payload[key] === "") {
      payload[key] = null;
    }
  }
  return payload;
}
