import { useQueries } from "@tanstack/react-query";
import BatteryFullIcon from "@mui/icons-material/BatteryFull";
import DeleteIcon from "@mui/icons-material/Delete";
import SignalCellularAltIcon from "@mui/icons-material/SignalCellularAlt";
import VisibilityIcon from "@mui/icons-material/Visibility";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Container from "@mui/material/Container";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogContentText from "@mui/material/DialogContentText";
import DialogTitle from "@mui/material/DialogTitle";
import IconButton from "@mui/material/IconButton";
import MenuItem from "@mui/material/MenuItem";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TablePagination from "@mui/material/TablePagination";
import TableRow from "@mui/material/TableRow";
import TextField from "@mui/material/TextField";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import { useState } from "react";
import { Link as RouterLink, useNavigate } from "react-router-dom";

import { fetchActiveAssignment } from "../features/devices/api";
import { useAllModels, useDeleteDevice, useDevices, useVendors } from "../features/devices/hooks";
import { DEVICE_STATUS_COLORS, DEVICE_STATUS_OPTIONS } from "../features/devices/options";
import { fetchProduct } from "../features/products/api";
import { useAllStores } from "../features/stores/hooks";

function DeleteDeviceDialog({ device, onClose, onDeleted }) {
  const deleteDevice = useDeleteDevice();
  const [formError, setFormError] = useState(null);

  const handleDelete = async () => {
    setFormError(null);
    try {
      await deleteDevice.mutateAsync(device.id);
      onDeleted();
    } catch (error) {
      setFormError(error.response?.data?.error?.message ?? "Unable to delete this device.");
    }
  };

  return (
    <Dialog open onClose={onClose}>
      <DialogTitle>Delete Device</DialogTitle>
      <DialogContent>
        {formError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {formError}
          </Alert>
        )}
        <DialogContentText>
          Delete &ldquo;{device.device_name}&rdquo;? Its product assignments and sync history are removed
          with it. This cannot be undone.
        </DialogContentText>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button color="error" variant="contained" onClick={handleDelete} disabled={deleteDevice.isPending}>
          {deleteDevice.isPending ? "Deleting…" : "Delete"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default function DevicesListPage() {
  const navigate = useNavigate();
  const [deletingDevice, setDeletingDevice] = useState(null);
  const [searchInput, setSearchInput] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const { data, isLoading, isError } = useDevices({ page, pageSize, status, search: searchInput || undefined });
  const { data: vendors } = useVendors();
  const { data: models } = useAllModels();
  const { data: stores } = useAllStores();

  const items = data?.items ?? [];
  const vendorById = new Map((vendors ?? []).map((v) => [v.id, v]));
  const modelById = new Map((models ?? []).map((m) => [m.id, m]));
  const storeById = new Map((stores ?? []).map((s) => [s.id, s]));

  const assignmentQueries = useQueries({
    queries: items.map((device) => ({
      queryKey: ["device-assignment", device.id],
      queryFn: () => fetchActiveAssignment(device.id),
    })),
  });
  const productIds = [
    ...new Set(assignmentQueries.map((q) => q.data?.product_id).filter(Boolean)),
  ];
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

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Stack
        direction={{ xs: "column", sm: "row" }}
        justifyContent="space-between"
        alignItems={{ xs: "flex-start", sm: "center" }}
        spacing={2}
        sx={{ mb: 3 }}
      >
        <Typography variant="h4" component="h1">
          Devices
        </Typography>
        <Button variant="contained" component={RouterLink} to="/devices/new">
          New Device
        </Button>
      </Stack>

      <Stack direction={{ xs: "column", sm: "row" }} spacing={2} sx={{ mb: 2 }}>
        <TextField
          label="Search"
          placeholder="Device name or identifier"
          value={searchInput}
          onChange={(event) => {
            setSearchInput(event.target.value);
            setPage(1);
          }}
          sx={{ minWidth: { xs: "100%", sm: 240 } }}
        />
        <TextField
          select
          label="Status"
          value={status}
          onChange={(event) => {
            setStatus(event.target.value);
            setPage(1);
          }}
          sx={{ minWidth: { xs: "100%", sm: 160 } }}
        >
          <MenuItem value="">All statuses</MenuItem>
          {DEVICE_STATUS_OPTIONS.map((option) => (
            <MenuItem key={option} value={option}>
              {option}
            </MenuItem>
          ))}
        </TextField>
      </Stack>

      {isError && <Alert severity="error">Unable to load devices.</Alert>}

      <TableContainer component={Paper} variant="outlined">
        <Table size="small" sx={{ "& th, & td": { overflowWrap: "anywhere" } }}>
          <TableHead>
            <TableRow>
              <TableCell>Device</TableCell>
              <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Vendor / Model</TableCell>
              <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>Store</TableCell>
              <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Product</TableCell>
              <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>Battery / Signal</TableCell>
              <TableCell>Status</TableCell>
              <TableCell sx={{ display: { xs: "none", lg: "table-cell" } }}>Last Sync</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading && (
              <TableRow>
                <TableCell colSpan={8} align="center" sx={{ py: 6 }}>
                  <CircularProgress size={28} />
                </TableCell>
              </TableRow>
            )}

            {!isLoading && items.length === 0 && (
              <TableRow>
                <TableCell colSpan={8} align="center" sx={{ py: 6 }}>
                  <Typography color="text.secondary">No devices found.</Typography>
                </TableCell>
              </TableRow>
            )}

            {!isLoading &&
              items.map((device) => {
                const productId = assignedProductByDevice.get(device.id);
                const product = productId ? productById.get(productId) : null;
                return (
                  <TableRow key={device.id} hover>
                    <TableCell>
                      <Typography variant="body2">{device.device_name}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {device.device_identifier}
                      </Typography>
                    </TableCell>
                    <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                      <Typography variant="body2">{vendorById.get(device.vendor_id)?.name ?? "—"}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {modelById.get(device.device_model_id)?.name ?? "—"}
                      </Typography>
                    </TableCell>
                    <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>
                      {storeById.get(device.store_id)?.name ?? "—"}
                    </TableCell>
                    <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                      {product ? `${product.product_name} (${product.sku})` : "—"}
                    </TableCell>
                    <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>
                      <Stack direction="row" spacing={0.5} alignItems="center">
                        <BatteryFullIcon fontSize="small" />
                        <span>{device.battery_level ?? "—"}%</span>
                      </Stack>
                      <Stack direction="row" spacing={0.5} alignItems="center">
                        <SignalCellularAltIcon fontSize="small" />
                        <span>{device.signal_strength ?? "—"}%</span>
                      </Stack>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={device.status}
                        size="small"
                        color={DEVICE_STATUS_COLORS[device.status] ?? "default"}
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell sx={{ display: { xs: "none", lg: "table-cell" } }}>
                      {device.last_sync_at ? new Date(device.last_sync_at).toLocaleString() : "Never"}
                    </TableCell>
                    <TableCell align="right" sx={{ whiteSpace: "nowrap" }}>
                      <Tooltip title="View">
                        <IconButton size="small" onClick={() => navigate(`/devices/${device.id}`)}>
                          <VisibilityIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <IconButton size="small" onClick={() => setDeletingDevice(device)}>
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                );
              })}
          </TableBody>
        </Table>
        <TablePagination
          component="div"
          count={data?.meta?.total ?? 0}
          page={page - 1}
          onPageChange={(_, newPage) => setPage(newPage + 1)}
          rowsPerPage={pageSize}
          onRowsPerPageChange={(event) => {
            setPageSize(Number(event.target.value));
            setPage(1);
          }}
          rowsPerPageOptions={[10, 20, 50]}
        />
      </TableContainer>

      {deletingDevice && (
        <DeleteDeviceDialog
          device={deletingDevice}
          onClose={() => setDeletingDevice(null)}
          onDeleted={() => {
            // Don't strand the user on an empty page after removing its last row.
            if (items.length === 1 && page > 1) setPage(page - 1);
            setDeletingDevice(null);
          }}
        />
      )}

      <Box sx={{ mt: 2 }} />
    </Container>
  );
}
