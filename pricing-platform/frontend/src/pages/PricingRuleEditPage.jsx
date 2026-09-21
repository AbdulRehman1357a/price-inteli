import { useQueries } from "@tanstack/react-query";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import Container from "@mui/material/Container";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { Link as RouterLink, useNavigate, useParams } from "react-router-dom";

import { useAllCategories } from "../features/categories/hooks";
import { fetchProduct } from "../features/products/api";
import RuleForm, { ruleToFormValues } from "../features/pricing/RuleForm";
import { useRule, useUpdateRule } from "../features/pricing/hooks";
import { useAllStores } from "../features/stores/hooks";

export default function PricingRuleEditPage() {
  const { ruleId } = useParams();
  const navigate = useNavigate();
  const { data: rule, isLoading: isRuleLoading, isError } = useRule(ruleId);
  const { data: categories, isLoading: isCategoriesLoading } = useAllCategories();
  const { data: stores, isLoading: isStoresLoading } = useAllStores();
  const updateRule = useUpdateRule(ruleId);

  const productIds = rule?.conditions_json?.product_ids ?? [];
  const productQueries = useQueries({
    queries: productIds.map((id) => ({
      queryKey: ["products", "detail", id],
      queryFn: () => fetchProduct(id),
    })),
  });
  const products = productQueries.map((q) => q.data).filter(Boolean);
  const isProductsLoading = productQueries.some((q) => q.isLoading);

  const isLoading = isRuleLoading || isCategoriesLoading || isStoresLoading || isProductsLoading;

  const handleSubmit = async (payload) => {
    await updateRule.mutateAsync(payload);
    navigate("/pricing/rules", { replace: true });
  };

  if (isLoading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (isError || !rule) {
    return (
      <Container sx={{ py: 4 }}>
        <Alert severity="error">Pricing rule not found.</Alert>
      </Container>
    );
  }

  const defaultValues = ruleToFormValues(rule, { categories, stores, products });

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
        <Typography variant="h4" component="h1">
          Edit Pricing Rule
        </Typography>
        <Button variant="outlined" component={RouterLink} to={`/pricing/rules/${ruleId}/test`}>
          Test This Rule
        </Button>
      </Stack>
      <Paper variant="outlined" sx={{ p: 3, mt: 2 }}>
        <RuleForm defaultValues={defaultValues} onSubmit={handleSubmit} submitLabel="Save Changes" />
      </Paper>
    </Container>
  );
}
