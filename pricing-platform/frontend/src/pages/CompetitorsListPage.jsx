import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
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
import MenuItem from "@mui/material/MenuItem";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import TextField from "@mui/material/TextField";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import { useState } from "react";
import { Link as RouterLink } from "react-router-dom";

import { useAuth } from "../features/auth/AuthContext";
import {
  useCompetitors,
  useCreateCompetitor,
  useDeleteCompetitor,
  useUpdateCompetitor,
} from "../features/competitors/hooks";
import { COMPETITOR_STATUS_OPTIONS } from "../features/competitors/options";

function CompetitorDialog({ open, onClose, competitor }) {
  const isEdit = Boolean(competitor);
  const [name, setName] = useState(competitor?.name ?? "");
  const [website, setWebsite] = useState(competitor?.website ?? "");
  const [status, setStatus] = useState(competitor?.status ?? "active");
  const [error, setError] = useState(null);
  const create = useCreateCompetitor();
  const update = useUpdateCompetitor(competitor?.id);

  const handleSave = async () => {
    setError(null);
    try {
      if (isEdit) {
        await update.mutateAsync({ name, website: website || null, status });
      } else {
        await create.mutateAsync({ name, website, status });
      }
      onClose();
    } catch (err) {
      setError(err.response?.data?.error?.message ?? "Unable to save this competitor.");
    }
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>{isEdit ? "Edit Competitor" : "New Competitor"}</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          {error && <Alert severity="error">{error}</Alert>}
          <TextField label="Name" required fullWidth value={name} onChange={(e) => setName(e.target.value)} />
          <TextField
            label="Website"
            fullWidth
            value={website}
            onChange={(e) => setWebsite(e.target.value)}
          />
          <TextField select label="Status" fullWidth value={status} onChange={(e) => setStatus(e.target.value)}>
            {COMPETITOR_STATUS_OPTIONS.map((option) => (
              <MenuItem key={option} value={option}>
                {option}
              </MenuItem>
            ))}
          </TextField>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" onClick={handleSave} disabled={!name || create.isPending || update.isPending}>
          Save
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default function CompetitorsListPage() {
  const { hasPermission } = useAuth();
  const { data: competitors, isLoading, isError } = useCompetitors();
  const deleteCompetitor = useDeleteCompetitor();
  const [dialogState, setDialogState] = useState(null); // { competitor: null|obj } when open
  const [competitorToDelete, setCompetitorToDelete] = useState(null);
  const [deleteError, setDeleteError] = useState(null);

  const canManage = hasPermission("pricing.update");
  const canCreate = hasPermission("pricing.create");

  const handleConfirmDelete = async () => {
    setDeleteError(null);
    try {
      await deleteCompetitor.mutateAsync(competitorToDelete.id);
      setCompetitorToDelete(null);
    } catch (error) {
      setDeleteError(error.response?.data?.error?.message ?? "Unable to delete this competitor.");
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Stack
        direction={{ xs: "column", sm: "row" }}
        justifyContent="space-between"
        alignItems={{ xs: "flex-start", sm: "center" }}
        spacing={2}
        sx={{ mb: 3 }}
      >
        <Typography variant="h4" component="h1">
          Competitors
        </Typography>
        {canCreate && (
          <Button variant="contained" onClick={() => setDialogState({ competitor: null })}>
            New Competitor
          </Button>
        )}
      </Stack>

      {isError && <Alert severity="error">Unable to load competitors.</Alert>}
      {deleteError && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setDeleteError(null)}>
          {deleteError}
        </Alert>
      )}

      <TableContainer component={Paper} variant="outlined">
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>Website</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading && (
              <TableRow>
                <TableCell colSpan={4} align="center" sx={{ py: 6 }}>
                  <CircularProgress size={28} />
                </TableCell>
              </TableRow>
            )}
            {!isLoading && (competitors ?? []).length === 0 && (
              <TableRow>
                <TableCell colSpan={4} align="center" sx={{ py: 6 }}>
                  <Typography color="text.secondary">No competitors yet.</Typography>
                </TableCell>
              </TableRow>
            )}
            {!isLoading &&
              (competitors ?? []).map((competitor) => (
                <TableRow key={competitor.id} hover>
                  <TableCell>
                    <RouterLink to={`/competitors/${competitor.id}`}>{competitor.name}</RouterLink>
                  </TableCell>
                  <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>
                    {competitor.website ?? "—"}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={competitor.status}
                      size="small"
                      color={competitor.status === "active" ? "success" : "default"}
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title="Edit">
                      <span>
                        <IconButton
                          size="small"
                          disabled={!canManage}
                          onClick={() => setDialogState({ competitor })}
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                      </span>
                    </Tooltip>
                    <Tooltip title="Delete">
                      <span>
                        <IconButton
                          size="small"
                          disabled={!canManage}
                          onClick={() => setCompetitorToDelete(competitor)}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </span>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
      </TableContainer>

      {dialogState && (
        <CompetitorDialog
          open
          competitor={dialogState.competitor}
          onClose={() => setDialogState(null)}
        />
      )}

      <Dialog open={Boolean(competitorToDelete)} onClose={() => setCompetitorToDelete(null)}>
        <DialogTitle>Delete competitor</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Delete <strong>{competitorToDelete?.name}</strong>? Competitors with tracked products can't be
            deleted — remove those first.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCompetitorToDelete(null)}>Cancel</Button>
          <Button color="error" onClick={handleConfirmDelete} disabled={deleteCompetitor.isPending}>
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
