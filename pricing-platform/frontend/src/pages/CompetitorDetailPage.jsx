import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import RefreshIcon from "@mui/icons-material/Refresh";
import Accordion from "@mui/material/Accordion";
import AccordionDetails from "@mui/material/AccordionDetails";
import AccordionSummary from "@mui/material/AccordionSummary";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Container from "@mui/material/Container";
import Grid from "@mui/material/Grid";
import IconButton from "@mui/material/IconButton";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import TextField from "@mui/material/TextField";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import { useState } from "react";
import { useParams } from "react-router-dom";

import { useAuth } from "../features/auth/AuthContext";
import {
  useAddCompetitorProduct,
  useCompetitor,
  useCompetitorProducts,
  usePrices,
  useRecordManualPrice,
  useSyncPrice,
} from "../features/competitors/hooks";
import ProductSelect from "../features/products/ProductSelect";

function PriceHistory({ competitorProductId }) {
  const { data: prices, isLoading } = usePrices(competitorProductId);

  if (isLoading) return <CircularProgress size={20} />;
  if (!prices || prices.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        No price observations yet.
      </Typography>
    );
  }

  return (
    <TableContainer>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Captured At</TableCell>
            <TableCell align="right">Price</TableCell>
            <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Availability</TableCell>
            <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Source</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {prices.map((p) => (
            <TableRow key={p.id}>
              <TableCell>{new Date(p.captured_at).toLocaleString()}</TableCell>
              <TableCell align="right">
                {p.currency} {p.price}
              </TableCell>
              <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                {p.availability ?? "—"}
              </TableCell>
              <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>{p.source}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

function TrackedProductRow({ competitorId, cp, canManage }) {
  const [price, setPrice] = useState("");
  const [availability, setAvailability] = useState("");
  const [error, setError] = useState(null);
  const recordManualPrice = useRecordManualPrice(competitorId);
  const syncPrice = useSyncPrice(competitorId);

  const handleRecord = async () => {
    setError(null);
    if (!price) {
      setError("Enter a price.");
      return;
    }
    try {
      await recordManualPrice.mutateAsync({
        competitorProductId: cp.id,
        payload: { price, availability: availability || undefined },
      });
      setPrice("");
      setAvailability("");
    } catch (err) {
      setError(err.response?.data?.error?.message ?? "Unable to record this price.");
    }
  };

  const handleSync = async () => {
    setError(null);
    try {
      await syncPrice.mutateAsync(cp.id);
    } catch (err) {
      setError(err.response?.data?.error?.message ?? "Unable to sync from the configured API.");
    }
  };

  return (
    <Accordion variant="outlined" disableGutters>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Stack direction="row" spacing={2} alignItems="center" sx={{ width: "100%" }}>
          <Typography sx={{ flexGrow: 1 }}>
            {cp.product_name} ({cp.sku})
          </Typography>
          {cp.latest_price && (
            <Chip
              label={`${cp.latest_price_currency} ${cp.latest_price}`}
              size="small"
              variant="outlined"
            />
          )}
          <Chip label={cp.status} size="small" />
        </Stack>
      </AccordionSummary>
      <AccordionDetails>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        {cp.external_product_url && (
          <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
            {cp.external_product_url}
          </Typography>
        )}

        {canManage && (
          <Grid container spacing={1} alignItems="center" sx={{ mb: 2 }}>
            <Grid item xs={12} sm={3}>
              <TextField
                label="Record Price"
                type="number"
                size="small"
                fullWidth
                value={price}
                onChange={(e) => setPrice(e.target.value)}
              />
            </Grid>
            <Grid item xs={12} sm={3}>
              <TextField
                label="Availability"
                size="small"
                fullWidth
                value={availability}
                onChange={(e) => setAvailability(e.target.value)}
              />
            </Grid>
            <Grid item xs={12} sm={3}>
              <Button size="small" variant="contained" onClick={handleRecord} disabled={recordManualPrice.isPending}>
                Record Manually
              </Button>
            </Grid>
            <Grid item xs={12} sm={3}>
              <Tooltip title={cp.external_product_url ? "Sync from configured API" : "No API URL configured"}>
                <span>
                  <Button
                    size="small"
                    startIcon={<RefreshIcon />}
                    onClick={handleSync}
                    disabled={!cp.external_product_url || syncPrice.isPending}
                  >
                    Sync from API
                  </Button>
                </span>
              </Tooltip>
            </Grid>
          </Grid>
        )}

        <PriceHistory competitorProductId={cp.id} />
      </AccordionDetails>
    </Accordion>
  );
}

export default function CompetitorDetailPage() {
  const { competitorId } = useParams();
  const { hasPermission } = useAuth();
  const { data: competitor } = useCompetitor(competitorId);
  const { data: products, isLoading } = useCompetitorProducts(competitorId);
  const addProduct = useAddCompetitorProduct(competitorId);
  const [productId, setProductId] = useState("");
  const [externalUrl, setExternalUrl] = useState("");
  const [addError, setAddError] = useState(null);

  const canManage = hasPermission("pricing.update");
  const canCreate = hasPermission("pricing.create");

  const handleAdd = async () => {
    setAddError(null);
    if (!productId) {
      setAddError("Select a product first.");
      return;
    }
    try {
      await addProduct.mutateAsync({ productId, externalProductUrl: externalUrl || undefined });
      setProductId("");
      setExternalUrl("");
    } catch (error) {
      setAddError(error.response?.data?.error?.message ?? "Unable to track this product.");
    }
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        {competitor ? competitor.name : "Competitor"}
      </Typography>

      {canCreate && (
        <Paper variant="outlined" sx={{ p: 3, mb: 3 }}>
          <Typography variant="subtitle1" gutterBottom>
            Track a Product
          </Typography>
          {addError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {addError}
            </Alert>
          )}
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={5}>
              <ProductSelect value={productId} onChange={setProductId} required />
            </Grid>
            <Grid item xs={12} sm={5}>
              <TextField
                label="External Product URL (optional — enables API sync)"
                fullWidth
                value={externalUrl}
                onChange={(e) => setExternalUrl(e.target.value)}
              />
            </Grid>
            <Grid item xs={12} sm={2}>
              <Button variant="contained" fullWidth onClick={handleAdd} disabled={addProduct.isPending}>
                Track
              </Button>
            </Grid>
          </Grid>
        </Paper>
      )}

      {isLoading && (
        <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {!isLoading && (products ?? []).length === 0 && (
        <Alert severity="info">No products tracked for this competitor yet.</Alert>
      )}

      <Stack spacing={1}>
        {(products ?? []).map((cp) => (
          <TrackedProductRow key={cp.id} competitorId={competitorId} cp={cp} canManage={canManage} />
        ))}
      </Stack>
    </Container>
  );
}
