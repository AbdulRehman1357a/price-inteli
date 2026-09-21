import { z } from "zod";

import { CREATE_NEW } from "./LabelTemplateSelect";

const optionalNumber = () =>
  z
    .string()
    .optional()
    .or(z.literal(""))
    .refine((value) => !value || /^\d+(\.\d+)?$/.test(value), { message: "Enter a valid number" });

export const outputChannelSchema = z.object({
  name: z.string().min(1, "Output name is required").max(255),
  output_type: z.string().min(1, "Output type is required"),
  store_id: z.string().optional().or(z.literal("")),
  label_template_id: z.string().optional().or(z.literal("")),
  status: z.enum(["active", "inactive"]),

  // esl_simulator configuration
  label_size: z.string().optional().or(z.literal("")),
  orientation: z.string().optional().or(z.literal("")),
  theme: z.string().optional().or(z.literal("")),

  // qr_code configuration
  box_size: optionalNumber(),
  border: optionalNumber(),
  error_correction: z.string().optional().or(z.literal("")),

  // pdf_label configuration
  label_width_mm: optionalNumber(),
  label_height_mm: optionalNumber(),
  show_qr: z.boolean().optional(),
  qr_position: z.enum(["left", "right"]).optional(),
  qr_size_mm: optionalNumber(),
  show_unit_price: z.boolean().optional(),
  banner_position: z.enum(["top", "bottom"]).optional(),

  // pos_integration configuration
  pos_terminal_id: z.string().optional().or(z.literal("")),

  // ecommerce_integration configuration
  platform: z.string().optional().or(z.literal("")),

  // digital_signage configuration
  screen_id: z.string().optional().or(z.literal("")),
}).superRefine((values, ctx) => {
  // The "+ Create new template..." option is a UI sentinel, not a real
  // template id — if the user submits before finishing (or cancelling)
  // that inline editor, catch it here with a field-level message instead
  // of letting the raw sentinel string reach the backend as a UUID and
  // come back as a confusing Pydantic parse error.
  if (values.label_template_id === CREATE_NEW) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      path: ["label_template_id"],
      message: "Finish saving the new template below, or choose a different option, before submitting.",
    });
  }
});

export const routingRuleSchema = z.object({
  name: z.string().min(1, "Rule name is required").max(255),
  priority: z
    .string()
    .min(1, "Priority is required")
    .refine((value) => /^\d+$/.test(value), { message: "Priority must be a whole number" }),
  status: z.enum(["active", "inactive"]),
  target_outputs_json: z.array(z.string()).min(1, "Select at least one output"),
  product_ids: z.array(z.any()).optional(),
  category_ids: z.array(z.any()).optional(),
  store_ids: z.array(z.any()).optional(),
});
