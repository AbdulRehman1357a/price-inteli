import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import CircularProgress from "@mui/material/CircularProgress";
import Container from "@mui/material/Container";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import { useNavigate, useParams } from "react-router-dom";

import AgentForm from "../features/agents/AgentForm";
import { useAgent, usePolicies, useUpdateAgent } from "../features/agents/hooks";

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

export default function AgentEditPage() {
  const { agentId } = useParams();
  const navigate = useNavigate();
  const { data: agent, isLoading: isAgentLoading, isError } = useAgent(agentId);
  const { data: policies, isLoading: isPoliciesLoading } = usePolicies();
  const updateAgent = useUpdateAgent(agentId);

  const handleSubmit = async (values) => {
    await updateAgent.mutateAsync({
      name: values.name,
      status: values.status,
      configuration: toConfiguration(values),
    });
    navigate("/ai-agents", { replace: true });
  };

  if (isAgentLoading || isPoliciesLoading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (isError || !agent) {
    return (
      <Container sx={{ py: 4 }}>
        <Alert severity="error">Agent not found.</Alert>
      </Container>
    );
  }

  const policy = (policies ?? []).find((p) => p.agent_type === agent.agent_type);
  const config = agent.configuration || {};
  const defaultValues = {
    name: agent.name,
    agentType: agent.agent_type,
    status: agent.status,
    schedule: config.schedule ?? "manual",
    scope: config.scope ?? "all",
    categoryId: config.category_id ?? "",
    storeId: config.store_id ?? "",
    productIds: config.product_ids ?? [],
    maxProductsPerRun: config.max_products_per_run ?? 50,
    mode: policy?.mode ?? "recommendation_only",
    minConfidence: policy ? Number(policy.min_confidence) : 0.7,
    maxPriceChangePercent: policy ? Number(policy.max_price_change_percent) : 10,
    minMarginPercent: policy ? Number(policy.min_margin_percent) : 15,
    approvalRequired: policy ? policy.approval_required : true,
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Edit Agent
      </Typography>
      <Paper variant="outlined" sx={{ p: 3, mt: 2 }}>
        <AgentForm mode="edit" defaultValues={defaultValues} onSubmitAgent={handleSubmit} submitLabel="Save Changes" />
      </Paper>
    </Container>
  );
}
