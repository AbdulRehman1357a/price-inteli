import { z } from "zod";

export const agentSchema = z.object({
  name: z.string().min(1, "Agent name is required"),
  agentType: z.string().min(1),
  status: z.string().min(1),
  schedule: z.string().min(1),
  scope: z.enum(["all", "category", "products"]),
  categoryId: z.string().optional(),
  storeId: z.string().optional(),
  productIds: z.array(z.string()).optional(),
  maxProductsPerRun: z.coerce.number().int().min(1).max(500),
  mode: z.string().min(1),
  minConfidence: z.coerce.number().min(0, "Must be 0-1").max(1, "Must be 0-1"),
  maxPriceChangePercent: z.coerce.number().min(0, "Must be 0 or more"),
  minMarginPercent: z.coerce.number(),
  approvalRequired: z.boolean(),
});
