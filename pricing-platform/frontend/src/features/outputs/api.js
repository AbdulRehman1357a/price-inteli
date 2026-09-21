import { apiClient } from "../../api/client";

export function fetchChannels({ page = 1, pageSize = 20, outputType, storeId, status } = {}) {
  const params = { page, page_size: pageSize };
  if (outputType) params.output_type = outputType;
  if (storeId) params.store_id = storeId;
  if (status) params.status = status;

  return apiClient.get("/outputs/channels", { params }).then((res) => ({
    items: res.data.data,
    meta: res.data.meta,
  }));
}

export function fetchChannel(channelId) {
  return apiClient.get(`/outputs/channels/${channelId}`).then((res) => res.data.data);
}

export function createChannel(payload) {
  return apiClient.post("/outputs/channels", payload).then((res) => res.data.data);
}

export function updateChannel(channelId, payload) {
  return apiClient.put(`/outputs/channels/${channelId}`, payload).then((res) => res.data.data);
}

export function fetchJobs({
  page = 1,
  pageSize = 20,
  outputChannelId,
  productId,
  storeId,
  status,
} = {}) {
  const params = { page, page_size: pageSize };
  if (outputChannelId) params.output_channel_id = outputChannelId;
  if (productId) params.product_id = productId;
  if (storeId) params.store_id = storeId;
  if (status) params.status = status;

  return apiClient.get("/outputs/jobs", { params }).then((res) => ({
    items: res.data.data,
    meta: res.data.meta,
  }));
}

export function fetchJob(jobId) {
  return apiClient.get(`/outputs/jobs/${jobId}`).then((res) => res.data.data);
}

export function createJob({ outputChannelId, productId, storeId }) {
  return apiClient
    .post("/outputs/jobs", {
      output_channel_id: outputChannelId,
      product_id: productId,
      store_id: storeId || undefined,
    })
    .then((res) => res.data.data);
}

export function createBulkJobs({ outputChannelId, productIds, storeId }) {
  return apiClient
    .post("/outputs/jobs/bulk", {
      output_channel_id: outputChannelId,
      product_ids: productIds,
      store_id: storeId || undefined,
    })
    .then((res) => res.data.data);
}

export function retryJob(jobId) {
  return apiClient.post(`/outputs/jobs/${jobId}/retry`).then((res) => res.data.data);
}

export function cancelJob(jobId) {
  return apiClient.post(`/outputs/jobs/${jobId}/cancel`).then((res) => res.data.data);
}

export function fetchJobsSummary() {
  return apiClient.get("/outputs/jobs/summary").then((res) => res.data.data);
}

export function fetchPublicPrice(productId, storeId) {
  const params = storeId ? { store_id: storeId } : undefined;
  return apiClient.get(`/public/price/${productId}`, { params }).then((res) => res.data.data);
}

export function fetchRoutingRules({ page = 1, pageSize = 20, status } = {}) {
  const params = { page, page_size: pageSize };
  if (status) params.status = status;

  return apiClient.get("/outputs/routing-rules", { params }).then((res) => ({
    items: res.data.data,
    meta: res.data.meta,
  }));
}

export function fetchRoutingRule(ruleId) {
  return apiClient.get(`/outputs/routing-rules/${ruleId}`).then((res) => res.data.data);
}

export function createRoutingRule(payload) {
  return apiClient.post("/outputs/routing-rules", payload).then((res) => res.data.data);
}

export function updateRoutingRule(ruleId, payload) {
  return apiClient.put(`/outputs/routing-rules/${ruleId}`, payload).then((res) => res.data.data);
}

// ── Label Templates ───────────────────────────────────────────

export function fetchLabelTemplates() {
  return apiClient.get("/outputs/label-templates").then((res) => res.data.data);
}

export function fetchLabelTemplate(templateId) {
  return apiClient.get(`/outputs/label-templates/${templateId}`).then((res) => res.data.data);
}

export function createLabelTemplate(payload) {
  return apiClient.post("/outputs/label-templates", payload).then((res) => res.data.data);
}

export function updateLabelTemplate(templateId, payload) {
  return apiClient.put(`/outputs/label-templates/${templateId}`, payload).then((res) => res.data.data);
}

export function deleteLabelTemplate(templateId) {
  return apiClient.delete(`/outputs/label-templates/${templateId}`).then((res) => res.data);
}

export function uploadTemplateBackgroundImage(templateId, file) {
  const formData = new FormData();
  formData.append("file", file);
  return apiClient
    .post(`/outputs/label-templates/${templateId}/background-image`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    })
    .then((res) => res.data.data);
}
