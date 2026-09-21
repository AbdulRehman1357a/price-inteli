export const CATEGORY_OPTIONS = ["erp", "pos", "ecommerce", "marketplace", "custom"];

export const PROVIDER_OPTIONS = [
  { value: "csv", label: "CSV" },
  { value: "rest_api", label: "REST API" },
  { value: "webhook", label: "Webhook" },
  { value: "sap", label: "SAP (framework-ready, not yet available)" },
  { value: "oracle", label: "Oracle (framework-ready, not yet available)" },
  { value: "square", label: "Square (framework-ready, not yet available)" },
  { value: "clover", label: "Clover (framework-ready, not yet available)" },
  { value: "shopify", label: "Shopify (framework-ready, not yet available)" },
  { value: "lightspeed", label: "Lightspeed (framework-ready, not yet available)" },
  { value: "toast", label: "Toast (framework-ready, not yet available)" },
  { value: "microsoft_dynamics", label: "Microsoft Dynamics (framework-ready, not yet available)" },
  { value: "netsuite", label: "NetSuite (framework-ready, not yet available)" },
];

export const AUTH_TYPE_OPTIONS = [
  { value: "none", label: "None" },
  { value: "basic", label: "Basic (Username/Password)" },
  { value: "api_key", label: "API Key" },
  { value: "bearer", label: "Bearer Token (API Key)" },
];

export const STATUS_OPTIONS = ["pending", "active", "error", "inactive"];

export const STATUS_COLORS = {
  pending: "default",
  active: "success",
  error: "error",
  inactive: "warning",
};

export const ENTITY_TYPE_OPTIONS = ["product", "price", "inventory", "promotion", "store", "order"];

export const TRANSFORMATION_OPTIONS = [
  { value: "direct", label: "Direct (no change)" },
  { value: "uppercase", label: "Uppercase" },
  { value: "lowercase", label: "Lowercase" },
  { value: "trim", label: "Trim whitespace" },
  { value: "multiply:100", label: "Multiply by 100" },
  { value: "default:0", label: "Default to 0 if empty" },
];

export const JOB_STATUS_COLORS = {
  pending: "default",
  processing: "info",
  completed: "success",
  completed_with_errors: "warning",
  failed: "error",
};

// --- Phase 10 upgrade ---

export const AUTHORITY_OPTIONS = [
  { value: "pip", label: "PIP (this platform)" },
  { value: "external", label: "External system" },
];

export const RECONCILIATION_STATUS_COLORS = {
  open: "warning",
  resolved_pip_kept: "success",
  resolved_external_applied: "success",
  ignored: "default",
};

export const WEBHOOK_EVENT_STATUS_COLORS = {
  received: "info",
  processing: "info",
  processed: "success",
  failed: "error",
  duplicate: "default",
};

export const SCHEDULE_INTERVAL_OPTIONS = [
  { value: 5, label: "Every 5 minutes" },
  { value: 15, label: "Every 15 minutes" },
  { value: 30, label: "Every 30 minutes" },
  { value: 60, label: "Hourly" },
  { value: 1440, label: "Daily" },
];
