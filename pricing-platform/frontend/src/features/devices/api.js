import { apiClient } from "../../api/client";

export function fetchVendors() {
  return apiClient.get("/devices/vendors").then((res) => res.data.data);
}

export function fetchModels(vendorId) {
  const params = vendorId ? { vendor_id: vendorId } : undefined;
  return apiClient.get("/devices/models", { params }).then((res) => res.data.data);
}

export function fetchDevices({
  page = 1,
  pageSize = 20,
  storeId,
  vendorId,
  eslIntegrationId,
  deviceModelId,
  status,
  search,
} = {}) {
  const params = { page, page_size: pageSize };
  if (storeId) params.store_id = storeId;
  if (vendorId) params.vendor_id = vendorId;
  if (eslIntegrationId) params.esl_integration_id = eslIntegrationId;
  if (deviceModelId) params.device_model_id = deviceModelId;
  if (status) params.status = status;
  if (search) params.search = search;

  return apiClient.get("/devices", { params }).then((res) => ({
    items: res.data.data,
    meta: res.data.meta,
  }));
}

export function fetchDevice(deviceId) {
  return apiClient.get(`/devices/${deviceId}`).then((res) => res.data.data);
}

export function createDevice(payload) {
  return apiClient.post("/devices", payload).then((res) => res.data.data);
}

export function updateDevice(deviceId, payload) {
  return apiClient.put(`/devices/${deviceId}`, payload).then((res) => res.data.data);
}

export function deleteDevice(deviceId) {
  return apiClient.delete(`/devices/${deviceId}`).then((res) => res.data.data);
}

export function fetchDeviceHealth(deviceId) {
  return apiClient.get(`/devices/${deviceId}/health`).then((res) => res.data.data);
}

export function syncDevice(deviceId) {
  return apiClient.post(`/devices/${deviceId}/sync`).then((res) => res.data.data);
}

export function fetchActiveAssignment(deviceId) {
  return apiClient.get(`/devices/${deviceId}/assignment`).then((res) => res.data.data);
}

export function fetchAssignments(deviceId, { page = 1, pageSize = 20 } = {}) {
  return apiClient
    .get("/devices/assignments", { params: { device_id: deviceId, page, page_size: pageSize } })
    .then((res) => ({ items: res.data.data, meta: res.data.meta }));
}

export function fetchSyncLogs(deviceId, { page = 1, pageSize = 20, status } = {}) {
  const params = { page, page_size: pageSize };
  if (status) params.status = status;
  return apiClient.get(`/devices/${deviceId}/sync-logs`, { params }).then((res) => ({
    items: res.data.data,
    meta: res.data.meta,
  }));
}

export function createAssignment({ deviceId, storeId, productId }) {
  return apiClient
    .post("/devices/assignments", { device_id: deviceId, store_id: storeId, product_id: productId })
    .then((res) => res.data.data);
}

export function unassignDevice(assignmentId) {
  return apiClient.post(`/devices/assignments/${assignmentId}/unassign`).then((res) => res.data.data);
}
