export const AGENT_TYPE_OPTIONS = [
  { value: "pricing_optimization", label: "Pricing Optimization Agent" },
  { value: "inventory_health", label: "Inventory Health Agent" },
  { value: "promotion", label: "Promotion Agent" },
  { value: "device_operations", label: "Device Operations Agent" },
  { value: "integration_monitoring", label: "Integration Monitoring Agent" },
];

// Only Pricing Optimization has a real implementation this phase — the
// other 4 are valid catalog entries you can configure, but running one
// fails with an explicit error (app/ai/agents/registry.py).
export const IMPLEMENTED_AGENT_TYPES = new Set(["pricing_optimization"]);

export const AGENT_STATUS_OPTIONS = ["active", "inactive"];

export const POLICY_MODE_OPTIONS = [
  { value: "recommendation_only", label: "Recommendation Only" },
  { value: "approval_required", label: "Approval Required" },
  { value: "auto_execute_within_limits", label: "Auto Execute Within Limits" },
];

export const SCHEDULE_OPTIONS = [
  { value: "manual", label: "Manual only" },
  { value: "hourly", label: "Hourly (not yet automated)" },
  { value: "daily", label: "Daily (not yet automated)" },
  { value: "weekly", label: "Weekly (not yet automated)" },
];

export const SCOPE_OPTIONS = [
  { value: "all", label: "All active products" },
  { value: "category", label: "One category" },
  { value: "products", label: "Specific products" },
];

export const AGENT_RUN_STATUS_COLORS = { running: "info", completed: "success", failed: "error" };

export const RUN_ACTION_LABELS = {
  auto_approved_and_applied: "Auto-approved & applied",
  created_pending_recommendation: "Created pending recommendation",
  no_change_recommended: "No change recommended",
};
