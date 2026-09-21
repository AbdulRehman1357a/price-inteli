import { useQueries } from "@tanstack/react-query";
import BatteryFullIcon from "@mui/icons-material/BatteryFull";
import ReplayIcon from "@mui/icons-material/Replay";
import SignalCellularAltIcon from "@mui/icons-material/SignalCellularAlt";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Grid from "@mui/material/Grid";
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
import Typography from "@mui/material/Typography";
import { useState } from "react";

import { fetchProduct } from "../products/api";
import { useProduct } from "../products/hooks";
import { useStore } from "../stores/hooks";
import AssignmentForm from "./AssignmentForm";
import DeviceESLPreview from "./DeviceESLPreview";
import {
  useActiveAssignment,
  useAssignments,
  useCreateAssignment,
  useDevice,
  useDeviceHealth,
  useModels,
  useSyncDevice,
  useSyncLogs,
  useUnassignDevice,
  useVendors,
} from "./hooks";
import { CONNECTIVITY_COLORS, DEVICE_STATUS_COLORS, DEVICE_SYNC_STATUS_COLORS } from "./options";

function Field({ label, value }) {
  return (
    <Grid item xs={12} sm={6}>
      <Typography variant="caption" color="text.secondary" display="block">
        {label}
      </Typography>
      <Typography>{value ?? "—"}</Typography>
    </Grid>
  );
}

function OverviewTab({ device, vendor, model, store }) {
  return (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        <Grid container spacing={2}>
          <Field label="Device Name" value={device.device_name} />
          <Field label="Device Identifier" value={device.device_identifier} />
          <Field label="Vendor" value={vendor?.name} />
          <Field label="Model" value={model?.name} />
          <Field label="Store" value={store?.name} />
          <Field
            label="Status"
            value={
              <Chip
                label={device.status}
                size="small"
                color={DEVICE_STATUS_COLORS[device.status] ?? "default"}
                variant="outlined"
              />
            }
          />
          <Field label="Created" value={new Date(device.created_at).toLocaleString()} />
          <Field
            label="Last Sync"
            value={device.last_sync_at ? new Date(device.last_sync_at).toLocaleString() : "Never"}
          />
        </Grid>
      </Grid>
      <Grid item xs={12} md={6}>
        <Typography variant="subtitle2" gutterBottom>
          Live Preview (React ESL Simulator)
        </Typography>
        <DeviceESLPreview device={device} />
      </Grid>
    </Grid>
  );
}

function AssignedProductTab({ device }) {
  const { data: assignment, isLoading } = useActiveAssignment(device.id);
  const { data: activeProduct } = useProduct(assignment?.product_id);
  const { data: history } = useAssignments(device.id, { page: 1, pageSize: 10 });
  const createAssignment = useCreateAssignment(device.id);
  const unassign = useUnassignDevice(device.id);

  const historyProductIds = [...new Set((history?.items ?? []).map((item) => item.product_id))];
  const historyProductQueries = useQueries({
    queries: historyProductIds.map((id) => ({
      queryKey: ["products", "detail", id],
      queryFn: () => fetchProduct(id),
    })),
  });
  const historyProductById = new Map(
    historyProductQueries.map((q) => q.data).filter(Boolean).map((p) => [p.id, p])
  );

  if (isLoading) {
    return <CircularProgress size={24} />;
  }

  return (
    <Stack spacing={3}>
      {assignment ? (
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Currently Assigned
          </Typography>
          <Typography>
            {activeProduct ? `${activeProduct.product_name} (${activeProduct.sku})` : "Loading…"}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Assigned {new Date(assignment.assigned_at).toLocaleString()}
          </Typography>
          <Box sx={{ mt: 1 }}>
            <Button
              variant="outlined"
              color="error"
              size="small"
              onClick={() => unassign.mutate(assignment.id)}
              disabled={unassign.isPending}
            >
              Unassign
            </Button>
          </Box>
        </Paper>
      ) : (
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Assign a Product
          </Typography>
          <AssignmentForm device={device} onSubmit={(args) => createAssignment.mutateAsync(args)} />
        </Paper>
      )}

      {history?.items && history.items.length > 0 && (
        <Box>
          <Typography variant="subtitle2" gutterBottom>
            Assignment History
          </Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Product</TableCell>
                  <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Assigned</TableCell>
                  <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Unassigned</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {history.items.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>
                      {historyProductById.get(item.product_id)?.product_name ?? item.product_id}
                    </TableCell>
                    <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                      {new Date(item.assigned_at).toLocaleString()}
                    </TableCell>
                    <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                      {item.unassigned_at ? new Date(item.unassigned_at).toLocaleString() : "—"}
                    </TableCell>
                    <TableCell>{item.status}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}
    </Stack>
  );
}

function SyncHistoryTab({ device }) {
  const { data, isLoading } = useSyncLogs(device.id, { page: 1, pageSize: 20 });
  const sync = useSyncDevice(device.id);

  return (
    <Stack spacing={2}>
      <Box>
        <Button
          variant="contained"
          startIcon={<ReplayIcon />}
          onClick={() => sync.mutate()}
          disabled={sync.isPending}
        >
          Resync Now
        </Button>
        {sync.isError && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {sync.error?.response?.data?.error?.message ?? "Unable to sync this device."}
          </Alert>
        )}
      </Box>
      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Status</TableCell>
              <TableCell>Attempted</TableCell>
              <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Completed</TableCell>
              <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Error</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading && (
              <TableRow>
                <TableCell colSpan={4} align="center">
                  <CircularProgress size={24} />
                </TableCell>
              </TableRow>
            )}
            {!isLoading && (data?.items ?? []).length === 0 && (
              <TableRow>
                <TableCell colSpan={4} align="center">
                  <Typography color="text.secondary">No sync attempts yet.</Typography>
                </TableCell>
              </TableRow>
            )}
            {!isLoading &&
              data?.items.map((log) => (
                <TableRow key={log.id}>
                  <TableCell>
                    <Chip
                      label={log.status}
                      size="small"
                      color={DEVICE_SYNC_STATUS_COLORS[log.status] ?? "default"}
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>{new Date(log.attempted_at).toLocaleString()}</TableCell>
                  <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                    {log.completed_at ? new Date(log.completed_at).toLocaleString() : "—"}
                  </TableCell>
                  <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                    {log.error_message ?? "—"}
                  </TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Stack>
  );
}

function DeviceHealthTab({ device }) {
  const { data: health, isLoading } = useDeviceHealth(device.id, { refetchInterval: 5000 });

  if (isLoading || !health) {
    return <CircularProgress size={24} />;
  }

  return (
    <Grid container spacing={3}>
      <Grid item xs={6} sm={3}>
        <Typography variant="caption" color="text.secondary">
          Connectivity
        </Typography>
        <Box>
          <Chip
            label={health.connectivity}
            color={CONNECTIVITY_COLORS[health.connectivity] ?? "default"}
            size="small"
          />
        </Box>
      </Grid>
      <Grid item xs={6} sm={3}>
        <Typography variant="caption" color="text.secondary">
          Battery
        </Typography>
        <Stack direction="row" spacing={0.5} alignItems="center">
          <BatteryFullIcon fontSize="small" />
          <Typography variant="h6">{health.battery_level ?? "—"}%</Typography>
        </Stack>
      </Grid>
      <Grid item xs={6} sm={3}>
        <Typography variant="caption" color="text.secondary">
          Signal
        </Typography>
        <Stack direction="row" spacing={0.5} alignItems="center">
          <SignalCellularAltIcon fontSize="small" />
          <Typography variant="h6">{health.signal_strength ?? "—"}%</Typography>
        </Stack>
      </Grid>
      <Grid item xs={6} sm={3}>
        <Typography variant="caption" color="text.secondary">
          Firmware
        </Typography>
        <Typography variant="h6">{health.firmware_version ?? "—"}</Typography>
      </Grid>
      <Grid item xs={12}>
        <Typography variant="caption" color="text.secondary">
          Last Seen
        </Typography>
        <Typography>{health.last_seen_at ? new Date(health.last_seen_at).toLocaleString() : "Never"}</Typography>
      </Grid>
    </Grid>
  );
}

function ConfigurationTab({ device, vendor, model }) {
  return (
    <Grid container spacing={2}>
      <Field label="Device Identifier" value={device.device_identifier} />
      <Field label="Firmware Version" value={device.firmware_version} />
      <Field label="Vendor Website" value={vendor?.website} />
      <Field label="Screen Size" value={model?.screen_size} />
      <Field label="Resolution" value={model?.resolution} />
      <Field label="Battery Type" value={model?.battery_type} />
      <Field label="Communication Type" value={model?.communication_type} />
      <Field
        label="Color Capabilities"
        value={model?.color_capabilities ? JSON.stringify(model.color_capabilities) : null}
      />
    </Grid>
  );
}

// The full per-device management surface (overview, assigned product, sync
// history, health, configuration) — shared by the device detail page and the
// "Manage device" dialog on the ESL Integration pages.
export default function DeviceManagementTabs({ deviceId }) {
  const [tab, setTab] = useState("overview");
  const { data: device, isLoading, isError } = useDevice(deviceId);
  const { data: vendors } = useVendors();
  const { data: models } = useModels(device?.vendor_id);
  const { data: store } = useStore(device?.store_id);

  if (isLoading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (isError || !device) {
    return <Alert severity="error">Device not found.</Alert>;
  }

  const vendor = vendors?.find((v) => v.id === device.vendor_id);
  const model = models?.find((m) => m.id === device.device_model_id);

  return (
    <>
      <Tabs
        value={tab}
        onChange={(_, newValue) => setTab(newValue)}
        variant="scrollable"
        scrollButtons="auto"
        sx={{ mb: 2 }}
      >
        <Tab value="overview" label="Overview" />
        <Tab value="assigned-product" label="Assigned Product" />
        <Tab value="sync-history" label="Sync History" />
        <Tab value="device-health" label="Device Health" />
        <Tab value="configuration" label="Configuration" />
      </Tabs>

      <Paper variant="outlined" sx={{ p: 3 }}>
        {tab === "overview" && <OverviewTab device={device} vendor={vendor} model={model} store={store} />}
        {tab === "assigned-product" && <AssignedProductTab device={device} />}
        {tab === "sync-history" && <SyncHistoryTab device={device} />}
        {tab === "device-health" && <DeviceHealthTab device={device} />}
        {tab === "configuration" && <ConfigurationTab device={device} vendor={vendor} model={model} />}
      </Paper>
    </>
  );
}
