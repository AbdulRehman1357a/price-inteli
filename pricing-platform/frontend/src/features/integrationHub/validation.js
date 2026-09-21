import { z } from "zod";

export const integrationSchema = z.object({
  name: z.string().min(1, "Integration name is required").max(255),
  integration_category: z.string().min(1, "Category is required"),
  provider: z.string().min(1, "Provider is required"),
  status: z.enum(["pending", "active", "error", "inactive"]),
  authentication_type: z.string().optional().or(z.literal("")),
  base_url: z.string().max(500).optional().or(z.literal("")),
  username: z.string().optional().or(z.literal("")),
  password: z.string().optional().or(z.literal("")),
  api_key: z.string().optional().or(z.literal("")),
  webhook_url: z.string().optional().or(z.literal("")),
});

export const mappingSchema = z.object({
  entity_type: z.string().min(1, "Entity type is required"),
  source_field: z.string().min(1, "Source field is required").max(255),
  canonical_field: z.string().min(1, "Canonical field is required").max(255),
  transformation_rule: z.string().optional().or(z.literal("")),
});
