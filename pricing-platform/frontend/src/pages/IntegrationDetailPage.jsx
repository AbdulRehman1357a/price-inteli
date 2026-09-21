import { useQueries } from "@tanstack/react-query";
import SendIcon from "@mui/icons-material/Send";
import TuneIcon from "@mui/icons-material/Tune";
import VisibilityIcon from "@mui/icons-material/Visibility";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Checkbox from "@mui/material/Checkbox";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Container from "@mui/material/Container";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogContentText from "@mui/material/DialogContentText";
import DialogTitle from "@mui/material/DialogTitle";
import Grid from "@mui/material/Grid";
import IconButton from "@mui/material/IconButton";
import MenuItem from "@mui/material/MenuItem";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Tab from "@mui/material/Tab";
import Tabs from "@mui/material/Tabs";
import TextField from "@mui/material/TextField";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { fetchActiveAssignment } from "../features/devices/api";
import DeviceManageDialog from "../features/devices/DeviceManageDialog";
import { useDevices, useModels, useVendors } from "../features/devices/hooks";
import { DEVICE_STATUS_COLORS } from "../features/devices/options";
import AddDeviceDialog from "../features/integrations/AddDeviceDialog";
import EditIntegrationDialog from "../features/integrations/EditIntegrationDialog";
import {
  useDeleteIntegration,
  useDiscoverDevices,
  useImportDevices,
  useIntegration,
  useTestConnection,
  useTestPriceUpdate,
} from "../features/integrations/hooks";
import { INTEGRATION_STATUS_COLORS } from "../features/integrations/options";
import { fetchProduct } from "../features/products/api";
import { useAllStores } from "../features/stores/hooks";

function DeleteIntegrationDialog({ integration, onClose, onDeleted }) {
  const deleteIntegration = useDeleteIntegration();
  const [formError, setFormError] = useState(null);

  const handleDelete = async () => {
    setFormError(null);
    try {
      await deleteIntegration.mutateAsync(integration.id);
      onDeleted();
    } catch (error) {
      setFormError(error.response?.data?.error?.message ?? "Unable to delete this integration.");
    }
  };

  return (
    <Dialog open onClose={onClose}>
      <DialogTitle>Delete Integration</DialogTitle>
      <DialogContent>
        {formError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {formError}
          </Alert>
        )}
        <DialogContentText>
          Delete &ldquo;{integration.name}&rdquo;? This cannot be undone.
        </DialogContentText>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button color="error" variant="contained" onClick={handleDelete} disabled={deleteIntegration.isPending}>
          {deleteIntegration.isPending ? "Deleting…" : "Delete"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

function OverviewTab({ integration, vendor, store }) {
  const navigate = useNavigate();
  const testConnection = useTestConnection(integration.id);
  const [testResult, setTestResult] = useState(null);
  const [editing, setEditing] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const handleTest = async () => {
    const result = await testConnection.mutateAsync();
    setTestResult(result);
  };

  return (
    <Stack spacing={3}>
      <Grid container spacing={2}>
        <Grid item xs={12} sm={6}>
          <Typography variant="caption" color="text.secondary">
            Vendor
          </Typography>
          <Typography>{vendor?.name ?? "—"}</Typography>
        </Grid>
        <Grid item xs={12} sm={6}>
          <Typography variant="caption" color="text.secondary">
            Store
          </Typography>
          <Typography>{store ? `${store.name} (${store.store_code})` : "—"}</Typography>
        </Grid>
        <Grid item xs={12} sm={6}>
          <Typography variant="caption" color="text.secondary">
            Integration Type
          </Typography>
          <Typography>{integration.integration_type}</Typography>
        </Grid>
        <Grid item xs={12} sm={6}>
          <Typography variant="caption" color="text.secondary">
            Base URL
          </Typography>
          <Typography>{integration.base_url || "—"}</Typography>
        </Grid>
      </Grid>

      <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap" useFlexGap>
        <Button variant="outlined" onClick={handleTest} disabled={testConnection.isPending}>
          {testConnection.isPending ? "Testing…" : "Test Connection"}
        </Button>
        <Chip
          label={integration.status}
          color={INTEGRATION_STATUS_COLORS[integration.status] ?? "default"}
          variant="outlined"
        />
        <Button onClick={() => setEditing(true)}>Edit</Button>
        <Button color="error" onClick={() => setDeleting(true)}>
          Delete
        </Button>
      </Stack>

      {testResult && (
        <Alert severity={testResult.success ? "success" : "error"}>{testResult.message}</Alert>
      )}

      {editing && (
        <EditIntegrationDialog integration={integration} vendorCode={vendor?.code} onClose={() => setEditing(false)} />
      )}
      {deleting && (
        <DeleteIntegrationDialog
          integration={integration}
          onClose={() => setDeleting(false)}
          onDeleted={() => navigate("/integrations")}
        />
      )}
    </Stack>
  );
}

function DevicesTab({ integration, vendor, store }) {
  const navigate = useNavigate();
  const { data, isLoading } = useDevices({ eslIntegrationId: integration.id, pageSize: 100 });
  const { data: models } = useModels(integration.vendor_id);
  const modelById = new Map((models ?? []).map((m) => [m.id, m]));
  const items = data?.items ?? [];

  const assignmentQueries = useQueries({
    queries: items.map((device) => ({
      queryKey: ["device-assignment", device.id],
      queryFn: () => fetchActiveAssignment(device.id),
    })),
  });
  const productIds = [...new Set(assignmentQueries.map((q) => q.data?.product_id).filter(Boolean))];
  const productQueries = useQueries({
    queries: productIds.map((id) => ({
      queryKey: ["products", "detail", id],
      queryFn: () => fetchProduct(id),
    })),
  });
  const productById = new Map(productQueries.map((q) => q.data).filter(Boolean).map((p) => [p.id, p]));
  const assignedProductByDevice = new Map(
    items.map((device, index) => [device.id, assignmentQueries[index]?.data?.product_id])
  );

  const discoverDevices = useDiscoverDevices(integration.id);
  const importDevices = useImportDevices(integration.id);
  const testPriceUpdate = useTestPriceUpdate(integration.id);
  const [discoveredDevices, setDiscoveredDevices] = useState([]);
  const [selectedIdentifiers, setSelectedIdentifiers] = useState(new Set());
  const [importModelId, setImportModelId] = useState("");
  const [discoverNotice, setDiscoverNotice] = useState(null);
  const [addOpen, setAddOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [managingDevice, setManagingDevice] = useState(null);

  // Device identifiers are unique per organization, so anything already
  // registered (under any integration) can't be imported again.
  const { data: allDevices } = useDevices({ pageSize: 500 });
  const registeredIdentifiers = new Set((allDevices?.items ?? []).map((d) => d.device_identifier));
  const [priceTestResult, setPriceTestResult] = useState(null);

  const handleTestPrice = async (device) => {
    setPriceTestResult(null);
    try {
      const result = await testPriceUpdate.mutateAsync({ deviceId: device.id });
      setPriceTestResult({ deviceName: device.device_name, ...result });
    } catch (error) {
      setPriceTestResult({
        deviceName: device.device_name,
        success: false,
        message: error.response?.data?.error?.message ?? "Unable to test the price update.",
      });
    }
  };

  const handleDiscover = async () => {
    setDiscoverNotice(null);
    setDiscoveredDevices([]);
    try {
      const result = await discoverDevices.mutateAsync();
      const devices = result.devices ?? [];
      // The API answers 200 with success:false + a reason when the vendor
      // can't discover (missing credentials, unreachable, no adapter) -
      // that reason has to be shown, not swallowed.
      if (!result.success) {
        setDiscoverNotice({
          severity: "error",
          message: result.message ?? "Discovery failed.",
          canEdit: true,
        });
        return;
      }
      if (devices.length === 0) {
        setDiscoverNotice({
          severity: "info",
          message: result.message ?? "The vendor reported no devices for this integration.",
        });
        return;
      }
      setDiscoveredDevices(devices);
      setSelectedIdentifiers(
        new Set(devices.filter((d) => !registeredIdentifiers.has(d.device_identifier)).map((d) => d.device_identifier))
      );
      setDiscoverNotice({
        severity: "success",
        message: `${result.message ? `${result.message} ` : ""}Found ${devices.length} device${devices.length === 1 ? "" : "s"}.`,
      });
    } catch (error) {
      setDiscoverNotice({
        severity: "error",
        message: error.response?.data?.error?.message ?? "Unable to discover devices.",
      });
    }
  };

  const toggleDevice = (identifier) => {
    setSelectedIdentifiers((prev) => {
      const next = new Set(prev);
      if (next.has(identifier)) next.delete(identifier);
      else next.add(identifier);
      return next;
    });
  };

  const handleImport = async () => {
    setDiscoverNotice(null);
    if (!importModelId) {
      setDiscoverNotice({ severity: "error", message: "Select a device model to apply to the imported devices." });
      return;
    }
    const devices = discoveredDevices
      .filter((d) => selectedIdentifiers.has(d.device_identifier))
      .map((d) => ({ device_identifier: d.device_identifier, device_name: d.device_name }));
    if (devices.length === 0) {
      setDiscoverNotice({ severity: "error", message: "Select at least one discovered device." });
      return;
    }
    try {
      await importDevices.mutateAsync({ deviceModelId: importModelId, devices });
      setDiscoveredDevices([]);
      setSelectedIdentifiers(new Set());
      setDiscoverNotice({
        severity: "success",
        message: `Imported ${devices.length} device${devices.length === 1 ? "" : "s"}.`,
      });
    } catch (error) {
      setDiscoverNotice({
        severity: "error",
        message: error.response?.data?.error?.message ?? "Unable to import devices.",
      });
    }
  };

  return (
    <Stack spacing={3}>
      <Paper variant="outlined" sx={{ p: 2 }}>
        <Stack
          direction={{ xs: "column", sm: "row" }}
          justifyContent="space-between"
          alignItems={{ xs: "flex-start", sm: "center" }}
          spacing={2}
        >
          <Typography variant="subtitle2">Discover &amp; Import Devices</Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            <Button variant="outlined" onClick={handleDiscover} disabled={discoverDevices.isPending}>
              {discoverDevices.isPending ? "Discovering…" : "Discover Devices"}
            </Button>
            <Button variant="contained" onClick={() => setAddOpen(true)}>
              Add Device Manually
            </Button>
          </Stack>
        </Stack>

        {!integration.store_id && (
          <Alert
            severity="warning"
            sx={{ mt: 2 }}
            action={
              <Button color="inherit" size="small" onClick={() => setEditOpen(true)}>
                Set store
              </Button>
            }
          >
            This integration has no store yet - devices can&apos;t be imported or added until you set one.
          </Alert>
        )}

        {discoverNotice && (
          <Alert
            severity={discoverNotice.severity}
            sx={{ mt: 2 }}
            onClose={() => setDiscoverNotice(null)}
            action={
              discoverNotice.canEdit ? (
                <Button color="inherit" size="small" onClick={() => setEditOpen(true)}>
                  Edit integration
                </Button>
              ) : undefined
            }
          >
            {discoverNotice.message}
          </Alert>
        )}

        {discoveredDevices.length > 0 && (
          <Stack spacing={2} sx={{ mt: 2 }}>
            <TextField
              select
              label="Device Model"
              required
              value={importModelId}
              onChange={(e) => setImportModelId(e.target.value)}
              sx={{ minWidth: { xs: "100%", sm: 260 } }}
            >
              {(models ?? []).map((model) => (
                <MenuItem key={model.id} value={model.id}>
                  {model.name} ({model.model_code})
                </MenuItem>
              ))}
            </TextField>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell padding="checkbox" />
                  <TableCell>Device Identifier</TableCell>
                  <TableCell>Device Name</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {discoveredDevices.map((device) => {
                  const alreadyAdded = registeredIdentifiers.has(device.device_identifier);
                  return (
                    <TableRow key={device.device_identifier}>
                      <TableCell padding="checkbox">
                        <Checkbox
                          checked={selectedIdentifiers.has(device.device_identifier)}
                          disabled={alreadyAdded}
                          onChange={() => toggleDevice(device.device_identifier)}
                        />
                      </TableCell>
                      <TableCell>{device.device_identifier}</TableCell>
                      <TableCell>{device.device_name}</TableCell>
                      <TableCell>
                        {alreadyAdded ? (
                          <Chip label="Already added" size="small" variant="outlined" />
                        ) : (
                          device.status ?? "—"
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
            <Box>
              <Button
                variant="contained"
                onClick={handleImport}
                disabled={importDevices.isPending || selectedIdentifiers.size === 0}
              >
                {importDevices.isPending ? "Importing…" : "Import Selected"}
              </Button>
            </Box>
          </Stack>
        )}
      </Paper>

      {priceTestResult && (
        <Alert severity={priceTestResult.success ? "success" : "error"} onClose={() => setPriceTestResult(null)}>
          {priceTestResult.deviceName}: {priceTestResult.message}
        </Alert>
      )}

      <TableContainer component={Paper} variant="outlined">
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Device Name</TableCell>
              <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Device ID</TableCell>
              <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Model</TableCell>
              <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Product</TableCell>
              <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>Battery</TableCell>
              <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>Signal</TableCell>
              <TableCell>Status</TableCell>
              <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Last Sync</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading && (
              <TableRow>
                <TableCell colSpan={9} align="center" sx={{ py: 6 }}>
                  <CircularProgress size={28} />
                </TableCell>
              </TableRow>
            )}

            {!isLoading && items.length === 0 && (
              <TableRow>
                <TableCell colSpan={9} align="center" sx={{ py: 6 }}>
                  <Typography color="text.secondary">
                    No devices under this integration yet — discover or add one above.
                  </Typography>
                </TableCell>
              </TableRow>
            )}

            {!isLoading &&
              items.map((device) => {
                const productId = assignedProductByDevice.get(device.id);
                const product = productId ? productById.get(productId) : null;
                return (
                  <TableRow key={device.id} hover>
                    <TableCell>{device.device_name}</TableCell>
                    <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                      {device.device_identifier}
                    </TableCell>
                    <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                      {modelById.get(device.device_model_id)?.name ?? "—"}
                    </TableCell>
                    <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                      {product ? `${product.product_name} (${product.sku})` : "—"}
                    </TableCell>
                    <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>
                      {device.battery_level ?? "—"}%
                    </TableCell>
                    <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>
                      {device.signal_strength ?? "—"}%
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={device.status}
                        size="small"
                        color={DEVICE_STATUS_COLORS[device.status] ?? "default"}
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                      {device.last_sync_at ? new Date(device.last_sync_at).toLocaleString() : "Never"}
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title="Manage device (product, sync history, health, configuration)">
                        <IconButton size="small" onClick={() => setManagingDevice(device)}>
                          <TuneIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Test Price Update">
                        <span>
                          <IconButton
                            size="small"
                            disabled={testPriceUpdate.isPending}
                            onClick={() => handleTestPrice(device)}
                          >
                            <SendIcon fontSize="small" />
                          </IconButton>
                        </span>
                      </Tooltip>
                      <Tooltip title="View">
                        <IconButton size="small" onClick={() => navigate(`/devices/${device.id}`)}>
                          <VisibilityIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                );
              })}
          </TableBody>
        </Table>
      </TableContainer>

      {editOpen && (
        <EditIntegrationDialog integration={integration} vendorCode={vendor?.code} onClose={() => setEditOpen(false)} />
      )}

      {addOpen && (
        <AddDeviceDialog
          integration={integration}
          vendor={vendor}
          store={store}
          onClose={() => setAddOpen(false)}
          onCreated={(device) => setManagingDevice(device)}
        />
      )}

      {managingDevice && (
        <DeviceManageDialog device={managingDevice} onClose={() => setManagingDevice(null)} />
      )}
    </Stack>
  );
}

export default function IntegrationDetailPage() {
  const { integrationId } = useParams();
  const [tab, setTab] = useState("overview");
  const { data: integration, isLoading, isError } = useIntegration(integrationId);
  const { data: vendors } = useVendors();
  const { data: stores } = useAllStores();

  if (isLoading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (isError || !integration) {
    return (
      <Container sx={{ py: 4 }}>
        <Alert severity="error">Integration not found.</Alert>
      </Container>
    );
  }

  const vendor = (vendors ?? []).find((v) => v.id === integration.vendor_id);
  const store = (stores ?? []).find((s) => s.id === integration.store_id);

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        {integration.name}
      </Typography>

      <Tabs
        value={tab}
        onChange={(_, newValue) => setTab(newValue)}
        variant="scrollable"
        scrollButtons="auto"
        sx={{ mb: 2 }}
      >
        <Tab value="overview" label="Overview" />
        <Tab value="devices" label="Devices" />
      </Tabs>

      <Paper variant="outlined" sx={{ p: 3 }}>
        {tab === "overview" && <OverviewTab integration={integration} vendor={vendor} store={store} />}
        {tab === "devices" && <DevicesTab integration={integration} vendor={vendor} store={store} />}
      </Paper>
    </Container>
  );
}
