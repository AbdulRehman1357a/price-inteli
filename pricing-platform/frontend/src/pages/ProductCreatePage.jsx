import Container from "@mui/material/Container";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import { useNavigate } from "react-router-dom";

import ProductForm from "../features/products/ProductForm";
import { useCreateProduct } from "../features/products/hooks";

export default function ProductCreatePage() {
  const navigate = useNavigate();
  const createProduct = useCreateProduct();

  const handleSubmit = async (values) => {
    const product = await createProduct.mutateAsync(values);
    navigate(`/products/${product.id}`, { replace: true });
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        New Product
      </Typography>
      <Paper variant="outlined" sx={{ p: 3, mt: 2 }}>
        <ProductForm onSubmit={handleSubmit} submitLabel="Create Product" />
      </Paper>
    </Container>
  );
}
