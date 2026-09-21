import { apiClient } from "../../api/client";

export function fetchIntegrations({ page = 1, pageSize = 20, vendorId, integrationType, status } = {}) {
  const params = { page, page_size: pageSize };
  if (vendorId) params.vendor_id = vendorId;
  if (integrationType) params.integration_type = integrationType;
  if (status) params.status = status;

  return apiClient.get("/esl-integrations", { params }).then((res) => ({
    items: res.data.data,
    meta: res.data.meta,
  }));
}

export function fetchIntegration(integrationId) {
  return apiClient.get(`/esl-integrations/${integrationId}`).then((res) => res.data.data);
}

export function createIntegration(payload) {
  return apiClient.post("/esl-integrations", payload).then((res) => res.data.data);
}

export function updateIntegration(integrationId, payload) {
  return apiClient.put(`/esl-integrations/${integrationId}`, payload).then((res) => res.data.data);
}

export function deleteIntegration(integrationId) {
  return apiClient.delete(`/esl-integrations/${integrationId}`).then((res) => res.data.data);
}

export function testConnection(integrationId) {
  return apiClient.post(`/esl-integrations/${integrationId}/test-connection`).then((res) => res.data.data);
}

export function discoverDevices(integrationId) {
  return apiClient.post(`/esl-integrations/${integrationId}/discover-devices`).then((res) => res.data.data);
}

export function importDevices(integrationId, { deviceModelId, devices }) {
  return apiClient
    .post(`/esl-integrations/${integrationId}/import-devices`, {
      device_model_id: deviceModelId,
      devices,
    })
    .then((res) => res.data.data);
}

export function testPriceUpdate(integrationId, { deviceId, productId }) {
  return apiClient
    .post(`/esl-integrations/${integrationId}/test-price-update`, {
      device_id: deviceId,
      product_id: productId || undefined,
    })
    .then((res) => res.data.data);
}

export function fetchSyncStatus(integrationId) {
  return apiClient.get(`/esl-integrations/${integrationId}/sync-status`).then((res) => res.data.data);
}
