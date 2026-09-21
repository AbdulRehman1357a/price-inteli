import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Container from "@mui/material/Container";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogContentText from "@mui/material/DialogContentText";
import DialogTitle from "@mui/material/DialogTitle";
import Grid from "@mui/material/Grid";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { useDeleteStore, useStore } from "../features/stores/hooks";

const STATUS_COLORS = { active: "success", inactive: "default", closed: "error" };

function Field({ label, value }) {
  return (
    <Grid item xs={12} sm={6}>
      <Typography variant="caption" color="text.secondary" display="block">
        {label}
      </Typography>
      <Typography>{value || "—"}</Typography>
    </Grid>
  );
}

export default function StoreDetailsPage() {
  const { storeId } = useParams();
  const navigate = useNavigate();
  const { data: store, isLoading, isError } = useStore(storeId);
  const deleteStore = useDeleteStore();
  const [confirmOpen, setConfirmOpen] = useState(false);

  const handleDelete = async () => {
    await deleteStore.mutateAsync(storeId);
    navigate("/stores", { replace: true });
  };

  if (isLoading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (isError || !store) {
    return (
      <Container sx={{ py: 4 }}>
        <Alert severity="error">Store not found.</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
        <Stack direction="row" spacing={2} alignItems="center">
          <Typography variant="h4" component="h1">
            {store.name}
          </Typography>
          <Chip
            label={store.status}
            color={STATUS_COLORS[store.status] ?? "default"}
            variant="outlined"
          />
        </Stack>
        <Stack direction="row" spacing={1}>
          <Button variant="outlined" onClick={() => navigate(`/stores/${storeId}/edit`)}>
            Edit
          </Button>
          <Button variant="outlined" color="error" onClick={() => setConfirmOpen(true)}>
            Delete
          </Button>
        </Stack>
      </Stack>

      <Card variant="outlined">
        <CardContent>
          <Typography variant="subtitle1" gutterBottom>
            Identity
          </Typography>
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Field label="Store Code" value={store.store_code} />
            <Field label="Legal Name" value={store.legal_name} />
            <Field label="Store Type" value={store.store_type} />
            <Field label="Opening Date" value={store.opening_date} />
          </Grid>

          <Typography variant="subtitle1" gutterBottom>
            Contact
          </Typography>
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Field label="Email" value={store.email} />
            <Field label="Phone" value={store.phone} />
          </Grid>

          <Typography variant="subtitle1" gutterBottom>
            Address
          </Typography>
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Field label="Address Line 1" value={store.address_line_1} />
            <Field label="Address Line 2" value={store.address_line_2} />
            <Field label="City" value={store.city} />
            <Field label="State / Province" value={store.state} />
            <Field label="Country" value={store.country} />
            <Field label="Postal Code" value={store.postal_code} />
          </Grid>

          <Typography variant="subtitle1" gutterBottom>
            Operations
          </Typography>
          <Grid container spacing={2}>
            <Field label="Timezone" value={store.timezone} />
            <Field label="Currency" value={store.currency} />
            <Field label="Created" value={new Date(store.created_at).toLocaleString()} />
            <Field label="Last Updated" value={new Date(store.updated_at).toLocaleString()} />
          </Grid>
        </CardContent>
      </Card>

      <Dialog open={confirmOpen} onClose={() => setConfirmOpen(false)}>
        <DialogTitle>Delete store</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Delete <strong>{store.name}</strong> ({store.store_code})? This can't be undone from here.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmOpen(false)}>Cancel</Button>
          <Button color="error" onClick={handleDelete} disabled={deleteStore.isPending}>
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
