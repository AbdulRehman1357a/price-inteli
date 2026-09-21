export const ENTITY_TYPE_OPTIONS = [
  { value: "products", label: "Products" },
  { value: "inventory", label: "Inventory" },
  { value: "users", label: "Users" },
];

// Mirrors backend app/schemas/import_job.py ImportField and
// app/services/import_service.py's _REQUIRED_FIELDS.
export const FIELDS_BY_ENTITY_TYPE = {
  products: [
    { value: "sku", label: "SKU", required: true },
    { value: "barcode", label: "Barcode", required: false },
    { value: "product_name", label: "Product Name", required: true },
    { value: "category", label: "Category", required: true },
    { value: "cost_price", label: "Cost Price", required: false },
    { value: "selling_price", label: "Selling Price", required: true },
  ],
  inventory: [
    { value: "sku", label: "SKU", required: true },
    { value: "quantity", label: "Quantity", required: true },
    { value: "reorder_point", label: "Reorder Point", required: false },
    // "store" is only required when the job wasn't uploaded with a fixed
    // store — see fieldsForJob() below.
    { value: "store", label: "Store", required: false },
  ],
  users: [
    { value: "first_name", label: "First Name", required: true },
    { value: "last_name", label: "Last Name", required: true },
    { value: "email", label: "Email", required: true },
    { value: "password", label: "Initial Password", required: true },
    { value: "role", label: "Role", required: true },
    { value: "phone", label: "Phone", required: false },
  ],
};

export function fieldsForJob(entityType, hasJobLevelStore) {
  const fields = FIELDS_BY_ENTITY_TYPE[entityType] ?? [];
  if (entityType !== "inventory") return fields;
  return fields
    .filter((field) => field.value !== "store" || !hasJobLevelStore)
    .map((field) => (field.value === "store" ? { ...field, required: true } : field));
}

export const STATUS_LABELS = {
  uploaded: "Uploaded",
  queued: "Queued",
  processing: "Processing",
  completed: "Completed",
  completed_with_errors: "Completed with errors",
  failed: "Failed",
};

export const TERMINAL_STATUSES = new Set(["completed", "completed_with_errors", "failed"]);
