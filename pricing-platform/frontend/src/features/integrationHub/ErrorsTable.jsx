import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Typography from "@mui/material/Typography";

import { useErrors, useResolveError } from "./hooks";

const SEVERITY_COLORS = { warning: "warning", error: "error", critical: "error" };

export default function ErrorsTable({ integrationId }) {
  const { data, isLoading } = useErrors(integrationId, { page: 1, pageSize: 20, isResolved: false });
  const resolveError = useResolveError(integrationId);

  return (
    <Stack spacing={2}>
      <Typography variant="body2" color="text.secondary">
        Structured, resolvable errors from sync, webhook, and outbound push runs — showing open ones
        first.
      </Typography>
      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Type</TableCell>
              <TableCell>Severity</TableCell>
              <TableCell>Message</TableCell>
              <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Occurred</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {!isLoading && (data?.items.length ?? 0) === 0 && (
              <TableRow>
                <TableCell colSpan={5} align="center" sx={{ py: 4 }}>
                  <Typography color="text.secondary">No open errors.</Typography>
                </TableCell>
              </TableRow>
            )}
            {(data?.items ?? []).map((error) => (
              <TableRow key={error.id}>
                <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>{error.error_type}</TableCell>
                <TableCell>
                  <Chip
                    label={error.severity}
                    size="small"
                    color={SEVERITY_COLORS[error.severity] ?? "default"}
                    variant="outlined"
                  />
                </TableCell>
                <TableCell>{error.message}</TableCell>
                <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                  {new Date(error.created_at).toLocaleString()}
                </TableCell>
                <TableCell align="right">
                  <Button size="small" onClick={() => resolveError.mutate(error.id)}>
                    Resolve
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Stack>
  );
}
