import { zodResolver } from "@hookform/resolvers/zod";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Grid from "@mui/material/Grid";
import MenuItem from "@mui/material/MenuItem";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";

import { AUTH_TYPE_OPTIONS, CATEGORY_OPTIONS, PROVIDER_OPTIONS, STATUS_OPTIONS } from "./options";
import { integrationSchema } from "./validation";

const EMPTY_VALUES = {
  name: "",
  integration_category: "erp",
  provider: "csv",
  status: "pending",
  authentication_type: "none",
  base_url: "",
  username: "",
  password: "",
  api_key: "",
  webhook_url: "",
};

// Converts the API's IntegrationOut shape into this form's flat field
// values. Credentials are never returned by the API (encrypted at rest,
// never echoed back) — on edit, the credential fields simply start blank;
// submitting leaves them unchanged unless the user fills something in.
export function integrationToFormValues(integration) {
  return { ...EMPTY_VALUES, ...integration };
}

function toApiPayload(values, { isCreate }) {
  const credentials = {};
  if (values.authentication_type) credentials.authentication_type = values.authentication_type;
  if (values.base_url) credentials.base_url = values.base_url;
  if (values.username) credentials.username = values.username;
  if (values.password) credentials.password = values.password;
  if (values.api_key) credentials.api_key = values.api_key;
  if (values.webhook_url) credentials.webhook_url = values.webhook_url;

  const payload = { name: values.name, status: values.status };
  if (isCreate) {
    payload.integration_category = values.integration_category;
    payload.provider = values.provider;
    payload.credentials = credentials;
  } else {
    payload.integration_category = values.integration_category;
    if (Object.keys(credentials).length > 0) payload.credentials = credentials;
  }
  return payload;
}

export default function IntegrationForm({ defaultValues, onSubmit, submitLabel, isCreate = false }) {
  const [formError, setFormError] = useState(null);

  const {
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(integrationSchema),
    defaultValues: { ...EMPTY_VALUES, ...defaultValues },
  });

  const submit = async (values) => {
    setFormError(null);
    try {
      await onSubmit(toApiPayload(values, { isCreate }));
    } catch (error) {
      setFormError(
        error.response?.data?.error?.message ?? "Unable to save this integration. Please try again."
      );
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit(submit)} noValidate>
      <Stack spacing={2}>
        {formError && <Alert severity="error">{formError}</Alert>}

        <Controller
          name="name"
          control={control}
          render={({ field }) => (
            <TextField
              {...field}
              label="Integration Name"
              required
              fullWidth
              error={!!errors.name}
              helperText={errors.name?.message}
            />
          )}
        />

        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <Controller
              name="integration_category"
              control={control}
              render={({ field }) => (
                <TextField {...field} select label="Category" required fullWidth>
                  {CATEGORY_OPTIONS.map((option) => (
                    <MenuItem key={option} value={option}>
                      {option}
                    </MenuItem>
                  ))}
                </TextField>
              )}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <Controller
              name="provider"
              control={control}
              render={({ field }) => (
                <TextField {...field} select label="Provider" required fullWidth disabled={!isCreate}>
                  {PROVIDER_OPTIONS.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </TextField>
              )}
            />
          </Grid>
        </Grid>

        <Typography variant="subtitle2" sx={{ pt: 1 }}>
          Authentication
        </Typography>
        <Typography variant="caption" color="text.secondary">
          Credentials are encrypted at rest and are never shown again after saving.
        </Typography>

        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <Controller
              name="authentication_type"
              control={control}
              render={({ field }) => (
                <TextField {...field} select label="Authentication Type" required fullWidth>
                  {AUTH_TYPE_OPTIONS.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </TextField>
              )}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <Controller
              name="base_url"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Base URL"
                  fullWidth
                  helperText="For CSV providers, the file path or URL to read."
                />
              )}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <Controller
              name="username"
              control={control}
              render={({ field }) => <TextField {...field} label="Username" fullWidth />}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <Controller
              name="password"
              control={control}
              render={({ field }) => <TextField {...field} label="Password" type="password" fullWidth />}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <Controller
              name="api_key"
              control={control}
              render={({ field }) => <TextField {...field} label="API Key" type="password" fullWidth />}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <Controller
              name="webhook_url"
              control={control}
              render={({ field }) => <TextField {...field} label="Webhook URL" fullWidth />}
            />
          </Grid>
        </Grid>

        <Controller
          name="status"
          control={control}
          render={({ field }) => (
            <TextField {...field} select label="Status" required sx={{ maxWidth: 240 }}>
              {STATUS_OPTIONS.map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </TextField>
          )}
        />

        <Box>
          <Button type="submit" variant="contained" size="large" disabled={isSubmitting}>
            {submitLabel}
          </Button>
        </Box>
      </Stack>
    </Box>
  );
}
