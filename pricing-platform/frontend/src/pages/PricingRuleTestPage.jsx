import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Container from "@mui/material/Container";
import Divider from "@mui/material/Divider";
import Grid from "@mui/material/Grid";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Typography from "@mui/material/Typography";
import { useState } from "react";
import { useParams } from "react-router-dom";

import { useTestRule } from "../features/pricing/hooks";
import ProductSelect from "../features/products/ProductSelect";
import StoreSelect from "../features/stores/StoreSelect";

function money(value) {
  return `$${Number(value).toFixed(2)}`;
}

export default function PricingRuleTestPage() {
  const { ruleId } = useParams();
  const [productId, setProductId] = useState("");
  const [storeId, setStoreId] = useState("");
  const [formError, setFormError] = useState(null);
  const testRule = useTestRule(ruleId);

  const handleRun = async () => {
    setFormError(null);
    if (!productId) {
      setFormError("Select a product to test this rule against.");
      return;
    }
    try {
      await testRule.mutateAsync({ productId, storeId: storeId || undefined });
    } catch (error) {
      setFormError(error.response?.data?.error?.message ?? "Unable to run the test. Please try again.");
    }
  };

  const result = testRule.data;
  const nameById = new Map((result?.matched_rules ?? []).map((r) => [r.rule_id, r.rule_name]));

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Test Pricing Rule
      </Typography>

      <Paper variant="outlined" sx={{ p: 3, mt: 2 }}>
        <Stack spacing={2}>
          {formError && <Alert severity="error">{formError}</Alert>}
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <ProductSelect value={productId} onChange={setProductId} required label="Product" />
            </Grid>
            <Grid item xs={12} sm={6}>
              <StoreSelect value={storeId} onChange={setStoreId} label="Store (optional)" />
            </Grid>
          </Grid>
          <Box>
            <Button variant="contained" onClick={handleRun} disabled={testRule.isPending}>
              {testRule.isPending ? "Running…" : "Run Test"}
            </Button>
          </Box>
        </Stack>
      </Paper>

      {testRule.isPending && (
        <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {result && (
        <Stack spacing={3} sx={{ mt: 3 }}>
          <Paper variant="outlined" sx={{ p: 3 }}>
            <Grid container spacing={2}>
              <Grid item xs={6} sm={3}>
                <Typography variant="caption" color="text.secondary">
                  Current Price
                </Typography>
                <Typography variant="h6">{money(result.current_price)}</Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="caption" color="text.secondary">
                  Calculated Price
                </Typography>
                <Typography variant="h6">{money(result.calculated_price)}</Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="caption" color="text.secondary">
                  Final Price
                </Typography>
                <Typography variant="h6" color="primary">
                  {money(result.final_price)}
                </Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="caption" color="text.secondary">
                  Approval Required
                </Typography>
                <Box>
                  <Chip
                    size="small"
                    label={result.approval_required ? "Yes" : "No"}
                    color={result.approval_required ? "warning" : "success"}
                  />
                </Box>
              </Grid>
            </Grid>
          </Paper>

          <Paper variant="outlined" sx={{ p: 3 }}>
            <Typography variant="subtitle1" gutterBottom>
              Matched Rules &amp; Execution Order
            </Typography>
            {result.matched_rules.length === 0 ? (
              <Typography color="text.secondary">No rules matched this product/store.</Typography>
            ) : (
              <>
                <Stack direction="row" spacing={1} sx={{ mb: 2, flexWrap: "wrap", gap: 1 }}>
                  {result.rule_execution_order.map((ruleIdInOrder, index) => (
                    <Chip
                      key={ruleIdInOrder}
                      size="small"
                      label={`${index + 1}. ${nameById.get(ruleIdInOrder) ?? ruleIdInOrder}`}
                    />
                  ))}
                </Stack>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Rule</TableCell>
                        <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>Type</TableCell>
                        <TableCell align="right" sx={{ display: { xs: "none", md: "table-cell" } }}>
                          Priority
                        </TableCell>
                        <TableCell align="right" sx={{ display: { xs: "none", sm: "table-cell" } }}>
                          Before
                        </TableCell>
                        <TableCell align="right" sx={{ display: { xs: "none", sm: "table-cell" } }}>
                          After Action
                        </TableCell>
                        <TableCell align="right">After Constraints</TableCell>
                        <TableCell>Approval</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {result.matched_rules.map((trace) => (
                        <TableRow key={trace.rule_id}>
                          <TableCell>{trace.rule_name}</TableCell>
                          <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>
                            {trace.rule_type}
                          </TableCell>
                          <TableCell align="right" sx={{ display: { xs: "none", md: "table-cell" } }}>
                            {trace.priority}
                          </TableCell>
                          <TableCell align="right" sx={{ display: { xs: "none", sm: "table-cell" } }}>
                            {money(trace.price_before)}
                          </TableCell>
                          <TableCell align="right" sx={{ display: { xs: "none", sm: "table-cell" } }}>
                            {money(trace.price_after_action)}
                          </TableCell>
                          <TableCell align="right">{money(trace.price_after_constraints)}</TableCell>
                          <TableCell>{trace.approval_required ? "Yes" : "No"}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </>
            )}
          </Paper>

          <Paper variant="outlined" sx={{ p: 3 }}>
            <Typography variant="subtitle1" gutterBottom>
              Constraint Validation
            </Typography>
            {result.constraint_validation.length === 0 ? (
              <Typography color="text.secondary">No constraints were applied.</Typography>
            ) : (
              <List dense disablePadding>
                {result.constraint_validation.map((note, index) => (
                  <ListItem key={index} disableGutters divider={index < result.constraint_validation.length - 1}>
                    <ListItemText primary={note} />
                  </ListItem>
                ))}
              </List>
            )}
          </Paper>

          <Divider />
        </Stack>
      )}
    </Container>
  );
}
