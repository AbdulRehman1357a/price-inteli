import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Container from "@mui/material/Container";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
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
import { useNavigate, useParams } from "react-router-dom";

import {
  useApplyRecommendation,
  useApproveRecommendation,
  useModifyRecommendation,
  useRecommendation,
  useRejectRecommendation,
} from "../features/aiPricing/hooks";
import { RECOMMENDATION_STATUS_COLORS, formatCurrency, formatPercent } from "../features/aiPricing/options";
import { useAuth } from "../features/auth/AuthContext";

function Field({ label, value }) {
  return (
    <Grid item xs={12} sm={6} md={4}>
      <Typography variant="caption" color="text.secondary" display="block">
        {label}
      </Typography>
      <Typography>{value ?? "—"}</Typography>
    </Grid>
  );
}

function Section({ title, children }) {
  return (
    <Paper variant="outlined" sx={{ p: 3, mb: 3 }}>
      <Typography variant="subtitle1" gutterBottom>
        {title}
      </Typography>
      {children}
    </Paper>
  );
}

export default function AIPricingRecommendationDetailPage() {
  const { recommendationId } = useParams();
  const navigate = useNavigate();
  const { hasPermission } = useAuth();
  const { data: r, isLoading, isError } = useRecommendation(recommendationId);
  const approve = useApproveRecommendation();
  const reject = useRejectRecommendation();
  const apply = useApplyRecommendation();
  const modify = useModifyRecommendation();
  const [actionError, setActionError] = useState(null);
  const [modifyOpen, setModifyOpen] = useState(false);
  const [modifyPrice, setModifyPrice] = useState("");

  if (isLoading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (isError || !r) {
    return (
      <Container sx={{ py: 4 }}>
        <Alert severity="error">Recommendation not found.</Alert>
      </Container>
    );
  }

  const snapshot = r.input_snapshot || {};
  const guardrail = snapshot.guardrail || {};
  const manualModification = snapshot.manual_modification;
  const expectedImpact = snapshot.expected_impact || {};
  const inventory = snapshot.inventory || {};
  const salesHistory = snapshot.sales_history || {};
  const rules = snapshot.existing_pricing_rules || [];
  const ruleConstraints = snapshot.rule_constraints || {};

  const canReview = hasPermission("ai_recommendations.review") && r.status === "pending";
  const canApply = hasPermission("ai_recommendations.apply") && r.status === "approved";

  const runAction = async (mutation, arg) => {
    setActionError(null);
    try {
      await mutation.mutateAsync(arg);
    } catch (error) {
      setActionError(error.response?.data?.error?.message ?? "That action could not be completed.");
    }
  };

  const openModify = () => {
    setModifyPrice(r.recommended_price);
    setModifyOpen(true);
  };

  const handleModifySubmit = async () => {
    setActionError(null);
    try {
      await modify.mutateAsync({ recommendationId: r.id, recommendedPrice: modifyPrice });
      setModifyOpen(false);
    } catch (error) {
      setActionError(error.response?.data?.error?.message ?? "Unable to modify this recommendation.");
    }
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Stack
        direction={{ xs: "column", sm: "row" }}
        justifyContent="space-between"
        alignItems={{ xs: "flex-start", sm: "center" }}
        spacing={2}
        sx={{ mb: 3 }}
      >
        <Typography variant="h4" component="h1">
          Recommendation Detail
        </Typography>
        <Chip
          label={r.status}
          color={RECOMMENDATION_STATUS_COLORS[r.status] ?? "default"}
          variant="outlined"
        />
      </Stack>

      {actionError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {actionError}
        </Alert>
      )}

      <Section title="Product Data">
        <Grid container spacing={2}>
          <Field label="Product" value={`${r.product_name} (${r.sku})`} />
          <Field label="Category" value={r.category_name} />
          <Field label="Store" value={r.store_name ?? "All stores"} />
          <Field label="Created By" value={r.created_by_agent} />
          <Field label="Created At" value={new Date(r.created_at).toLocaleString()} />
          <Field
            label="Reviewed At"
            value={r.reviewed_at ? new Date(r.reviewed_at).toLocaleString() : "Not yet reviewed"}
          />
        </Grid>
      </Section>

      <Section title="Current Pricing">
        <Grid container spacing={2}>
          <Field label="Current Price" value={formatCurrency(r.current_price)} />
          <Field label="Recommended Price" value={formatCurrency(r.recommended_price)} />
          <Field label="Difference" value={formatPercent(r.price_difference_percentage)} />
          <Field label="Current Margin" value={snapshot.current_margin_percentage ? `${snapshot.current_margin_percentage}%` : "Unknown"} />
          <Field label="Confidence" value={`${(Number(r.confidence_score) * 100).toFixed(0)}%`} />
          <Field label="Cost Price" value={snapshot.cost_price ? formatCurrency(snapshot.cost_price) : "Unknown"} />
        </Grid>
      </Section>

      <Section title="Inventory">
        <Grid container spacing={2}>
          <Field label="On Hand" value={inventory.quantity_on_hand} />
          <Field label="Available" value={inventory.quantity_available} />
          <Field label="Reorder Point" value={inventory.reorder_point ?? "Not set"} />
          <Field label="Units Sold (lookback)" value={salesHistory.units_sold} />
          <Field label="Sales Velocity" value={`${salesHistory.sales_velocity_per_day ?? 0} units/day`} />
          <Field label="Lookback Window" value={`${salesHistory.lookback_days ?? "—"} days`} />
        </Grid>
      </Section>

      <Section title="Existing Pricing Rules Considered">
        {rules.length === 0 ? (
          <Typography color="text.secondary">No in-force pricing rules matched this product.</Typography>
        ) : (
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap sx={{ mb: ruleConstraints ? 2 : 0 }}>
            {rules.map((rule) => (
              <Chip key={rule.id} label={rule.name} size="small" />
            ))}
          </Stack>
        )}
        {Object.keys(ruleConstraints).length > 0 && (
          <Typography variant="body2" color="text.secondary">
            Combined constraints: {Object.entries(ruleConstraints).map(([k, v]) => `${k}=${v}`).join(", ")}
          </Typography>
        )}
      </Section>

      <Section title="Historical Pricing">
        {r.price_history.length === 0 ? (
          <Typography color="text.secondary">No price history yet.</Typography>
        ) : (
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Date</TableCell>
                  <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>Old Price</TableCell>
                  <TableCell>New Price</TableCell>
                  <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>Source</TableCell>
                  <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Reason</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {r.price_history.map((h) => (
                  <TableRow key={h.id}>
                    <TableCell>{new Date(h.created_at).toLocaleDateString()}</TableCell>
                    <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>
                      {h.old_price ? formatCurrency(h.old_price) : "—"}
                    </TableCell>
                    <TableCell>{formatCurrency(h.new_price)}</TableCell>
                    <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>{h.source}</TableCell>
                    <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                      {h.reason ?? "—"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Section>

      <Section title="AI Explanation">
        <Typography>{r.recommendation_reason}</Typography>
      </Section>

      <Section title="Expected Impact">
        <Grid container spacing={2}>
          <Field label="Horizon" value={`${expectedImpact.horizon_days ?? "—"} days`} />
          <Field label="Projected Units" value={expectedImpact.projected_units ?? "—"} />
          <Field
            label="Revenue Impact"
            value={expectedImpact.revenue_impact ? formatCurrency(expectedImpact.revenue_impact) : "—"}
          />
          <Field
            label="Margin Impact"
            value={expectedImpact.margin_impact ? formatCurrency(expectedImpact.margin_impact) : "Unknown (no cost price)"}
          />
          <Field
            label="Recommended Margin"
            value={expectedImpact.recommended_margin_percentage ? `${expectedImpact.recommended_margin_percentage}%` : "Unknown"}
          />
        </Grid>
      </Section>

      <Section title="Guardrail Results">
        <Grid container spacing={2} sx={{ mb: 1 }}>
          <Field label="Passed Without Adjustment" value={guardrail.passed ? "Yes" : "No — adjusted"} />
          <Field label="Proposed Price" value={guardrail.proposed_price ? formatCurrency(guardrail.proposed_price) : "—"} />
          <Field label="Adjusted Price" value={guardrail.adjusted_price ? formatCurrency(guardrail.adjusted_price) : "—"} />
        </Grid>
        {guardrail.notes?.length > 0 && (
          <Stack spacing={0.5}>
            {guardrail.notes.map((note, index) => (
              <Typography key={index} variant="body2" color="text.secondary">
                • {note}
              </Typography>
            ))}
          </Stack>
        )}
        {manualModification && (
          <Alert severity="info" sx={{ mt: 2 }}>
            Manually modified to {formatCurrency(manualModification.proposed_price)}
            {manualModification.notes?.length > 0 &&
              ` — guardrail adjusted to ${formatCurrency(manualModification.adjusted_price)}: ${manualModification.notes.join("; ")}`}
          </Alert>
        )}
      </Section>

      <Paper variant="outlined" sx={{ p: 3 }}>
        <Typography variant="subtitle1" gutterBottom>
          Actions
        </Typography>
        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
          <Button
            variant="contained"
            color="success"
            disabled={!canReview || approve.isPending}
            onClick={() => runAction(approve, r.id)}
          >
            Approve
          </Button>
          <Button
            variant="outlined"
            color="error"
            disabled={!canReview || reject.isPending}
            onClick={() => runAction(reject, r.id)}
          >
            Reject
          </Button>
          <Button variant="outlined" disabled={!canReview} onClick={openModify}>
            Modify
          </Button>
          <Button
            variant="contained"
            disabled={!canApply || apply.isPending}
            onClick={() => runAction(apply, r.id)}
          >
            Apply
          </Button>
          <Button variant="text" onClick={() => navigate("/ai-pricing")}>
            Back to Dashboard
          </Button>
        </Stack>
        {r.status === "pending" && !hasPermission("ai_recommendations.review") && (
          <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
            You don't have permission to review this recommendation.
          </Typography>
        )}
      </Paper>

      <Dialog open={modifyOpen} onClose={() => setModifyOpen(false)}>
        <DialogTitle>Modify Recommended Price</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            label="New Recommended Price"
            type="number"
            value={modifyPrice}
            onChange={(event) => setModifyPrice(event.target.value)}
            fullWidth
            sx={{ mt: 1 }}
            helperText="Still validated against the same deterministic guardrails (min margin, max discount, cost floor)."
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setModifyOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleModifySubmit} disabled={modify.isPending}>
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
