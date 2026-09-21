import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import CircularProgress from "@mui/material/CircularProgress";
import Container from "@mui/material/Container";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import { useNavigate, useParams } from "react-router-dom";

import ProductForm from "../features/products/ProductForm";
import { useProduct, useUpdateProduct } from "../features/products/hooks";

export default function ProductEditPage() {
  const { productId } = useParams();
  const navigate = useNavigate();
  const { data: product, isLoading, isError } = useProduct(productId);
  const updateProduct = useUpdateProduct(productId);

  const handleSubmit = async (values) => {
    await updateProduct.mutateAsync(values);
    navigate(`/products/${productId}`, { replace: true });
  };

  if (isLoading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (isError || !product) {
    return (
      <Container sx={{ py: 4 }}>
        <Alert severity="error">Product not found.</Alert>
      </Container>
    );
  }

  // MUI/react-hook-form need "" for an empty controlled field; the API
  // returns null for unset optional columns, and Decimal fields come back
  // as strings already (e.g. "19.9900"), which TextField wants anyway.
  const defaultValues = Object.fromEntries(
    Object.entries(product).map(([key, value]) => [key, value === null ? "" : value])
  );

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Edit Product
      </Typography>
      <Paper variant="outlined" sx={{ p: 3, mt: 2 }}>
        <ProductForm defaultValues={defaultValues} onSubmit={handleSubmit} submitLabel="Save Changes" />
      </Paper>
    </Container>
  );
}
