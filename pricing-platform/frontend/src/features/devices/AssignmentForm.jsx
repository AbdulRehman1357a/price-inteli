import { zodResolver } from "@hookform/resolvers/zod";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";

import ProductSelect from "../products/ProductSelect";
import { useStore } from "../stores/hooks";
import { assignmentSchema } from "./validation";

// "Device*" and "Store*" from the Phase 8 Assignment Form spec are
// pre-filled from the device whose detail page this form is embedded in
// (assigning always happens in that context) and shown read-only rather
// than as free-choice dropdowns — a device can only assign within its own
// store, which the backend also enforces (device_store_mismatch).
export default function AssignmentForm({ device, onSubmit, submitLabel = "Assign Product" }) {
  const [formError, setFormError] = useState(null);
  const { data: store } = useStore(device.store_id);

  const {
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(assignmentSchema),
    defaultValues: { product_id: "" },
  });

  const submit = async (values) => {
    setFormError(null);
    try {
      await onSubmit({ deviceId: device.id, storeId: device.store_id, productId: values.product_id });
    } catch (error) {
      setFormError(error.response?.data?.error?.message ?? "Unable to assign this product.");
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit(submit)} noValidate>
      <Stack spacing={2}>
        {formError && <Alert severity="error">{formError}</Alert>}
        <TextField label="Device" value={device.device_name} disabled fullWidth />
        <TextField label="Store" value={store?.name ?? ""} disabled fullWidth />
        <Controller
          name="product_id"
          control={control}
          render={({ field }) => (
            <ProductSelect
              value={field.value}
              onChange={field.onChange}
              required
              error={!!errors.product_id}
              helperText={errors.product_id?.message}
            />
          )}
        />
        <Box>
          <Button type="submit" variant="contained" disabled={isSubmitting}>
            {submitLabel}
          </Button>
        </Box>
      </Stack>
    </Box>
  );
}
