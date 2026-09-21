import Container from "@mui/material/Container";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import { useNavigate } from "react-router-dom";

import RoutingRuleForm from "../features/outputs/RoutingRuleForm";
import { useCreateRoutingRule } from "../features/outputs/hooks";

export default function OutputRoutingRuleCreatePage() {
  const navigate = useNavigate();
  const createRule = useCreateRoutingRule();

  const handleSubmit = async (payload) => {
    const rule = await createRule.mutateAsync(payload);
    navigate(`/outputs/routing-rules/${rule.id}/edit`, { replace: true });
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        New Output Routing Rule
      </Typography>
      <Paper variant="outlined" sx={{ p: 3, mt: 2 }}>
        <RoutingRuleForm onSubmit={handleSubmit} submitLabel="Create Rule" />
      </Paper>
    </Container>
  );
}
