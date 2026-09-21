import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Container from "@mui/material/Container";
import MenuItem from "@mui/material/MenuItem";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Step from "@mui/material/Step";
import StepLabel from "@mui/material/StepLabel";
import Stepper from "@mui/material/Stepper";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useVendors } from "../features/devices/hooks";
import StoreSelect from "../features/stores/StoreSelect";
import { useCreateIntegration, useTestConnection, useUpdateIntegration } from "../features/integrations/hooks";
import {
  CREDENTIAL_FIELDS_BY_TYPE,
  CREDENTIAL_FIELDS_BY_VENDOR_CODE,
  DEFAULT_BASE_URL_BY_VENDOR,
  DEFAULT_INTEGRATION_TYPE_BY_VENDOR_CODE,
  INTEGRATION_TYPE_OPTIONS,
} from "../features/integrations/options";

const STEP_LABELS = ["Select Vendor & Store", "Enter Credentials", "Test Connection"];
const PHASE_TO_STEP_INDEX = {
  vendor: 0,
  credentials: 1,
  test: 2,
};

export default function IntegrationSetupWizardPage() {
  const navigate = useNavigate();
  const { data: vendors } = useVendors();

  const [phase, setPhase] = useState("vendor");
  const [formError, setFormError] = useState(null);

  // Step 1
  const [vendorId, setVendorId] = useState("");
  const [integrationType, setIntegrationType] = useState("mock");
  const [name, setName] = useState("");
  const [storeId, setStoreId] = useState("");

  // Step 2
  const [credentials, setCredentials] = useState({});
  const [integration, setIntegration] = useState(null);
  const [baseUrl, setBaseUrl] = useState("");

  // Step 3
  const [testResult, setTestResult] = useState(null);

  const createIntegration = useCreateIntegration();
  const updateIntegration = useUpdateIntegration(integration?.id);
  const testConnection = useTestConnection(integration?.id);

  const selectedVendor = vendors?.find((v) => v.id === vendorId);
  const selectedVendorCode = selectedVendor?.code;
  const credentialFields = CREDENTIAL_FIELDS_BY_VENDOR_CODE[selectedVendorCode]
    ?? CREDENTIAL_FIELDS_BY_TYPE[integrationType]
    ?? [];

  const handleVendorNext = () => {
    if (!vendorId) {
      setFormError("Select a vendor.");
      return;
    }
    if (!storeId) {
      setFormError("Select a store — every devices this integration manages will belong to it.");
      return;
    }
    setFormError(null);
    setPhase("credentials");
  };

  const handleSaveCredentials = async () => {
    setFormError(null);
    try {
      if (!integration) {
        const created = await createIntegration.mutateAsync({
          vendor_id: vendorId,
          name: name || `${selectedVendor?.name ?? "Vendor"} Integration`,
          integration_type: integrationType,
          store_id: storeId,
          credentials,
          base_url: baseUrl || undefined,
        });
        setIntegration(created);
      } else {
        const updated = await updateIntegration.mutateAsync({ credentials, base_url: baseUrl || undefined });
        setIntegration(updated);
      }
      setTestResult(null);
      setPhase("test");
    } catch (error) {
      setFormError(error.response?.data?.error?.message ?? "Unable to save credentials.");
    }
  };

  const handleTestConnection = async () => {
    setFormError(null);
    try {
      const result = await testConnection.mutateAsync();
      setTestResult(result);
    } catch (error) {
      setFormError(error.response?.data?.error?.message ?? "Unable to test the connection.");
    }
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Integration Setup Wizard
      </Typography>

      <Stepper activeStep={PHASE_TO_STEP_INDEX[phase]} sx={{ my: 4, flexWrap: "wrap", rowGap: 2 }} alternativeLabel>
        {STEP_LABELS.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      <Paper variant="outlined" sx={{ p: 3 }}>
        {formError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {formError}
          </Alert>
        )}

        {phase === "vendor" && (
          <Stack spacing={2}>
            <Typography variant="subtitle1">Step 1: Select Vendor &amp; Store</Typography>
            <TextField
              select
              label="Vendor"
              required
              value={vendorId}
              onChange={(e) => {
                setVendorId(e.target.value);
                const vendor = vendors?.find((v) => v.id === e.target.value);
                setIntegrationType(DEFAULT_INTEGRATION_TYPE_BY_VENDOR_CODE[vendor?.code] ?? "api");
                setBaseUrl(DEFAULT_BASE_URL_BY_VENDOR[vendor?.code] ?? "");
              }}
            >
              {(vendors ?? []).map((vendor) => (
                <MenuItem key={vendor.id} value={vendor.id}>
                  {vendor.name}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="Integration Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={selectedVendor ? `${selectedVendor.name} Integration` : ""}
            />
            <StoreSelect
              value={storeId}
              onChange={setStoreId}
              required
              helperText="Devices discovered, imported, or added under this integration will all belong to this store."
            />
            <TextField
              select
              label="Integration Type"
              value={integrationType}
              onChange={(e) => setIntegrationType(e.target.value)}
              helperText="Auto-suggested from the vendor — change if needed."
            >
              {INTEGRATION_TYPE_OPTIONS.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </TextField>
            <Box>
              <Button variant="contained" onClick={handleVendorNext}>
                Next
              </Button>
            </Box>
          </Stack>
        )}

        {phase === "credentials" && (
          <Stack spacing={2}>
            <Typography variant="subtitle1">Step 2: Enter Credentials</Typography>
            <Typography variant="caption" color="text.secondary">
              Credentials are encrypted at rest and are never shown again after saving.
            </Typography>
            {credentialFields.length === 0 && (
              <Alert severity="info">This integration type doesn&apos;t require credentials.</Alert>
            )}
            {credentialFields.map((field) => (
              <TextField
                key={field.name}
                label={field.label}
                type={field.isSecret ? "password" : "text"}
                value={credentials[field.name] ?? ""}
                onChange={(e) => setCredentials((prev) => ({ ...prev, [field.name]: e.target.value }))}
              />
            ))}
            {integrationType === "api" && (
              <TextField
                label="API Base URL"
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
                placeholder={DEFAULT_BASE_URL_BY_VENDOR[selectedVendorCode] ?? "https://api.example.com"}
                helperText="Leave blank for vendor default. For simulator testing, use http://localhost:8090"
              />
            )}
            <Box>
              <Button
                variant="contained"
                onClick={handleSaveCredentials}
                disabled={createIntegration.isPending || updateIntegration.isPending}
              >
                Save &amp; Continue
              </Button>
            </Box>
          </Stack>
        )}

        {phase === "test" && integration && (
          <Stack spacing={2}>
            <Typography variant="subtitle1">Step 3: Test Connection</Typography>
            <Button
              variant="contained"
              onClick={handleTestConnection}
              disabled={testConnection.isPending}
              sx={{ alignSelf: "flex-start" }}
            >
              {testConnection.isPending ? "Testing…" : "Test Connection"}
            </Button>
            {testResult && (
              <Alert severity={testResult.success ? "success" : "error"}>{testResult.message}</Alert>
            )}
            <Stack direction="row" spacing={1}>
              <Button onClick={() => setPhase("credentials")}>Back to Credentials</Button>
              <Button variant="contained" onClick={() => navigate(`/integrations/${integration.id}`)}>
                Finish — Manage Devices
              </Button>
            </Stack>
          </Stack>
        )}
      </Paper>
    </Container>
  );
}
