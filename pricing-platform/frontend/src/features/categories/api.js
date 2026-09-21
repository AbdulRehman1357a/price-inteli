import { apiClient } from "../../api/client";

// Tenants have a small number of categories, so the tree-building UI (the
// hierarchical selector, the list filter) just fetches "all of them" in one
// page rather than needing a dedicated /categories/tree endpoint.
const ALL_PAGE_SIZE = 500;

export function fetchAllCategories() {
  return apiClient
    .get("/categories", { params: { page: 1, page_size: ALL_PAGE_SIZE } })
    .then((res) => res.data.data);
}

export function fetchCategories({ page = 1, pageSize = 20, search, status, sort } = {}) {
  const params = { page, page_size: pageSize };
  if (search) params.search = search;
  if (status) params.status = status;
  if (sort) params.sort = sort;

  return apiClient.get("/categories", { params }).then((res) => ({
    items: res.data.data,
    meta: res.data.meta,
  }));
}

export function fetchCategory(categoryId) {
  return apiClient.get(`/categories/${categoryId}`).then((res) => res.data.data);
}

export function createCategory(payload) {
  return apiClient.post("/categories", toApiPayload(payload)).then((res) => res.data.data);
}

export function updateCategory(categoryId, payload) {
  return apiClient.put(`/categories/${categoryId}`, toApiPayload(payload)).then((res) => res.data.data);
}

export function deleteCategory(categoryId) {
  return apiClient.delete(`/categories/${categoryId}`).then((res) => res.data.data);
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
