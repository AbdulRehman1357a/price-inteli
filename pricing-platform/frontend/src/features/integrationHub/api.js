import { apiClient } from "../../api/client";

export function fetchIntegrations({ page = 1, pageSize = 20, integrationCategory, provider, status } = {}) {
  const params = { page, page_size: pageSize };
  if (integrationCategory) params.integration_category = integrationCategory;
  if (provider) params.provider = provider;
  if (status) params.status = status;

  return apiClient.get("/integrations", { params }).then((res) => ({
    items: res.data.data,
    meta: res.data.meta,
  }));
}

export function fetchIntegration(integrationId) {
  return apiClient.get(`/integrations/${integrationId}`).then((res) => res.data.data);
}

export function createIntegration(payload) {
  return apiClient.post("/integrations", payload).then((res) => res.data.data);
}

export function updateIntegration(integrationId, payload) {
  return apiClient.put(`/integrations/${integrationId}`, payload).then((res) => res.data.data);
}

export function testConnection(integrationId) {
  return apiClient.post(`/integrations/${integrationId}/test`).then((res) => res.data.data);
}

export function startSync(integrationId, { entityType, jobType = "full_sync", records }) {
  return apiClient
    .post(`/integrations/${integrationId}/sync`, {
      entity_type: entityType,
      job_type: jobType,
      records,
    })
    .then((res) => res.data.data);
}

export function fetchSyncJobs(integrationId, { page = 1, pageSize = 20, status } = {}) {
  const params = { page, page_size: pageSize };
  if (status) params.status = status;
  return apiClient.get(`/integrations/${integrationId}/jobs`, { params }).then((res) => ({
    items: res.data.data,
    meta: res.data.meta,
  }));
}

export function retrySyncJob(integrationId, jobId) {
  return apiClient
    .post(`/integrations/${integrationId}/jobs/${jobId}/retry`)
    .then((res) => res.data.data);
}

export function fetchMappings(integrationId) {
  return apiClient.get(`/integrations/${integrationId}/mappings`).then((res) => res.data.data);
}

export function createMapping(integrationId, payload) {
  return apiClient
    .post(`/integrations/${integrationId}/mappings`, payload)
    .then((res) => res.data.data);
}

export function deleteMapping(integrationId, mappingId) {
  return apiClient
    .delete(`/integrations/${integrationId}/mappings/${mappingId}`)
    .then((res) => res.data.data);
}

// --- Phase 10 upgrade ---

export function fetchLocations(integrationId) {
  return apiClient.get(`/integrations/${integrationId}/locations`).then((res) => res.data.data);
}

export function discoverLocations(integrationId) {
  return apiClient
    .post(`/integrations/${integrationId}/locations/discover`)
    .then((res) => res.data.data);
}

export function updateLocation(integrationId, locationId, payload) {
  return apiClient
    .put(`/integrations/${integrationId}/locations/${locationId}`, payload)
    .then((res) => res.data.data);
}

export function fetchAuthorities(integrationId) {
  return apiClient.get(`/integrations/${integrationId}/authorities`).then((res) => res.data.data);
}

export function createAuthority(integrationId, payload) {
  return apiClient
    .post(`/integrations/${integrationId}/authorities`, payload)
    .then((res) => res.data.data);
}

export function deleteAuthority(integrationId, authorityId) {
  return apiClient
    .delete(`/integrations/${integrationId}/authorities/${authorityId}`)
    .then((res) => res.data.data);
}

export function fetchSchedules(integrationId) {
  return apiClient.get(`/integrations/${integrationId}/schedules`).then((res) => res.data.data);
}

export function createSchedule(integrationId, payload) {
  return apiClient
    .post(`/integrations/${integrationId}/schedules`, payload)
    .then((res) => res.data.data);
}

export function updateSchedule(integrationId, scheduleId, payload) {
  return apiClient
    .put(`/integrations/${integrationId}/schedules/${scheduleId}`, payload)
    .then((res) => res.data.data);
}

export function fetchWebhookEvents(integrationId, { page = 1, pageSize = 20 } = {}) {
  return apiClient
    .get(`/integrations/${integrationId}/webhook-events`, { params: { page, page_size: pageSize } })
    .then((res) => ({ items: res.data.data, meta: res.data.meta }));
}

export function rotateWebhookSecret(integrationId) {
  return apiClient
    .post(`/integrations/${integrationId}/webhook-secret/rotate`)
    .then((res) => res.data.data);
}

export function fetchErrors(integrationId, { page = 1, pageSize = 20, isResolved } = {}) {
  const params = { page, page_size: pageSize };
  if (isResolved !== undefined) params.is_resolved = isResolved;
  return apiClient
    .get(`/integrations/${integrationId}/errors`, { params })
    .then((res) => ({ items: res.data.data, meta: res.data.meta }));
}

export function resolveError(integrationId, errorId) {
  return apiClient
    .post(`/integrations/${integrationId}/errors/${errorId}/resolve`)
    .then((res) => res.data.data);
}

export function fetchReconciliation(integrationId, { page = 1, pageSize = 20, status } = {}) {
  const params = { page, page_size: pageSize };
  if (status) params.status = status;
  return apiClient
    .get(`/integrations/${integrationId}/reconciliation`, { params })
    .then((res) => ({ items: res.data.data, meta: res.data.meta }));
}

export function runReconciliation(integrationId, entityType) {
  return apiClient
    .post(`/integrations/${integrationId}/reconcile`, { entity_type: entityType })
    .then((res) => res.data.data);
}

export function resolveReconciliation(integrationId, reconciliationId, resolution) {
  return apiClient
    .post(`/integrations/${integrationId}/reconciliation/${reconciliationId}/resolve`, { resolution })
    .then((res) => res.data.data);
}

export function pushPrices(integrationId, priceIds) {
  return apiClient
    .post(`/integrations/${integrationId}/push`, { price_ids: priceIds })
    .then((res) => res.data.data);
}

export function fetchHealth(integrationId) {
  return apiClient.get(`/integrations/${integrationId}/health`).then((res) => res.data.data);
}
