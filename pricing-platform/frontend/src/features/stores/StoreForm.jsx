import { zodResolver } from "@hookform/resolvers/zod";
import Alert from "@mui/material/Alert";
import Autocomplete from "@mui/material/Autocomplete";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Grid from "@mui/material/Grid";
import MenuItem from "@mui/material/MenuItem";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";

import { CURRENCY_OPTIONS, TIMEZONE_OPTIONS } from "../../utils/localeOptions";
import { useAuth } from "../auth/AuthContext";
import { STORE_STATUS_OPTIONS, STORE_TYPE_OPTIONS } from "./options";
import { storeSchema } from "./validation";

// Every field here is submitted to the API. organization_id is deliberately
// never one of them — the "Organization" field below is display-only,
// sourced from the authenticated user's own org (see StoreForm's use of
// useAuth()), not from form state, so it can never be spoofed from the client.
const EMPTY_VALUES = {
  name: "",
  store_code: "",
  store_type: "",
  email: "",
  phone: "",
  country: "",
  state: "",
  city: "",
  postal_code: "",
  address_line_1: "",
  address_line_2: "",
  timezone: "UTC",
  currency: "USD",
  status: "active",
  opening_date: "",
};

export default function StoreForm({ defaultValues, onSubmit, submitLabel }) {
  const { organization } = useAuth();
  const [formError, setFormError] = useState(null);

  const {
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(storeSchema),
    defaultValues: { ...EMPTY_VALUES, ...defaultValues },
  });

  const submit = async (values) => {
    setFormError(null);
    try {
      await onSubmit(values);
    } catch (error) {
      setFormError(
        error.response?.data?.error?.message ?? "Unable to save the store. Please try again."
      );
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit(submit)} noValidate>
      <Stack spacing={3}>
        {formError && <Alert severity="error">{formError}</Alert>}

        <section>
          <Typography variant="subtitle1" gutterBottom>
            Details
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <Controller
                name="name"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Store Name"
                    required
                    fullWidth
                    error={!!errors.name}
                    helperText={errors.name?.message}
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="store_code"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Store Code"
                    required
                    fullWidth
                    error={!!errors.store_code}
                    helperText={errors.store_code?.message}
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="store_type"
                control={control}
                render={({ field: { onChange, value, ...field } }) => (
                  <Autocomplete
                    freeSolo
                    options={STORE_TYPE_OPTIONS}
                    value={value || ""}
                    onInputChange={(_, newValue) => onChange(newValue)}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        {...field}
                        label="Store Type"
                        required
                        error={!!errors.store_type}
                        helperText={errors.store_type?.message}
                      />
                    )}
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Organization"
                value={organization?.name ?? ""}
                disabled
                fullWidth
                helperText="Set automatically from your account — cannot be changed here."
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="email"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Email"
                    type="email"
                    fullWidth
                    error={!!errors.email}
                    helperText={errors.email?.message}
                  />
                )}
              />
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
          </Grid>
        </section>

        <section>
          <Typography variant="subtitle1" gutterBottom>
            Address
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <Controller
                name="country"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Country"
                    required
                    fullWidth
                    error={!!errors.country}
                    helperText={errors.country?.message}
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="state"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="State / Province"
                    fullWidth
                    error={!!errors.state}
                    helperText={errors.state?.message}
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="city"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="City"
                    required
                    fullWidth
                    error={!!errors.city}
                    helperText={errors.city?.message}
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="postal_code"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Postal Code"
                    fullWidth
                    error={!!errors.postal_code}
                    helperText={errors.postal_code?.message}
                  />
                )}
              />
            </Grid>
            <Grid item xs={12}>
              <Controller
                name="address_line_1"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Address Line 1"
                    required
                    fullWidth
                    error={!!errors.address_line_1}
                    helperText={errors.address_line_1?.message}
                  />
                )}
              />
            </Grid>
            <Grid item xs={12}>
              <Controller
                name="address_line_2"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Address Line 2"
                    fullWidth
                    error={!!errors.address_line_2}
                    helperText={errors.address_line_2?.message}
                  />
                )}
              />
            </Grid>
          </Grid>
        </section>

        <section>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <Controller
                name="timezone"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    select
                    label="Timezone"
                    required
                    fullWidth
                    error={!!errors.timezone}
                    helperText={errors.timezone?.message}
                  >
                    {TIMEZONE_OPTIONS.map((tz) => (
                      <MenuItem key={tz} value={tz}>
                        {tz}
                      </MenuItem>
                    ))}
                  </TextField>
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="currency"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    select
                    label="Currency"
                    required
                    fullWidth
                    error={!!errors.currency}
                    helperText={errors.currency?.message}
                  >
                    {CURRENCY_OPTIONS.map((currency) => (
                      <MenuItem key={currency} value={currency}>
                        {currency}
                      </MenuItem>
                    ))}
                  </TextField>
                )}
              />
            </Grid>
          </Grid>
        </section>

        <section>
          <Grid container spacing={2}>
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
                    {STORE_STATUS_OPTIONS.map((status) => (
                      <MenuItem key={status} value={status}>
                        {status}
                      </MenuItem>
                    ))}
                  </TextField>
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="opening_date"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Opening Date"
                    type="date"
                    fullWidth
                    InputLabelProps={{ shrink: true }}
                    error={!!errors.opening_date}
                    helperText={errors.opening_date?.message}
                  />
                )}
              />
            </Grid>
          </Grid>
        </section>

        <Box>
          <Button type="submit" variant="contained" size="large" disabled={isSubmitting}>
            {submitLabel}
          </Button>
        </Box>
      </Stack>
    </Box>
  );
}
