import { apiClient } from "../../api/client";

export function uploadImport({ file, entityType, storeId }) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("entity_type", entityType);
  if (storeId) formData.append("store_id", storeId);

  return apiClient
    .post("/imports", formData, { headers: { "Content-Type": "multipart/form-data" } })
    .then((res) => res.data.data);
}

export function startImport(jobId, mapping) {
  return apiClient.post(`/imports/${jobId}/start`, { mapping }).then((res) => res.data.data);
}

export function fetchImportJob(jobId) {
  return apiClient.get(`/imports/${jobId}`).then((res) => res.data.data);
}

export function fetchImportErrors(jobId, { page = 1, pageSize = 50 } = {}) {
  return apiClient
    .get(`/imports/${jobId}/errors`, { params: { page, page_size: pageSize } })
    .then((res) => ({ items: res.data.data, meta: res.data.meta }));
}

export function fetchImportTemplate(entityType) {
  return apiClient.get(`/imports/templates/${entityType}`).then((res) => res.data.data);
}
