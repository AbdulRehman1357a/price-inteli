import { zodResolver } from "@hookform/resolvers/zod";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Grid from "@mui/material/Grid";
import MenuItem from "@mui/material/MenuItem";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import { useEffect, useState } from "react";
import { Controller, useForm } from "react-hook-form";

import StoreSelect from "../stores/StoreSelect";
import { useModels, useVendors } from "./hooks";
import { DEVICE_STATUS_OPTIONS } from "./options";
import { deviceSchema } from "./validation";

const EMPTY_VALUES = {
  device_name: "",
  vendor_id: "",
  device_model_id: "",
  device_identifier: "",
  store_id: "",
  status: "active",
};

export default function DeviceForm({ defaultValues, onSubmit, submitLabel, isCreate = false }) {
  const [formError, setFormError] = useState(null);
  const { data: vendors } = useVendors();

  const {
    control,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(deviceSchema),
    defaultValues: { ...EMPTY_VALUES, ...defaultValues },
  });

  const vendorId = watch("vendor_id");
  const { data: models } = useModels(vendorId);

  // Changing the vendor invalidates whatever model was selected for the
  // previous one (models belong to exactly one vendor).
  useEffect(() => {
    if (!isCreate) return;
    setValue("device_model_id", "");
  }, [vendorId, isCreate, setValue]);

  const submit = async (values) => {
    setFormError(null);
    try {
      const payload = isCreate
        ? values
        : { device_name: values.device_name, store_id: values.store_id, status: values.status };
      await onSubmit(payload);
    } catch (error) {
      setFormError(error.response?.data?.error?.message ?? "Unable to save this device. Please try again.");
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit(submit)} noValidate>
      <Stack spacing={2}>
        {formError && <Alert severity="error">{formError}</Alert>}

        <Controller
          name="device_name"
          control={control}
          render={({ field }) => (
            <TextField
              {...field}
              label="Device Name"
              required
              fullWidth
              error={!!errors.device_name}
              helperText={errors.device_name?.message}
            />
          )}
        />

        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <Controller
              name="vendor_id"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  select
                  label="Vendor"
                  required
                  fullWidth
                  disabled={!isCreate}
                  error={!!errors.vendor_id}
                  helperText={errors.vendor_id?.message}
                >
                  {(vendors ?? []).map((vendor) => (
                    <MenuItem key={vendor.id} value={vendor.id}>
                      {vendor.name}
                    </MenuItem>
                  ))}
                </TextField>
              )}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <Controller
              name="device_model_id"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  select
                  label="Model"
                  required
                  fullWidth
                  disabled={!isCreate || !vendorId}
                  error={!!errors.device_model_id}
                  helperText={errors.device_model_id?.message}
                >
                  {(models ?? []).map((model) => (
                    <MenuItem key={model.id} value={model.id}>
                      {model.name} ({model.model_code})
                    </MenuItem>
                  ))}
                </TextField>
              )}
            />
          </Grid>
        </Grid>

        <Controller
          name="device_identifier"
          control={control}
          render={({ field }) => (
            <TextField
              {...field}
              label="Device Identifier"
              required
              fullWidth
              disabled={!isCreate}
              error={!!errors.device_identifier}
              helperText={errors.device_identifier?.message}
            />
          )}
        />

        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <Controller
              name="store_id"
              control={control}
              render={({ field }) => (
                <StoreSelect
                  value={field.value}
                  onChange={field.onChange}
                  required
                  error={!!errors.store_id}
                  helperText={errors.store_id?.message}
                />
              )}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <Controller
              name="status"
              control={control}
              render={({ field }) => (
                <TextField {...field} select label="Status" required fullWidth>
                  {DEVICE_STATUS_OPTIONS.map((status) => (
                    <MenuItem key={status} value={status}>
                      {status}
                    </MenuItem>
                  ))}
                </TextField>
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
