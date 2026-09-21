import Container from "@mui/material/Container";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import { useNavigate } from "react-router-dom";

import StoreForm from "../features/stores/StoreForm";
import { useCreateStore } from "../features/stores/hooks";

export default function StoreCreatePage() {
  const navigate = useNavigate();
  const createStore = useCreateStore();

  const handleSubmit = async (values) => {
    const store = await createStore.mutateAsync(values);
    navigate(`/stores/${store.id}`, { replace: true });
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        New Store
      </Typography>
      <Paper variant="outlined" sx={{ p: 3, mt: 2 }}>
        <StoreForm onSubmit={handleSubmit} submitLabel="Create Store" />
      </Paper>
    </Container>
  );
}
