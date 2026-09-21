import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Container from "@mui/material/Container";
import Grid from "@mui/material/Grid";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TablePagination from "@mui/material/TablePagination";
import TableRow from "@mui/material/TableRow";
import Tab from "@mui/material/Tab";
import Tabs from "@mui/material/Tabs";
import Typography from "@mui/material/Typography";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../features/auth/AuthContext";
import { useGenerateRecommendation, useRecommendations, useSummary } from "../features/aiPricing/hooks";
import { RECOMMENDATION_STATUS_COLORS, formatCurrency, formatPercent } from "../features/aiPricing/options";
import ProductSelect from "../features/products/ProductSelect";
import StoreSelect from "../features/stores/StoreSelect";

const STATUS_TABS = ["all", "pending", "approved", "rejected", "applied", "expired"];

function SummaryCard({ label, value, color }) {
  return (
    <Card variant="outlined">
      <CardContent>
        <Typography variant="caption" color="text.secondary" display="block">
          {label}
        </Typography>
        <Typography variant="h5" color={color}>
          {value}
        </Typography>
      </CardContent>
    </Card>
  );
}

export default function AIPricingDashboardPage() {
  const navigate = useNavigate();
  const { hasPermission } = useAuth();
  const [tab, setTab] = useState("all");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [productId, setProductId] = useState("");
  const [storeId, setStoreId] = useState("");
  const [generateError, setGenerateError] = useState(null);

  const { data: summary } = useSummary();
  const { data, isLoading, isError } = useRecommendations({
    page,
    pageSize,
    status: tab === "all" ? undefined : tab,
  });
  const generate = useGenerateRecommendation();

  const canCreate = hasPermission("ai_recommendations.create");
  const items = data?.items ?? [];

  const handleGenerate = async () => {
    setGenerateError(null);
    if (!productId) {
      setGenerateError("Select a product first.");
      return;
    }
    try {
      const recommendation = await generate.mutateAsync({ productId, storeId: storeId || undefined });
      navigate(`/ai-pricing/${recommendation.id}`);
    } catch (error) {
      setGenerateError(error.response?.data?.error?.message ?? "Unable to generate a recommendation.");
    }
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        AI Pricing Dashboard
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Recommendation-only: nothing here changes a price automatically. Every recommendation needs an
        explicit Approve and Apply before it affects what customers see.
      </Typography>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={2.4}>
          <SummaryCard label="Pending" value={summary?.pending_count ?? "—"} color="warning.main" />
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <SummaryCard label="Approved" value={summary?.approved_count ?? "—"} color="info.main" />
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <SummaryCard label="Rejected" value={summary?.rejected_count ?? "—"} color="error.main" />
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <SummaryCard
            label="Potential Revenue Impact"
            value={summary ? formatCurrency(summary.potential_revenue_impact) : "—"}
            color="text.primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <SummaryCard
            label="Potential Margin Impact"
            value={summary ? formatCurrency(summary.potential_margin_impact) : "—"}
            color="text.primary"
          />
        </Grid>
      </Grid>

      {canCreate && (
        <Paper variant="outlined" sx={{ p: 3, mb: 3 }}>
          <Typography variant="subtitle1" gutterBottom>
            Generate Recommendation
          </Typography>
          {generateError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {generateError}
            </Alert>
          )}
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={5}>
              <ProductSelect value={productId} onChange={setProductId} required />
            </Grid>
            <Grid item xs={12} sm={4}>
              <StoreSelect value={storeId} onChange={setStoreId} label="Store (optional)" />
            </Grid>
            <Grid item xs={12} sm={3}>
              <Button variant="contained" onClick={handleGenerate} disabled={generate.isPending} fullWidth>
                {generate.isPending ? "Generating..." : "Generate"}
              </Button>
            </Grid>
          </Grid>
        </Paper>
      )}

      <Tabs
        value={tab}
        onChange={(_, newValue) => {
          setTab(newValue);
          setPage(1);
        }}
        variant="scrollable"
        scrollButtons="auto"
        sx={{ mb: 2 }}
      >
        {STATUS_TABS.map((status) => (
          <Tab key={status} value={status} label={status === "all" ? "All" : status} />
        ))}
      </Tabs>

      {isError && <Alert severity="error">Unable to load recommendations.</Alert>}

      <TableContainer component={Paper} variant="outlined">
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Product</TableCell>
              <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>Store</TableCell>
              <TableCell align="right" sx={{ display: { xs: "none", sm: "table-cell" } }}>
                Current Price
              </TableCell>
              <TableCell align="right">Recommended Price</TableCell>
              <TableCell align="right" sx={{ display: { xs: "none", sm: "table-cell" } }}>
                Difference
              </TableCell>
              <TableCell align="right" sx={{ display: { xs: "none", md: "table-cell" } }}>
                Confidence
              </TableCell>
              <TableCell>Status</TableCell>
              <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Created At</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading && (
              <TableRow>
                <TableCell colSpan={8} align="center" sx={{ py: 6 }}>
                  <CircularProgress size={28} />
                </TableCell>
              </TableRow>
            )}

            {!isLoading && items.length === 0 && (
              <TableRow>
                <TableCell colSpan={8} align="center" sx={{ py: 6 }}>
                  <Typography color="text.secondary">No recommendations found.</Typography>
                </TableCell>
              </TableRow>
            )}

            {!isLoading &&
              items.map((r) => (
                <TableRow key={r.id} hover sx={{ cursor: "pointer" }} onClick={() => navigate(`/ai-pricing/${r.id}`)}>
                  <TableCell>
                    {r.product_name} ({r.sku})
                  </TableCell>
                  <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>
                    {r.store_name ?? "All stores"}
                  </TableCell>
                  <TableCell align="right" sx={{ display: { xs: "none", sm: "table-cell" } }}>
                    {formatCurrency(r.current_price)}
                  </TableCell>
                  <TableCell align="right">{formatCurrency(r.recommended_price)}</TableCell>
                  <TableCell align="right" sx={{ display: { xs: "none", sm: "table-cell" } }}>
                    {formatPercent(r.price_difference_percentage)}
                  </TableCell>
                  <TableCell align="right" sx={{ display: { xs: "none", md: "table-cell" } }}>
                    {(Number(r.confidence_score) * 100).toFixed(0)}%
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={r.status}
                      size="small"
                      color={RECOMMENDATION_STATUS_COLORS[r.status] ?? "default"}
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                    {new Date(r.created_at).toLocaleString()}
                  </TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
        <TablePagination
          component="div"
          count={data?.meta?.total ?? 0}
          page={page - 1}
          onPageChange={(_, newPage) => setPage(newPage + 1)}
          rowsPerPage={pageSize}
          onRowsPerPageChange={(event) => {
            setPageSize(Number(event.target.value));
            setPage(1);
          }}
          rowsPerPageOptions={[10, 20, 50]}
        />
      </TableContainer>
    </Container>
  );
}
