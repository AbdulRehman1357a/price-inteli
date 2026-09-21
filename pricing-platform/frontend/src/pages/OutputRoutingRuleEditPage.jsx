import { useQueries } from "@tanstack/react-query";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import CircularProgress from "@mui/material/CircularProgress";
import Container from "@mui/material/Container";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import { useNavigate, useParams } from "react-router-dom";

import { useAllCategories } from "../features/categories/hooks";
import RoutingRuleForm, { routingRuleToFormValues } from "../features/outputs/RoutingRuleForm";
import { useRoutingRule, useUpdateRoutingRule } from "../features/outputs/hooks";
import { fetchProduct } from "../features/products/api";
import { useAllStores } from "../features/stores/hooks";

export default function OutputRoutingRuleEditPage() {
  const { ruleId } = useParams();
  const navigate = useNavigate();
  const { data: rule, isLoading: isRuleLoading, isError } = useRoutingRule(ruleId);
  const { data: categories, isLoading: isCategoriesLoading } = useAllCategories();
  const { data: stores, isLoading: isStoresLoading } = useAllStores();
  const updateRule = useUpdateRoutingRule(ruleId);

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
    navigate("/outputs/routing-rules", { replace: true });
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
        <Alert severity="error">Output routing rule not found.</Alert>
      </Container>
    );
  }

  const defaultValues = routingRuleToFormValues(rule, { categories, stores, products });

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Edit Output Routing Rule
      </Typography>
      <Paper variant="outlined" sx={{ p: 3, mt: 2 }}>
        <RoutingRuleForm defaultValues={defaultValues} onSubmit={handleSubmit} submitLabel="Save Changes" />
      </Paper>
    </Container>
  );
}
