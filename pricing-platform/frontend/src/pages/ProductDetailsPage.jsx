import InventoryIcon from "@mui/icons-material/Inventory2";
import Alert from "@mui/material/Alert";
import Avatar from "@mui/material/Avatar";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Container from "@mui/material/Container";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogContentText from "@mui/material/DialogContentText";
import DialogTitle from "@mui/material/DialogTitle";
import Grid from "@mui/material/Grid";
import Stack from "@mui/material/Stack";
import Link from "@mui/material/Link";
import Typography from "@mui/material/Typography";
import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { useCategory } from "../features/categories/hooks";
import { useDeleteProduct, useProduct } from "../features/products/hooks";

const STATUS_COLORS = { active: "success", inactive: "default", discontinued: "error" };

function Field({ label, value }) {
  return (
    <Grid item xs={12} sm={6}>
      <Typography variant="caption" color="text.secondary" display="block">
        {label}
      </Typography>
      <Typography>{value || "—"}</Typography>
    </Grid>
  );
}

export default function ProductDetailsPage() {
  const { productId } = useParams();
  const navigate = useNavigate();
  const { data: product, isLoading, isError } = useProduct(productId);
  const { data: category } = useCategory(product?.category_id);
  const deleteProduct = useDeleteProduct();
  const [confirmOpen, setConfirmOpen] = useState(false);

  const handleDelete = async () => {
    await deleteProduct.mutateAsync(productId);
    navigate("/products", { replace: true });
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

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Stack
        direction={{ xs: "column", sm: "row" }}
        justifyContent="space-between"
        alignItems={{ xs: "flex-start", sm: "center" }}
        spacing={2}
        sx={{ mb: 3 }}
      >
        <Stack direction="row" spacing={2} alignItems="center">
          <Avatar src={product.product_image_url || undefined} variant="rounded" sx={{ width: 56, height: 56 }}>
            <InventoryIcon />
          </Avatar>
          <Stack>
            <Typography variant="h4" component="h1">
              {product.product_name}
            </Typography>
            <Chip
              label={product.status}
              size="small"
              color={STATUS_COLORS[product.status] ?? "default"}
              variant="outlined"
              sx={{ width: "fit-content" }}
            />
          </Stack>
        </Stack>
        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
          <Button variant="outlined" onClick={() => navigate(`/products/${productId}/edit`)}>
            Edit
          </Button>
          <Button variant="outlined" color="error" onClick={() => setConfirmOpen(true)}>
            Delete
          </Button>
        </Stack>
      </Stack>

      <Card variant="outlined">
        <CardContent>
          <Typography variant="subtitle1" gutterBottom>
            Basic Information
          </Typography>
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Field label="SKU" value={product.sku} />
            <Field label="Barcode" value={product.barcode} />
            <Field label="Category" value={category?.name} />
            <Field label="Brand" value={product.brand} />
            <Field label="Manufacturer" value={product.manufacturer} />
            <Grid item xs={12} sm={6}>
              <Typography variant="caption" color="text.secondary" display="block">
                Product URL
              </Typography>
              {product.product_url ? (
                <Link href={product.product_url} target="_blank" rel="noopener noreferrer">
                  {product.product_url}
                </Link>
              ) : (
                <Typography>—</Typography>
              )}
            </Grid>
            <Field label="QR ID" value={product.qr_id} />
            <Field label="Shelf ID" value={product.shelf_id} />
          </Grid>

          <Typography variant="subtitle1" gutterBottom>
            Pricing
          </Typography>
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Field label="Cost Price" value={product.cost_price} />
            <Field label="Base Price" value={product.base_price} />
            <Field label="Selling Price" value={product.selling_price} />
            <Field label="Currency" value={product.currency} />
            <Field label="Tax Rate" value={product.tax_rate} />
          </Grid>

          <Typography variant="subtitle1" gutterBottom>
            Additional Details
          </Typography>
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Field label="Short Description" value={product.short_description} />
            <Field label="Weight" value={product.weight ? `${product.weight} ${product.weight_unit ?? ""}` : null} />
          </Grid>
          {product.description && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="caption" color="text.secondary" display="block">
                Full Description
              </Typography>
              <Typography sx={{ whiteSpace: "pre-wrap" }}>{product.description}</Typography>
            </Box>
          )}

          <Typography variant="subtitle1" gutterBottom>
            Record
          </Typography>
          <Grid container spacing={2}>
            <Field label="Created" value={new Date(product.created_at).toLocaleString()} />
            <Field label="Last Updated" value={new Date(product.updated_at).toLocaleString()} />
          </Grid>
        </CardContent>
      </Card>

      <Dialog open={confirmOpen} onClose={() => setConfirmOpen(false)}>
        <DialogTitle>Delete product</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Delete <strong>{product.product_name}</strong> ({product.sku})? This can't be undone from
            here.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmOpen(false)}>Cancel</Button>
          <Button color="error" onClick={handleDelete} disabled={deleteProduct.isPending}>
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
