import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import MenuItem from "@mui/material/MenuItem";
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

import { useReconciliation, useResolveReconciliation, useRunReconciliation } from "./hooks";
import { RECONCILIATION_STATUS_COLORS } from "./options";

export default function ReconciliationTable({ integrationId }) {
  const [entityType, setEntityType] = useState("price");
  const [runError, setRunError] = useState(null);
  const { data, isLoading } = useReconciliation(integrationId, { page: 1, pageSize: 20 });
  const runReconciliation = useRunReconciliation(integrationId);
  const resolveReconciliation = useResolveReconciliation(integrationId);

  const handleRun = async () => {
    setRunError(null);
    try {
      await runReconciliation.mutateAsync(entityType);
    } catch (error) {
      setRunError(error.response?.data?.error?.message ?? "Unable to run reconciliation.");
    }
  };

  return (
    <Stack spacing={2}>
      <Paper variant="outlined" sx={{ p: 2 }}>
        <Stack direction={{ xs: "column", sm: "row" }} spacing={2} alignItems={{ xs: "stretch", sm: "center" }}>
          <TextField
            select
            label="Entity Type"
            value={entityType}
            onChange={(event) => setEntityType(event.target.value)}
            sx={{ minWidth: { xs: "100%", sm: 160 } }}
          >
            <MenuItem value="price">price</MenuItem>
            <MenuItem value="inventory">inventory</MenuItem>
          </TextField>
          <Button variant="contained" onClick={handleRun} disabled={runReconciliation.isPending}>
            {runReconciliation.isPending ? "Comparing…" : "Run Reconciliation"}
          </Button>
        </Stack>
        <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 1 }}>
          Compares PIP's current price/inventory against what this integration last synced. Only
          price and inventory support an automatic comparison in this build.
        </Typography>
        {runError && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {runError}
          </Alert>
        )}
      </Paper>

      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>Entity</TableCell>
              <TableCell>Reference</TableCell>
              <TableCell>PIP Value</TableCell>
              <TableCell>External Value</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {!isLoading && (data?.items.length ?? 0) === 0 && (
              <TableRow>
                <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                  <Typography color="text.secondary">No mismatches recorded.</Typography>
                </TableCell>
              </TableRow>
            )}
            {(data?.items ?? []).map((row) => (
              <TableRow key={row.id}>
                <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>{row.entity_type}</TableCell>
                <TableCell>{row.external_id}</TableCell>
                <TableCell>{row.pip_value ?? "—"}</TableCell>
                <TableCell>{row.external_value ?? "—"}</TableCell>
                <TableCell>
                  <Chip
                    label={row.status}
                    size="small"
                    color={RECONCILIATION_STATUS_COLORS[row.status] ?? "default"}
                    variant="outlined"
                  />
                </TableCell>
                <TableCell align="right">
                  {row.status === "open" && (
                    <Stack direction="row" spacing={1} justifyContent="flex-end">
                      <Button
                        size="small"
                        onClick={() =>
                          resolveReconciliation.mutate({ reconciliationId: row.id, resolution: "keep_pip" })
                        }
                      >
                        Keep PIP
                      </Button>
                      <Button
                        size="small"
                        onClick={() =>
                          resolveReconciliation.mutate({
                            reconciliationId: row.id,
                            resolution: "apply_external",
                          })
                        }
                      >
                        Apply External
                      </Button>
                    </Stack>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Stack>
  );
}
