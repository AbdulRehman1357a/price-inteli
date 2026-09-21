import Container from "@mui/material/Container";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import { useNavigate } from "react-router-dom";

import RuleForm from "../features/pricing/RuleForm";
import { useCreateRule } from "../features/pricing/hooks";

export default function PricingRuleCreatePage() {
  const navigate = useNavigate();
  const createRule = useCreateRule();

  const handleSubmit = async (payload) => {
    const rule = await createRule.mutateAsync(payload);
    navigate(`/pricing/rules/${rule.id}/edit`, { replace: true });
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        New Pricing Rule
      </Typography>
      <Paper variant="outlined" sx={{ p: 3, mt: 2 }}>
        <RuleForm onSubmit={handleSubmit} submitLabel="Create Rule" />
      </Paper>
    </Container>
  );
}
