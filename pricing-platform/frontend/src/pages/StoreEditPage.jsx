import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import CircularProgress from "@mui/material/CircularProgress";
import Container from "@mui/material/Container";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import { useNavigate, useParams } from "react-router-dom";

import StoreForm from "../features/stores/StoreForm";
import { useStore, useUpdateStore } from "../features/stores/hooks";

export default function StoreEditPage() {
  const { storeId } = useParams();
  const navigate = useNavigate();
  const { data: store, isLoading, isError } = useStore(storeId);
  const updateStore = useUpdateStore(storeId);

  const handleSubmit = async (values) => {
    await updateStore.mutateAsync(values);
    navigate(`/stores/${storeId}`, { replace: true });
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

  // MUI/react-hook-form need "" for an empty controlled field; the API
  // returns null for unset optional columns.
  const defaultValues = Object.fromEntries(
    Object.entries(store).map(([key, value]) => [key, value === null ? "" : value])
  );

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Edit Store
      </Typography>
      <Paper variant="outlined" sx={{ p: 3, mt: 2 }}>
        <StoreForm defaultValues={defaultValues} onSubmit={handleSubmit} submitLabel="Save Changes" />
      </Paper>
    </Container>
  );
}
