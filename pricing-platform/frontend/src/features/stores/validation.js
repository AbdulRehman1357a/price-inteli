import { z } from "zod";

export const storeSchema = z.object({
  store_code: z.string().min(1, "Store code is required").max(100),
  name: z.string().min(1, "Store name is required").max(255),
  legal_name: z.string().max(255).optional().or(z.literal("")),
  store_type: z.string().min(1, "Store type is required").max(100),
  email: z
    .string()
    .max(255)
    .optional()
    .or(z.literal(""))
    .refine((value) => !value || z.string().email().safeParse(value).success, {
      message: "Enter a valid email address",
    }),
  phone: z.string().max(50).optional().or(z.literal("")),
  country: z.string().min(1, "Country is required").max(100),
  state: z.string().max(100).optional().or(z.literal("")),
  city: z.string().min(1, "City is required").max(100),
  postal_code: z.string().max(30).optional().or(z.literal("")),
  address_line_1: z.string().min(1, "Address line 1 is required").max(255),
  address_line_2: z.string().max(255).optional().or(z.literal("")),
  timezone: z.string().min(1, "Timezone is required").max(100),
  currency: z.string().min(1, "Currency is required").max(10),
  status: z.enum(["active", "inactive", "closed"]),
  opening_date: z.string().optional().or(z.literal("")),
});
