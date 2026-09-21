import { apiClient } from "../../api/client";

export function fetchAgents() {
  return apiClient.get("/ai-agents").then((res) => res.data.data);
}

export function fetchAgent(agentId) {
  return apiClient.get(`/ai-agents/${agentId}`).then((res) => res.data.data);
}

export function createAgent(payload) {
  return apiClient.post("/ai-agents", payload).then((res) => res.data.data);
}

export function updateAgent(agentId, payload) {
  return apiClient.put(`/ai-agents/${agentId}`, payload).then((res) => res.data.data);
}

export function deleteAgent(agentId) {
  return apiClient.delete(`/ai-agents/${agentId}`).then((res) => res.data.data);
}

export function runAgent(agentId) {
  return apiClient.post(`/ai-agents/${agentId}/run`).then((res) => res.data.data);
}

export function fetchRuns({ page = 1, pageSize = 20, agentId } = {}) {
  const params = { page, page_size: pageSize };
  if (agentId) params.agent_id = agentId;
  return apiClient.get("/ai-agent-runs", { params }).then((res) => ({
    items: res.data.data,
    meta: res.data.meta,
  }));
}

export function fetchRun(runId) {
  return apiClient.get(`/ai-agent-runs/${runId}`).then((res) => res.data.data);
}

export function fetchPolicies() {
  return apiClient.get("/ai-policies").then((res) => res.data.data);
}

export function updatePolicy(agentType, payload) {
  return apiClient.put(`/ai-policies/${agentType}`, payload).then((res) => res.data.data);
}
