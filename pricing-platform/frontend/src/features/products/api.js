import { apiClient } from "../../api/client";

export function fetchProducts({ page = 1, pageSize = 20, search, categoryId, status, sort } = {}) {
  const params = { page, page_size: pageSize };
  if (search) params.search = search;
  if (categoryId) params.category_id = categoryId;
  if (status) params.status = status;
  if (sort) params.sort = sort;

  return apiClient.get("/products", { params }).then((res) => ({
    items: res.data.data,
    meta: res.data.meta,
  }));
}

export function fetchProduct(productId) {
  return apiClient.get(`/products/${productId}`).then((res) => res.data.data);
}

export function createProduct(payload) {
  return apiClient.post("/products", toApiPayload(payload)).then((res) => res.data.data);
}

export function updateProduct(productId, payload) {
  return apiClient.put(`/products/${productId}`, toApiPayload(payload)).then((res) => res.data.data);
}

export function deleteProduct(productId) {
  return apiClient.delete(`/products/${productId}`).then((res) => res.data.data);
}

export function fetchProductFromUrl(url) {
  return apiClient.post("/products/fetch-from-url", { url }).then((res) => res.data.data);
}

// Form values use empty strings for untouched optional fields; the API
// expects those to simply be absent (null) rather than "".
function toApiPayload(values) {
  const payload = { ...values };
  for (const key of Object.keys(payload)) {
    if (payload[key] === "") {
      payload[key] = null;
    }
  }
  return payload;
}
