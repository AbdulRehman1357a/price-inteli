import { z } from "zod";

const DECIMAL_PATTERN = /^\d+(\.\d+)?$/;

const optionalDecimal = () =>
  z
    .string()
    .optional()
    .or(z.literal(""))
    .refine((value) => !value || DECIMAL_PATTERN.test(value), { message: "Enter a valid number" });

const requiredDecimal = (message) =>
  z
    .string()
    .min(1, message)
    .refine((value) => DECIMAL_PATTERN.test(value), { message: "Enter a valid number" });

export const productSchema = z.object({
  // Basic Information
  product_name: z.string().min(1, "Product name is required").max(255),
  sku: z.string().min(1, "SKU is required").max(150),
  barcode: z.string().max(150).optional().or(z.literal("")),
  category_id: z.string().min(1, "Category is required"),
  brand: z.string().max(255).optional().or(z.literal("")),
  manufacturer: z.string().max(255).optional().or(z.literal("")),
  status: z.enum(["active", "inactive", "discontinued"]),

  // Pricing
  cost_price: optionalDecimal(),
  base_price: optionalDecimal(),
  selling_price: requiredDecimal("Selling price is required"),
  currency: z.string().max(10).optional().or(z.literal("")),
  tax_rate: optionalDecimal(),

  // Additional Details
  short_description: z.string().max(500).optional().or(z.literal("")),
  description: z.string().optional().or(z.literal("")),
  weight: optionalDecimal(),
  weight_unit: z.string().max(20).optional().or(z.literal("")),

  // Media
  product_image_url: z.string().max(500).optional().or(z.literal("")),
  product_url: z.string().max(500).optional().or(z.literal("")),
  qr_id: z.string().max(150).optional().or(z.literal("")),
  shelf_id: z.string().max(150).optional().or(z.literal("")),
});
