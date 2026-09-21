import { z } from "zod";

export const userCreateSchema = z.object({
  firstName: z.string().min(1, "First name is required"),
  lastName: z.string().min(1, "Last name is required"),
  email: z.string().min(1, "Email is required").email("Enter a valid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
  phone: z.string().optional(),
  roleIds: z.array(z.string()).min(1, "Select at least one role"),
});

export const userUpdateSchema = z.object({
  firstName: z.string().min(1, "First name is required"),
  lastName: z.string().min(1, "Last name is required"),
  phone: z.string().optional(),
  status: z.string().min(1, "Status is required"),
  roleIds: z.array(z.string()).min(1, "Select at least one role"),
});
