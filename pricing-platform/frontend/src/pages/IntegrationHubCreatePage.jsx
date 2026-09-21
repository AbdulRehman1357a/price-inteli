import Container from "@mui/material/Container";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import { useNavigate } from "react-router-dom";

import IntegrationForm from "../features/integrationHub/IntegrationForm";
import { useCreateIntegration } from "../features/integrationHub/hooks";

export default function IntegrationHubCreatePage() {
  const navigate = useNavigate();
  const createIntegration = useCreateIntegration();

  const handleSubmit = async (payload) => {
    const integration = await createIntegration.mutateAsync(payload);
    navigate(`/integration-hub/${integration.id}`, { replace: true });
  };

  return (
    <Container maxWidth="sm" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        New Integration
      </Typography>
      <Paper variant="outlined" sx={{ p: 3, mt: 2 }}>
        <IntegrationForm onSubmit={handleSubmit} submitLabel="Create Integration" isCreate />
      </Paper>
    </Container>
  );
}
