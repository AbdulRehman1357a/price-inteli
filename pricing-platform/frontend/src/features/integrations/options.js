export const INTEGRATION_TYPE_OPTIONS = [
  { value: "mock", label: "Mock (Testing)" },
  { value: "mqtt", label: "MQTT" },
  { value: "api", label: "Vendor API" },
];

// Sensible default integration_type per vendor code, used to prefill Step 1
// — still an explicit, independently-stored field (esl_integrations.integration_type),
// not derived implicitly.
export const DEFAULT_INTEGRATION_TYPE_BY_VENDOR_CODE = {
  mock: "mock",
  esl_simulator: "mqtt",
  vusion: "api",
  hanshow: "api",
  solum: "api",
  pricer: "api",
  zkong: "api",
};

export const INTEGRATION_STATUS_COLORS = {
  pending: "default",
  active: "success",
  error: "error",
  inactive: "warning",
};

// Common credential fields offered in Step 2 — which ones apply depends on
// integration_type; nothing here is vendor-specific (no hard-coded vendor
// API shape), just a generic credentials form.
export const CREDENTIAL_FIELDS_BY_TYPE = {
  mock: [],
  mqtt: [
    { name: "username", label: "MQTT Username (optional)" },
    { name: "password", label: "MQTT Password (optional)", isSecret: true },
  ],
  api: [
    { name: "api_key", label: "API Key" },
    { name: "api_secret", label: "API Secret", isSecret: true },
    { name: "username", label: "Username (optional)" },
    { name: "password", label: "Password (optional)", isSecret: true },
  ],
};

// Vendor-specific credential fields — when a vendor has its own auth model,
// these override the generic CREDENTIAL_FIELDS_BY_TYPE for that vendor code.
export const CREDENTIAL_FIELDS_BY_VENDOR_CODE = {
  pricer: [
    { name: "client_id", label: "Pricer Client ID", isSecret: false },
    { name: "client_secret", label: "Pricer Client Secret", isSecret: true },
    { name: "store_id", label: "Pricer Plaza Store ID", isSecret: false },
  ],
};

// Default base_url pre-filled per vendor (shown in Step 2 for api-type integrations).
// The user can change this — it maps to ESLIntegration.base_url on the backend.
export const DEFAULT_BASE_URL_BY_VENDOR = {
  pricer: "https://api.pricer-plaza.com",
};
