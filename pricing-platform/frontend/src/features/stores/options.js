export const STORE_STATUS_OPTIONS = ["active", "inactive", "closed"];

// A curated starting list, not an enforced enum — store_type is a free-text
// column on the backend, so the form uses an Autocomplete that also accepts
// a typed custom value.
export const STORE_TYPE_OPTIONS = [
  "flagship",
  "outlet",
  "mall",
  "warehouse",
  "kiosk",
  "pop-up",
  "franchise",
];
