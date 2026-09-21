export const RECOMMENDATION_STATUS_OPTIONS = ["pending", "approved", "rejected", "applied", "expired"];

export const RECOMMENDATION_STATUS_COLORS = {
  pending: "warning",
  approved: "info",
  rejected: "error",
  applied: "success",
  expired: "default",
};

export function formatCurrency(value, currency = "USD") {
  const amount = Number(value);
  if (Number.isNaN(amount)) return "—";
  try {
    return new Intl.NumberFormat(undefined, { style: "currency", currency }).format(amount);
  } catch {
    return amount.toFixed(2);
  }
}

export function formatPercent(value) {
  if (value === null || value === undefined) return "—";
  const amount = Number(value);
  if (Number.isNaN(amount)) return "—";
  return `${amount > 0 ? "+" : ""}${amount.toFixed(2)}%`;
}
