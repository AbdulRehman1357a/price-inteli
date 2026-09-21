import { z } from "zod";

const DECIMAL_PATTERN = /^-?\d+(\.\d+)?$/;
const decimalString = (message) =>
  z
    .string()
    .optional()
    .or(z.literal(""))
    .refine((value) => !value || DECIMAL_PATTERN.test(value), { message: message ?? "Enter a valid number" });

export const ruleSchema = z.object({
  name: z.string().min(1, "Rule name is required").max(255),
  description: z.string().optional().or(z.literal("")),
  rule_type: z.string().min(1, "Rule type is required"),
  priority: z
    .string()
    .min(1, "Priority is required")
    .refine((value) => /^\d+$/.test(value), { message: "Priority must be a whole number" }),
  status: z.enum(["draft", "active", "inactive"]),
  approval_required: z.boolean().optional(),
  effective_from: z.string().optional().or(z.literal("")),
  effective_to: z.string().optional().or(z.literal("")),

  // Action
  action_kind: z.string().min(1, "Action is required"),
  action_value: z
    .string()
    .min(1, "Value is required")
    .refine((value) => DECIMAL_PATTERN.test(value), { message: "Enter a valid number" }),

  // Scope (conditions)
  product_ids: z.array(z.string()).optional(),
  category_ids: z.array(z.string()).optional(),
  store_ids: z.array(z.string()).optional(),
  min_quantity: decimalString(),
  max_quantity: decimalString(),

  // Constraints
  min_price: decimalString(),
  max_price: decimalString(),
  min_margin_percentage: decimalString(),
  max_discount_percentage: decimalString(),
  rounding: z.string().optional().or(z.literal("")),
});
