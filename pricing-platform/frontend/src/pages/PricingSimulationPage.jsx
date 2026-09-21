import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import Accordion from "@mui/material/Accordion";
import AccordionDetails from "@mui/material/AccordionDetails";
import AccordionSummary from "@mui/material/AccordionSummary";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import Grid from "@mui/material/Grid";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useState } from "react";

import { useRunSimulation } from "../features/pricing/hooks";
import ProductSelect from "../features/products/ProductSelect";
import StoreSelect from "../features/stores/StoreSelect";

const RISK_COLORS = { low: "success", medium: "warning", high: "error" };

function formatMoney(value) {
  if (value === null || value === undefined) return "—";
  return `$${Number(value).toFixed(2)}`;
}

function formatPercent(value) {
  if (value === null || value === undefined) return "—";
  const n = Number(value);
  return `${n > 0 ? "+" : ""}${n.toFixed(2)}%`;
}

function ScenarioTable({ title, scenario }) {
  return (
    <Paper variant="outlined" sx={{ p: 2, flex: 1 }}>
      <Typography variant="subtitle2" gutterBottom>
        {title}
      </Typography>
      <Table size="small">
        <TableBody>
          <TableRow>
            <TableCell>Price</TableCell>
            <TableCell align="right">{formatMoney(scenario.price)}</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Estimated Unit Sales</TableCell>
            <TableCell align="right">{Number(scenario.estimated_unit_sales).toFixed(1)}</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Revenue</TableCell>
            <TableCell align="right">{formatMoney(scenario.revenue)}</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Gross Margin</TableCell>
            <TableCell align="right">
              {scenario.gross_margin !== null ? formatMoney(scenario.gross_margin) : "Unknown (no cost)"}
            </TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Margin %</TableCell>
            <TableCell align="right">
              {scenario.gross_margin_percent !== null ? `${scenario.gross_margin_percent}%` : "—"}
            </TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Inventory Days</TableCell>
            <TableCell align="right">
              {scenario.inventory_days !== null ? scenario.inventory_days : "—"}
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </Paper>
  );
}

export default function PricingSimulationPage() {
  const [productId, setProductId] = useState("");
  const [storeId, setStoreId] = useState("");
  const [currentPrice, setCurrentPrice] = useState("");
  const [proposedPrice, setProposedPrice] = useState("");
  const [expectedDemandChangePercent, setExpectedDemandChangePercent] = useState("");
  const [cost, setCost] = useState("");
  const [inventoryQuantity, setInventoryQuantity] = useState("");
  const [formError, setFormError] = useState(null);

  const runSimulation = useRunSimulation();
  const result = runSimulation.data;

  const handleSubmit = async () => {
    setFormError(null);
    if (!productId || !proposedPrice) {
      setFormError("Select a product and enter a proposed price.");
      return;
    }
    try {
      await runSimulation.mutateAsync({
        productId,
        storeId: storeId || undefined,
        currentPrice: currentPrice || undefined,
        proposedPrice,
        expectedDemandChangePercent: expectedDemandChangePercent || undefined,
        cost: cost || undefined,
        inventoryQuantity: inventoryQuantity || undefined,
      });
    } catch (error) {
      setFormError(error.response?.data?.error?.message ?? "Unable to run this simulation.");
    }
  };

  return (
    <Box sx={{ py: 4, px: { xs: 2, md: 4 } }}>
      <Typography variant="h4" component="h1" gutterBottom>
        What-If Pricing Simulation
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        A deterministic estimate — nothing here changes a real price. Use the AI Pricing or Pricing Rules
        screens to act on a decision.
      </Typography>

      <Paper variant="outlined" sx={{ p: 3, mb: 3 }}>
        {formError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {formError}
          </Alert>
        )}
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={3}>
            <ProductSelect value={productId} onChange={setProductId} required />
          </Grid>
          <Grid item xs={12} sm={3}>
            <StoreSelect value={storeId} onChange={setStoreId} label="Store (optional)" />
          </Grid>
          <Grid item xs={12} sm={2}>
            <TextField
              label="Current Price"
              type="number"
              fullWidth
              value={currentPrice}
              onChange={(e) => setCurrentPrice(e.target.value)}
              helperText="Blank = today's price"
            />
          </Grid>
          <Grid item xs={12} sm={2}>
            <TextField
              label="Proposed Price"
              type="number"
              required
              fullWidth
              value={proposedPrice}
              onChange={(e) => setProposedPrice(e.target.value)}
            />
          </Grid>
          <Grid item xs={12} sm={2}>
            <Button
              variant="contained"
              fullWidth
              onClick={handleSubmit}
              disabled={runSimulation.isPending}
              sx={{ height: "100%" }}
            >
              {runSimulation.isPending ? "Running..." : "Run Simulation"}
            </Button>
          </Grid>
        </Grid>

        <Accordion variant="outlined" sx={{ mt: 2 }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="body2">Advanced (optional overrides)</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={4}>
                <TextField
                  label="Expected Demand Change (%)"
                  type="number"
                  fullWidth
                  value={expectedDemandChangePercent}
                  onChange={(e) => setExpectedDemandChangePercent(e.target.value)}
                  helperText="Blank = deterministic elasticity estimate"
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField
                  label="Cost"
                  type="number"
                  fullWidth
                  value={cost}
                  onChange={(e) => setCost(e.target.value)}
                  helperText="Blank = product's cost price"
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField
                  label="Inventory Quantity"
                  type="number"
                  fullWidth
                  value={inventoryQuantity}
                  onChange={(e) => setInventoryQuantity(e.target.value)}
                  helperText="Blank = current available stock"
                />
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>
      </Paper>

      {result && (
        <>
          <Stack direction={{ xs: "column", md: "row" }} spacing={2} sx={{ mb: 3 }}>
            <ScenarioTable title="Current Scenario" scenario={result.current_scenario} />
            <ScenarioTable title="Proposed Scenario" scenario={result.proposed_scenario} />
          </Stack>

          <Paper variant="outlined" sx={{ p: 3, mb: 3 }}>
            <Typography variant="subtitle1" gutterBottom>
              Difference
            </Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell />
                    <TableCell align="right">Change</TableCell>
                    <TableCell align="right">% Change</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>Revenue</TableCell>
                    <TableCell align="right">{formatMoney(result.revenue_change)}</TableCell>
                    <TableCell align="right">{formatPercent(result.revenue_change_percent)}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Gross Margin</TableCell>
                    <TableCell align="right">
                      {result.margin_change !== null ? formatMoney(result.margin_change) : "Unknown"}
                    </TableCell>
                    <TableCell align="right">
                      {result.margin_change_percent_points !== null
                        ? `${formatPercent(result.margin_change_percent_points)} pts`
                        : "—"}
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>

          <Paper variant="outlined" sx={{ p: 3 }}>
            <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 1 }}>
              <Typography variant="subtitle1">Recommendation</Typography>
              <Chip
                label={`${result.risk_level} risk (${result.risk_score})`}
                size="small"
                color={RISK_COLORS[result.risk_level] ?? "default"}
              />
            </Stack>
            <Typography sx={{ mb: 2 }}>{result.recommendation}</Typography>
            {result.assumptions.demand_change_defaulted && (
              <Alert severity="info">
                No demand-change estimate was provided, so a default price-elasticity assumption (
                {result.assumptions.default_elasticity_used}) was used — this lowers confidence in the
                result. Provide your own estimate in Advanced for a more reliable simulation.
              </Alert>
            )}
          </Paper>
        </>
      )}
    </Box>
  );
}
