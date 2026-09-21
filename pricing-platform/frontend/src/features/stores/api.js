import { apiClient } from "../../api/client";

// Tenants have a small number of stores, so the store selector just fetches
// "all of them" in one page rather than needing search-as-you-type.
// page_size is capped at 100 server-side (PaginationParams) — 500 here
// used to fail every request with a 422, silently emptying every Store
// dropdown in the app. Only active stores are offered: assigning a device,
// output, inventory adjustment, or import to an inactive/closed store isn't
// a valid choice.
const ALL_PAGE_SIZE = 100;

export function fetchAllStores() {
  return apiClient
    .get("/stores", { params: { page: 1, page_size: ALL_PAGE_SIZE, status: "active" } })
    .then((res) => res.data.data);
}

export function fetchStores({ page = 1, pageSize = 20, search, status, storeType } = {}) {
  const params = { page, page_size: pageSize };
  if (search) params.search = search;
  if (status) params.status = status;
  if (storeType) params.store_type = storeType;

  return apiClient.get("/stores", { params }).then((res) => ({
    items: res.data.data,
    meta: res.data.meta,
  }));
}

export function fetchStore(storeId) {
  return apiClient.get(`/stores/${storeId}`).then((res) => res.data.data);
}

export function createStore(payload) {
  return apiClient.post("/stores", toApiPayload(payload)).then((res) => res.data.data);
}

export function updateStore(storeId, payload) {
  return apiClient.put(`/stores/${storeId}`, toApiPayload(payload)).then((res) => res.data.data);
}

export function deleteStore(storeId) {
  return apiClient.delete(`/stores/${storeId}`).then((res) => res.data.data);
}

// Form values use empty strings for untouched optional fields; the API
// expects those to simply be absent (or null for opening_date) rather than "".
function toApiPayload(values) {
  const payload = { ...values };
  for (const key of Object.keys(payload)) {
    if (payload[key] === "") {
      payload[key] = null;
    }
  }
  return payload;
}
