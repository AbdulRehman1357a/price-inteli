export const RULE_TYPE_OPTIONS = [
  { value: "fixed_price", label: "Fixed Price" },
  { value: "percentage_discount", label: "Percentage Discount" },
  { value: "fixed_discount", label: "Fixed Discount" },
  { value: "margin_based", label: "Margin Based" },
  { value: "cost_plus", label: "Cost Plus" },
  { value: "inventory_based", label: "Inventory Based" },
  { value: "time_based", label: "Time Based" },
  { value: "store_specific", label: "Store Specific" },
  { value: "promotion", label: "Promotion" },
  { value: "clearance", label: "Clearance" },
];

export const RULE_STATUS_OPTIONS = ["draft", "active", "inactive"];

// What the engine actually computes (app/schemas/pricing_rule.py ActionKind)
// — decoupled from rule_type, which is just a categorization label.
export const ACTION_KIND_OPTIONS = [
  { value: "fixed_price", label: "Fixed Price", valueField: "value", valueLabel: "Price" },
  {
    value: "percentage_discount",
    label: "Percentage Discount",
    valueField: "value",
    valueLabel: "Percentage Off (%)",
  },
  { value: "fixed_discount", label: "Fixed Discount", valueField: "value", valueLabel: "Amount Off" },
  {
    value: "margin_based",
    label: "Margin Based",
    valueField: "margin_percentage",
    valueLabel: "Target Margin (%)",
  },
  {
    value: "cost_plus",
    label: "Cost Plus",
    valueField: "markup_percentage",
    valueLabel: "Markup Over Cost (%)",
  },
];

export const ROUNDING_OPTIONS = [
  { value: "", label: "No rounding" },
  { value: "0.01", label: "Nearest cent" },
  { value: "0.05", label: "Nearest nickel ($0.05)" },
  { value: "0.10", label: "Nearest dime ($0.10)" },
  { value: "1.00", label: "Nearest dollar" },
  { value: "charm_99", label: "Charm pricing (X.99)" },
];
