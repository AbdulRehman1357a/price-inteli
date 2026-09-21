import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import MenuItem from "@mui/material/MenuItem";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useState } from "react";

import StoreSelect from "../stores/StoreSelect";
import { useUpdateIntegration } from "./hooks";
import { CREDENTIAL_FIELDS_BY_TYPE, CREDENTIAL_FIELDS_BY_VENDOR_CODE } from "./options";

const STATUS_OPTIONS = ["pending", "active", "error", "inactive"];

export default function EditIntegrationDialog({ integration, vendorCode, onClose }) {
  const updateIntegration = useUpdateIntegration(integration.id);
  const [name, setName] = useState(integration.name);
  const [status, setStatus] = useState(integration.status);
  const [baseUrl, setBaseUrl] = useState(integration.base_url ?? "");
  const [storeId, setStoreId] = useState(integration.store_id ?? "");
  const [credentials, setCredentials] = useState({});
  const [formError, setFormError] = useState(null);

  const credentialFields = CREDENTIAL_FIELDS_BY_VENDOR_CODE[vendorCode]
    ?? CREDENTIAL_FIELDS_BY_TYPE[integration.integration_type]
    ?? [];
  const hasCredentialEdits = Object.values(credentials).some((value) => value);

  const handleSave = async () => {
    setFormError(null);
    try {
      await updateIntegration.mutateAsync({
        name,
        status,
        base_url: baseUrl || null,
        store_id: storeId || undefined,
        credentials: hasCredentialEdits ? credentials : undefined,
      });
      onClose();
    } catch (error) {
      setFormError(error.response?.data?.error?.message ?? "Unable to save changes.");
    }
  };

  return (
    <Dialog open onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Edit Integration</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          {formError && <Alert severity="error">{formError}</Alert>}
          <TextField label="Integration Name" value={name} onChange={(e) => setName(e.target.value)} required />
          <StoreSelect value={storeId} onChange={setStoreId} required />
          <TextField select label="Status" value={status} onChange={(e) => setStatus(e.target.value)}>
            {STATUS_OPTIONS.map((option) => (
              <MenuItem key={option} value={option}>
                {option}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            label="Base URL"
            value={baseUrl}
            onChange={(e) => setBaseUrl(e.target.value)}
            placeholder="https://api.example.com"
          />
          {credentialFields.length > 0 && (
            <>
              <Typography variant="caption" color="text.secondary">
                Leave a credential field blank to keep its current saved value.
              </Typography>
              {credentialFields.map((field) => (
                <TextField
                  key={field.name}
                  label={field.label}
                  type={field.isSecret ? "password" : "text"}
                  value={credentials[field.name] ?? ""}
                  onChange={(e) => setCredentials((prev) => ({ ...prev, [field.name]: e.target.value }))}
                />
              ))}
            </>
          )}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" onClick={handleSave} disabled={updateIntegration.isPending || !name || !storeId}>
          {updateIntegration.isPending ? "Saving…" : "Save Changes"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
