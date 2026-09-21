import { zodResolver } from "@hookform/resolvers/zod";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import Grid from "@mui/material/Grid";
import MenuItem from "@mui/material/MenuItem";
import TextField from "@mui/material/TextField";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";

import { CURRENCY_OPTIONS, TIMEZONE_OPTIONS } from "../../utils/localeOptions";
import { useAuth } from "../auth/AuthContext";
import { updateOrganization } from "./api";
import { organizationSchema } from "./validation";

export default function OrganizationEditDialog({ open, onClose }) {
  const { organization, refreshMe } = useAuth();
  const [formError, setFormError] = useState(null);

  const {
    control,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(organizationSchema),
    values: {
      name: organization?.name ?? "",
      legalName: organization?.legal_name ?? "",
      email: organization?.email ?? "",
      phone: organization?.phone ?? "",
      website: organization?.website ?? "",
      country: organization?.country ?? "",
      timezone: organization?.timezone ?? "UTC",
      currency: organization?.currency ?? "USD",
    },
  });

  const handleClose = () => {
    setFormError(null);
    reset();
    onClose();
  };

  const submit = async (values) => {
    setFormError(null);
    try {
      await updateOrganization(values);
      await refreshMe();
      onClose();
    } catch (error) {
      setFormError(
        error.response?.data?.error?.message ?? "Unable to save company details. Please try again."
      );
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} fullWidth maxWidth="sm">
      <DialogTitle>Edit Company Details</DialogTitle>
      <Box component="form" onSubmit={handleSubmit(submit)} noValidate>
        <DialogContent>
          <Grid container spacing={2}>
            {formError && (
              <Grid item xs={12}>
                <Alert severity="error">{formError}</Alert>
              </Grid>
            )}
            <Grid item xs={12} sm={6}>
              <Controller
                name="name"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Company Name"
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
                name="legalName"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Legal Name"
                    fullWidth
                    error={!!errors.legalName}
                    helperText={errors.legalName?.message}
                  />
                )}
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
                    required
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
            <Grid item xs={12} sm={6}>
              <Controller
                name="website"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Website"
                    fullWidth
                    error={!!errors.website}
                    helperText={errors.website?.message}
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="country"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Country"
                    fullWidth
                    error={!!errors.country}
                    helperText={errors.country?.message}
                  />
                )}
              />
            </Grid>
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
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button type="submit" variant="contained" disabled={isSubmitting}>
            Save Changes
          </Button>
        </DialogActions>
      </Box>
    </Dialog>
  );
}
