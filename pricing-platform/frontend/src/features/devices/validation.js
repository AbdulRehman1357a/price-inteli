import { z } from "zod";

export const deviceSchema = z.object({
  device_name: z.string().min(1, "Device name is required").max(255),
  vendor_id: z.string().min(1, "Vendor is required"),
  device_model_id: z.string().min(1, "Model is required"),
  device_identifier: z.string().min(1, "Device identifier is required").max(255),
  store_id: z.string().min(1, "Store is required"),
  status: z.enum(["active", "inactive", "offline", "maintenance"]),
});

export const assignmentSchema = z.object({
  product_id: z.string().min(1, "Product is required"),
});
