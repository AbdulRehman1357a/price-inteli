import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import Grid from "@mui/material/Grid";
import MenuItem from "@mui/material/MenuItem";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import { useState } from "react";

import { useCreateDevice, useModels } from "../devices/hooks";
import { DEVICE_STATUS_OPTIONS } from "../devices/options";

// Same fields as the All Devices form (DeviceForm.jsx) — but Vendor and
// Store belong to the integration, so they're shown locked rather than
// editable; the backend derives both from esl_integration_id anyway.
export default function AddDeviceDialog({ integration, vendor, store, onClose, onCreated }) {
  const { data: models } = useModels(integration.vendor_id);
  const createDevice = useCreateDevice();
  const [deviceName, setDeviceName] = useState("");
  const [deviceModelId, setDeviceModelId] = useState("");
  const [deviceIdentifier, setDeviceIdentifier] = useState("");
  const [status, setStatus] = useState("active");
  const [formError, setFormError] = useState(null);

  const handleSave = async () => {
    setFormError(null);
    try {
      const device = await createDevice.mutateAsync({
        esl_integration_id: integration.id,
        device_model_id: deviceModelId,
        device_identifier: deviceIdentifier,
        device_name: deviceName,
        status,
      });
      onCreated?.(device);
      onClose();
    } catch (error) {
      setFormError(error.response?.data?.error?.message ?? "Unable to add this device.");
    }
  };

  return (
    <Dialog open onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Add Device</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          {formError && <Alert severity="error">{formError}</Alert>}

          <TextField
            label="Device Name"
            required
            fullWidth
            value={deviceName}
            onChange={(e) => setDeviceName(e.target.value)}
          />

          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField label="Vendor" fullWidth disabled value={vendor?.name ?? ""} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                select
                label="Model"
                required
                fullWidth
                value={deviceModelId}
                onChange={(e) => setDeviceModelId(e.target.value)}
              >
                {(models ?? []).map((model) => (
                  <MenuItem key={model.id} value={model.id}>
                    {model.name} ({model.model_code})
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
          </Grid>

          <TextField
            label="Device Identifier"
            required
            fullWidth
            value={deviceIdentifier}
            onChange={(e) => setDeviceIdentifier(e.target.value)}
          />

          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Store"
                fullWidth
                disabled
                value={store ? `${store.name} (${store.store_code})` : ""}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                select
                label="Status"
                required
                fullWidth
                value={status}
                onChange={(e) => setStatus(e.target.value)}
              >
                {DEVICE_STATUS_OPTIONS.map((option) => (
                  <MenuItem key={option} value={option}>
                    {option}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
          </Grid>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          onClick={handleSave}
          disabled={createDevice.isPending || !deviceName || !deviceIdentifier || !deviceModelId}
        >
          {createDevice.isPending ? "Adding…" : "Add Device"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
