export const OUTPUT_TYPE_OPTIONS = [
  { value: "esl_simulator", label: "ESL Simulator" },
  { value: "qr_code", label: "QR Code" },
  { value: "pdf_label", label: "Printable PDF Label" },
  { value: "web_display", label: "Web Price Display" },
  { value: "pos_integration", label: "POS Integration" },
  { value: "ecommerce_integration", label: "E-commerce Integration" },
  { value: "digital_signage", label: "Digital Signage" },
];

export const OUTPUT_CHANNEL_STATUS_OPTIONS = ["active", "inactive"];

export const OUTPUT_JOB_STATUS_OPTIONS = ["pending", "processing", "completed", "failed", "cancelled"];

export const OUTPUT_JOB_STATUS_COLORS = {
  pending: "default",
  processing: "info",
  completed: "success",
  failed: "error",
  cancelled: "warning",
};

export const ROUTING_RULE_STATUS_OPTIONS = ["active", "inactive"];

export const ERROR_CORRECTION_OPTIONS = ["L", "M", "Q", "H"];

export const ORIENTATION_OPTIONS = ["landscape", "portrait"];

export const THEME_OPTIONS = ["light", "dark"];

export const QR_POSITION_OPTIONS = [
  { value: "left", label: "Left" },
  { value: "right", label: "Right" },
];

export const BANNER_POSITION_OPTIONS = [
  { value: "top", label: "Top" },
  { value: "bottom", label: "Bottom" },
];
