import { z } from "zod";

export const organizationSchema = z.object({
  name: z.string().min(1, "Company name is required"),
  legalName: z.string().optional(),
  email: z.string().min(1, "Email is required").email("Enter a valid email address"),
  phone: z.string().optional(),
  website: z.string().optional(),
  country: z.string().optional(),
  timezone: z.string().min(1, "Timezone is required"),
  currency: z.string().min(1, "Currency is required"),
});
