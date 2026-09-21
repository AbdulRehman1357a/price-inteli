import { zodResolver } from "@hookform/resolvers/zod";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Grid from "@mui/material/Grid";
import MenuItem from "@mui/material/MenuItem";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";

import { USER_STATUS_OPTIONS } from "./options";
import RoleMultiSelect from "./RoleMultiSelect";
import { userCreateSchema, userUpdateSchema } from "./validation";

const EMPTY_VALUES = {
  firstName: "",
  lastName: "",
  email: "",
  password: "",
  phone: "",
  status: "active",
  roleIds: [],
};

export default function UserForm({ mode, defaultValues, onSubmit, submitLabel }) {
  const isEdit = mode === "edit";
  const [formError, setFormError] = useState(null);

  const {
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(isEdit ? userUpdateSchema : userCreateSchema),
    defaultValues: { ...EMPTY_VALUES, ...defaultValues },
  });

  const submit = async (values) => {
    setFormError(null);
    try {
      await onSubmit(values);
    } catch (error) {
      setFormError(error.response?.data?.error?.message ?? "Unable to save the user. Please try again.");
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit(submit)} noValidate>
      <Stack spacing={3}>
        {formError && <Alert severity="error">{formError}</Alert>}

        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <Controller
              name="firstName"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="First Name"
                  required
                  fullWidth
                  error={!!errors.firstName}
                  helperText={errors.firstName?.message}
                />
              )}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <Controller
              name="lastName"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Last Name"
                  required
                  fullWidth
                  error={!!errors.lastName}
                  helperText={errors.lastName?.message}
                />
              )}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            {isEdit ? (
              <TextField
                label="Email"
                value={defaultValues?.email ?? ""}
                disabled
                fullWidth
                helperText="Email cannot be changed here."
              />
            ) : (
              <Controller
                name="email"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Email"
                    type="email"
                    required
                    fullWidth
                    error={!!errors.email}
                    helperText={errors.email?.message}
                  />
                )}
              />
            )}
          </Grid>
          <Grid item xs={12} sm={6}>
            <Controller
              name="phone"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Phone"
                  fullWidth
                  error={!!errors.phone}
                  helperText={errors.phone?.message}
                />
              )}
            />
          </Grid>
          {!isEdit && (
            <Grid item xs={12} sm={6}>
              <Controller
                name="password"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Initial Password"
                    type="password"
                    required
                    fullWidth
                    error={!!errors.password}
                    helperText={errors.password?.message ?? "The user can change this later from their profile."}
                  />
                )}
              />
            </Grid>
          )}
          {isEdit && (
            <Grid item xs={12} sm={6}>
              <Controller
                name="status"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    select
                    label="Status"
                    required
                    fullWidth
                    error={!!errors.status}
                    helperText={errors.status?.message}
                  >
                    {USER_STATUS_OPTIONS.map((option) => (
                      <MenuItem key={option} value={option}>
                        {option}
                      </MenuItem>
                    ))}
                  </TextField>
                )}
              />
            </Grid>
          )}
          <Grid item xs={12}>
            <Controller
              name="roleIds"
              control={control}
              render={({ field }) => (
                <RoleMultiSelect
                  value={field.value}
                  onChange={field.onChange}
                  error={!!errors.roleIds}
                  helperText={errors.roleIds?.message}
                />
              )}
            />
          </Grid>
        </Grid>

        <Box>
          <Button type="submit" variant="contained" size="large" disabled={isSubmitting}>
            {submitLabel}
          </Button>
        </Box>
      </Stack>
    </Box>
  );
}
