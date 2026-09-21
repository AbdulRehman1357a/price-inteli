import DeleteIcon from "@mui/icons-material/Delete";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Checkbox from "@mui/material/Checkbox";
import FormControlLabel from "@mui/material/FormControlLabel";
import Grid from "@mui/material/Grid";
import IconButton from "@mui/material/IconButton";
import MenuItem from "@mui/material/MenuItem";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useState } from "react";

import { useAuthorities, useCreateAuthority, useDeleteAuthority } from "./hooks";
import { AUTHORITY_OPTIONS, ENTITY_TYPE_OPTIONS } from "./options";

const DEFAULT_FORM = { entity_type: "price", field_name: "selling_price", authority: "pip", allow_override: false };

export default function AuthorityTable({ integrationId }) {
  const [form, setForm] = useState(DEFAULT_FORM);
  const [formError, setFormError] = useState(null);
  const { data: authorities, isLoading } = useAuthorities(integrationId);
  const createAuthority = useCreateAuthority(integrationId);
  const deleteAuthority = useDeleteAuthority(integrationId);

  const submit = async () => {
    setFormError(null);
    try {
      await createAuthority.mutateAsync(form);
      setForm(DEFAULT_FORM);
    } catch (error) {
      setFormError(error.response?.data?.error?.message ?? "Unable to add this authority rule.");
    }
  };

  return (
    <Stack spacing={3}>
      <Typography variant="body2" color="text.secondary">
        Configure which system is the source of truth for a field. When PIP is authoritative, inbound
        sync writes to that field are blocked unless "Allow override" is checked (in which case the
        write proceeds but is flagged in Reconciliation for review).
      </Typography>

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="subtitle2" gutterBottom>
          Add Authority Rule
        </Typography>
        {formError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {formError}
          </Alert>
        )}
        <Box>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={2}>
              <TextField
                select
                label="Entity"
                fullWidth
                value={form.entity_type}
                onChange={(e) => setForm((f) => ({ ...f, entity_type: e.target.value }))}
              >
                {ENTITY_TYPE_OPTIONS.map((option) => (
                  <MenuItem key={option} value={option}>
                    {option}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} sm={3}>
              <TextField
                label="Field (or * for whole entity)"
                fullWidth
                value={form.field_name}
                onChange={(e) => setForm((f) => ({ ...f, field_name: e.target.value }))}
              />
            </Grid>
            <Grid item xs={12} sm={3}>
              <TextField
                select
                label="Authority"
                fullWidth
                value={form.authority}
                onChange={(e) => setForm((f) => ({ ...f, authority: e.target.value }))}
              >
                {AUTHORITY_OPTIONS.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} sm={3}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={form.allow_override}
                    onChange={(e) => setForm((f) => ({ ...f, allow_override: e.target.checked }))}
                  />
                }
                label="Allow override"
              />
            </Grid>
            <Grid item xs={12} sm={1}>
              <Button variant="contained" fullWidth onClick={submit} disabled={createAuthority.isPending}>
                Add
              </Button>
            </Grid>
          </Grid>
        </Box>
      </Paper>

      <Stack spacing={1}>
        {!isLoading && (authorities ?? []).length === 0 && (
          <Typography color="text.secondary">
            No authority rules configured — every field defaults to "External system" authority.
          </Typography>
        )}
        {(authorities ?? []).map((authority) => (
          <Paper key={authority.id} variant="outlined" sx={{ p: 1.5 }}>
            <Stack direction="row" spacing={2} alignItems="center" justifyContent="space-between">
              <Typography variant="body2">
                <strong>{authority.entity_type}</strong>.{authority.field_name} → owned by{" "}
                <strong>{authority.authority}</strong>
                {authority.allow_override ? " (override allowed, logged)" : ""}
              </Typography>
              <IconButton size="small" onClick={() => deleteAuthority.mutate(authority.id)}>
                <DeleteIcon fontSize="small" />
              </IconButton>
            </Stack>
          </Paper>
        ))}
      </Stack>
    </Stack>
  );
}
