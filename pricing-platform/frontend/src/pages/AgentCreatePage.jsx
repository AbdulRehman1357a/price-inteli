import Container from "@mui/material/Container";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import { useNavigate } from "react-router-dom";

import AgentForm from "../features/agents/AgentForm";
import { useCreateAgent } from "../features/agents/hooks";

function toConfiguration(values) {
  return {
    scope: values.scope,
    category_id: values.scope === "category" && values.categoryId ? values.categoryId : null,
    store_id: values.storeId || null,
    product_ids: values.scope === "products" ? values.productIds : null,
    max_products_per_run: values.maxProductsPerRun,
    schedule: values.schedule,
  };
}

export default function AgentCreatePage() {
  const navigate = useNavigate();
  const createAgent = useCreateAgent();

  const handleSubmit = async (values) => {
    await createAgent.mutateAsync({
      agent_type: values.agentType,
      name: values.name,
      status: values.status,
      configuration: toConfiguration(values),
    });
    navigate("/ai-agents", { replace: true });
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        New Agent
      </Typography>
      <Paper variant="outlined" sx={{ p: 3, mt: 2 }}>
        <AgentForm mode="create" onSubmitAgent={handleSubmit} submitLabel="Create Agent" />
      </Paper>
    </Container>
  );
}
