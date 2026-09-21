// Mirrors app.services.analytics_service.DEFAULT_RANGE_DAYS on the backend
// — used only to pre-fill the date pickers; the backend applies the same
// default itself if a request omits date_from/date_to.
const DEFAULT_RANGE_DAYS = 30;

function toDateInputValue(date) {
  return date.toISOString().slice(0, 10);
}

export function defaultDateRange() {
  const today = new Date();
  const from = new Date(today);
  from.setDate(from.getDate() - (DEFAULT_RANGE_DAYS - 1));
  return { dateFrom: toDateInputValue(from), dateTo: toDateInputValue(today) };
}

export const DASHBOARD_CARDS = [
  {
    key: "executive",
    to: "/dashboard/executive",
    title: "Executive Dashboard",
    description: "Revenue, margin, and activity across pricing, inventory, AI, and devices.",
    metrics: ["revenue", "gross_margin_pct", "ai_recommendations_count", "low_stock_count"],
  },
  {
    key: "pricing",
    to: "/dashboard/pricing",
    title: "Pricing Dashboard",
    description: "Revenue, margin, and how often — and by how much — prices are changing.",
    metrics: ["revenue", "price_changes_count", "average_price_change", "gross_margin_pct"],
  },
  {
    key: "inventory",
    to: "/dashboard/inventory",
    title: "Inventory Dashboard",
    description: "Stock health across every store — what's running low and what's overstocked.",
    metrics: ["low_stock_count", "overstock_count"],
  },
  {
    key: "ai",
    to: "/dashboard/ai",
    title: "AI Dashboard",
    description: "How many pricing recommendations the AI is generating, and how often they're approved.",
    metrics: ["ai_recommendations_count", "ai_approval_rate_pct"],
  },
  {
    key: "devices",
    to: "/dashboard/devices",
    title: "Device Dashboard",
    description: "ESL device sync reliability — failed updates and overall uptime.",
    metrics: ["failed_device_updates_count", "device_uptime_pct"],
  },
];

export const METRIC_DEFS = {
  revenue: { label: "Revenue", format: "currency" },
  gross_margin_amount: { label: "Gross Margin", format: "currency" },
  gross_margin_pct: { label: "Gross Margin", format: "percent" },
  price_changes_count: { label: "Price Changes", format: "count" },
  average_price_change: { label: "Average Price Change", format: "currency" },
  ai_recommendations_count: { label: "AI Recommendations", format: "count" },
  ai_approval_rate_pct: { label: "AI Approval Rate", format: "percent" },
  low_stock_count: { label: "Low Stock", format: "count" },
  overstock_count: { label: "Overstock", format: "count" },
  failed_device_updates_count: { label: "Failed Device Updates", format: "count" },
  device_uptime_pct: { label: "Device Uptime", format: "percent" },
};

export function formatMetricValue(key, value) {
  if (value === null || value === undefined) return "—";
  const { format } = METRIC_DEFS[key] ?? {};
  const number = Number(value);
  if (Number.isNaN(number)) return "—";
  if (format === "currency") {
    try {
      return new Intl.NumberFormat(undefined, { style: "currency", currency: "USD" }).format(number);
    } catch {
      return number.toFixed(2);
    }
  }
  if (format === "percent") return `${number.toFixed(2)}%`;
  return number.toLocaleString();
}
