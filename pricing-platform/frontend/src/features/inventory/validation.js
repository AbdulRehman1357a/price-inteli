import { z } from "zod";

const DECIMAL_PATTERN = /^\d+(\.\d+)?$/;

export const adjustmentSchema = z.object({
  store_id: z.string().min(1, "Store is required"),
  product_id: z.string().min(1, "Product is required"),
  adjustment_type: z.enum(["increase", "decrease", "correction"]),
  adjustment_quantity: z
    .string()
    .min(1, "Adjustment quantity is required")
    .refine((value) => DECIMAL_PATTERN.test(value), { message: "Enter a valid non-negative number" }),
  reason: z.string().min(1, "Reason is required").max(255),
  notes: z.string().optional().or(z.literal("")),
  allow_negative: z.boolean().optional(),
});
