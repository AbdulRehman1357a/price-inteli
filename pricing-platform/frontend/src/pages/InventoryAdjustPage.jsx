import { zodResolver } from "@hookform/resolvers/zod";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Checkbox from "@mui/material/Checkbox";
import Container from "@mui/material/Container";
import FormControlLabel from "@mui/material/FormControlLabel";
import MenuItem from "@mui/material/MenuItem";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";

import { ADJUSTMENT_TYPE_OPTIONS } from "../features/inventory/options";
import { useBulkUpdateInventory } from "../features/inventory/hooks";
import { adjustmentSchema } from "../features/inventory/validation";
import ProductSelect from "../features/products/ProductSelect";
import StoreSelect from "../features/stores/StoreSelect";

export default function InventoryAdjustPage() {
  const navigate = useNavigate();
  const bulkUpdate = useBulkUpdateInventory();
  const [formError, setFormError] = useState(null);

  const {
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(adjustmentSchema),
    defaultValues: {
      store_id: "",
      product_id: "",
      adjustment_type: "increase",
      adjustment_quantity: "",
      reason: "",
      notes: "",
      allow_negative: false,
    },
  });

  const onSubmit = async (values) => {
    setFormError(null);
    try {
      await bulkUpdate.mutateAsync([values]);
      navigate("/inventory", { replace: true });
    } catch (error) {
      setFormError(
        error.response?.data?.error?.message ?? "Unable to apply this adjustment. Please try again."
      );
    }
  };

  return (
    <Container maxWidth="sm" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Adjust Stock
      </Typography>
      <Paper variant="outlined" sx={{ p: 3, mt: 2 }}>
        <Box component="form" onSubmit={handleSubmit(onSubmit)} noValidate>
          <Stack spacing={2}>
            {formError && <Alert severity="error">{formError}</Alert>}

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

            <Controller
              name="adjustment_type"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  select
                  label="Adjustment Type"
                  required
                  fullWidth
                  error={!!errors.adjustment_type}
                  helperText={errors.adjustment_type?.message}
                >
                  {ADJUSTMENT_TYPE_OPTIONS.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </TextField>
              )}
            />

            <Controller
              name="adjustment_quantity"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Adjustment Quantity"
                  required
                  fullWidth
                  helperText={
                    errors.adjustment_quantity?.message ??
                    "For Increase/Decrease this is the change amount; for Correction it's the new total on hand."
                  }
                  error={!!errors.adjustment_quantity}
                />
              )}
            />

            <Controller
              name="reason"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Reason"
                  required
                  fullWidth
                  error={!!errors.reason}
                  helperText={errors.reason?.message}
                />
              )}
            />

            <Controller
              name="notes"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Notes"
                  fullWidth
                  multiline
                  minRows={3}
                  error={!!errors.notes}
                  helperText={errors.notes?.message}
                />
              )}
            />

            <Controller
              name="allow_negative"
              control={control}
              render={({ field }) => (
                <FormControlLabel
                  control={<Checkbox {...field} checked={field.value} />}
                  label="Allow this adjustment to make on-hand quantity negative"
                />
              )}
            />

            <Box>
              <Button type="submit" variant="contained" size="large" disabled={isSubmitting}>
                Apply Adjustment
              </Button>
            </Box>
          </Stack>
        </Box>
      </Paper>
    </Container>
  );
}
