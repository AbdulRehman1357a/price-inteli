import AddIcon from "@mui/icons-material/Add";
import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
import VisibilityIcon from "@mui/icons-material/Visibility";
import Alert from "@mui/material/Alert";
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
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import { useState } from "react";
import { Link as RouterLink, useNavigate } from "react-router-dom";

import DeviceManageDialog from "../features/devices/DeviceManageDialog";
import { useVendors } from "../features/devices/hooks";
import AddDeviceDialog from "../features/integrations/AddDeviceDialog";
import EditIntegrationDialog from "../features/integrations/EditIntegrationDialog";
import { useDeleteIntegration, useIntegrations } from "../features/integrations/hooks";
import { INTEGRATION_STATUS_COLORS } from "../features/integrations/options";
import { useAllStores } from "../features/stores/hooks";

function DeleteIntegrationDialog({ integration, onClose }) {
  const deleteIntegration = useDeleteIntegration();
  const [formError, setFormError] = useState(null);

  const handleDelete = async () => {
    setFormError(null);
    try {
      await deleteIntegration.mutateAsync(integration.id);
      onClose();
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

export default function IntegrationsListPage() {
  const navigate = useNavigate();
  const { data, isLoading, isError } = useIntegrations({ page: 1, pageSize: 50 });
  const { data: vendors } = useVendors();
  const { data: stores } = useAllStores();
  const vendorById = new Map((vendors ?? []).map((v) => [v.id, v]));
  const storeById = new Map((stores ?? []).map((s) => [s.id, s]));

  const [addingDeviceTo, setAddingDeviceTo] = useState(null);
  const [managingDevice, setManagingDevice] = useState(null);
  const [notice, setNotice] = useState(null);
  const [editingIntegration, setEditingIntegration] = useState(null);
  const [deletingIntegration, setDeletingIntegration] = useState(null);

  return (
    <Container sx={{ py: 4 }}>
      <Stack
        direction={{ xs: "column", sm: "row" }}
        justifyContent="space-between"
        alignItems={{ xs: "flex-start", sm: "center" }}
        spacing={2}
        sx={{ mb: 3 }}
      >
        <Typography variant="h4" component="h1">
          ESL Integrations
        </Typography>
        <Button variant="contained" component={RouterLink} to="/integrations/new">
          New Integration
        </Button>
      </Stack>

      {isError && <Alert severity="error">Unable to load integrations.</Alert>}
      {notice && (
        <Alert severity="success" onClose={() => setNotice(null)} sx={{ mb: 2 }}>
          {notice}
        </Alert>
      )}

      <TableContainer component={Paper} variant="outlined">
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>Vendor</TableCell>
              <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Store</TableCell>
              <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>Type</TableCell>
              <TableCell>Status</TableCell>
              <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Last Sync</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading && (
              <TableRow>
                <TableCell colSpan={7} align="center" sx={{ py: 6 }}>
                  <CircularProgress size={28} />
                </TableCell>
              </TableRow>
            )}

            {!isLoading && (data?.items.length ?? 0) === 0 && (
              <TableRow>
                <TableCell colSpan={7} align="center" sx={{ py: 6 }}>
                  <Typography color="text.secondary">No integrations configured yet.</Typography>
                </TableCell>
              </TableRow>
            )}

            {!isLoading &&
              data?.items.map((integration) => (
                <TableRow key={integration.id} hover>
                  <TableCell>{integration.name}</TableCell>
                  <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>
                    {vendorById.get(integration.vendor_id)?.name ?? "—"}
                  </TableCell>
                  <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                    {storeById.get(integration.store_id)?.name ?? "—"}
                  </TableCell>
                  <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>
                    {integration.integration_type}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={integration.status}
                      size="small"
                      color={INTEGRATION_STATUS_COLORS[integration.status] ?? "default"}
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                    {integration.last_sync_at ? new Date(integration.last_sync_at).toLocaleString() : "Never"}
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title="View">
                      <IconButton size="small" onClick={() => navigate(`/integrations/${integration.id}`)}>
                        <VisibilityIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Add Devices">
                      <IconButton size="small" onClick={() => setAddingDeviceTo(integration)}>
                        <AddIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Edit">
                      <IconButton size="small" onClick={() => setEditingIntegration(integration)}>
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete">
                      <IconButton size="small" onClick={() => setDeletingIntegration(integration)}>
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
      </TableContainer>

      {addingDeviceTo && (
        <AddDeviceDialog
          integration={addingDeviceTo}
          vendor={vendorById.get(addingDeviceTo.vendor_id)}
          store={storeById.get(addingDeviceTo.store_id)}
          onClose={() => setAddingDeviceTo(null)}
          onCreated={(device) => {
            setNotice(`Added "${device.device_name}" to ${addingDeviceTo.name}.`);
            setManagingDevice(device);
          }}
        />
      )}

      {managingDevice && (
        <DeviceManageDialog device={managingDevice} onClose={() => setManagingDevice(null)} />
      )}

      {editingIntegration && (
        <EditIntegrationDialog
          integration={editingIntegration}
          vendorCode={vendorById.get(editingIntegration.vendor_id)?.code}
          onClose={() => setEditingIntegration(null)}
        />
      )}

      {deletingIntegration && (
        <DeleteIntegrationDialog
          integration={deletingIntegration}
          onClose={() => setDeletingIntegration(null)}
        />
      )}
    </Container>
  );
}
