import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Container from "@mui/material/Container";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Typography from "@mui/material/Typography";
import { Link as RouterLink } from "react-router-dom";

import { useDashboard } from "../features/competitors/hooks";
import { POSITION_COLORS, POSITION_LABELS } from "../features/competitors/options";

function formatMoney(value, currency = "USD") {
  if (value === null || value === undefined) return "—";
  try {
    return new Intl.NumberFormat(undefined, { style: "currency", currency }).format(Number(value));
  } catch {
    return `$${Number(value).toFixed(2)}`;
  }
}

export default function CompetitorPricingDashboardPage() {
  const { data: rows, isLoading, isError } = useDashboard();

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Stack
        direction={{ xs: "column", sm: "row" }}
        justifyContent="space-between"
        alignItems={{ xs: "flex-start", sm: "center" }}
        spacing={2}
        sx={{ mb: 3 }}
      >
        <Typography variant="h4" component="h1">
          Competitor Pricing Dashboard
        </Typography>
        <Button variant="outlined" component={RouterLink} to="/competitors">
          Manage Competitors
        </Button>
      </Stack>

      {isError && <Alert severity="error">Unable to load the competitor dashboard.</Alert>}

      <TableContainer component={Paper} variant="outlined">
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Product</TableCell>
              <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>Competitor</TableCell>
              <TableCell align="right" sx={{ display: { xs: "none", sm: "table-cell" } }}>
                Our Price
              </TableCell>
              <TableCell align="right" sx={{ display: { xs: "none", sm: "table-cell" } }}>
                Competitor Price
              </TableCell>
              <TableCell align="right">Gap</TableCell>
              <TableCell>Position</TableCell>
              <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Availability</TableCell>
              <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Captured At</TableCell>
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

            {!isLoading && (rows ?? []).length === 0 && (
              <TableRow>
                <TableCell colSpan={8} align="center" sx={{ py: 6 }}>
                  <Typography color="text.secondary">
                    No tracked competitor products yet — add one from Manage Competitors.
                  </Typography>
                </TableCell>
              </TableRow>
            )}

            {!isLoading &&
              (rows ?? []).map((row) => (
                <TableRow key={row.competitor_product_id} hover>
                  <TableCell>
                    {row.product_name} ({row.sku})
                  </TableCell>
                  <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>
                    {row.competitor_name}
                  </TableCell>
                  <TableCell align="right" sx={{ display: { xs: "none", sm: "table-cell" } }}>
                    {formatMoney(row.our_price, row.our_currency)}
                  </TableCell>
                  <TableCell align="right" sx={{ display: { xs: "none", sm: "table-cell" } }}>
                    {formatMoney(row.competitor_price, row.competitor_currency)}
                  </TableCell>
                  <TableCell align="right">
                    {row.price_gap !== null ? formatMoney(row.price_gap, row.our_currency) : "—"}
                    {row.price_gap_percent !== null && (
                      <Typography variant="caption" color="text.secondary" display="block">
                        {row.price_gap_percent}%
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={POSITION_LABELS[row.position] ?? row.position}
                      size="small"
                      color={POSITION_COLORS[row.position] ?? "default"}
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                    {row.competitor_availability ?? "—"}
                  </TableCell>
                  <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                    {row.captured_at ? new Date(row.captured_at).toLocaleString() : "—"}
                  </TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Container>
  );
}
