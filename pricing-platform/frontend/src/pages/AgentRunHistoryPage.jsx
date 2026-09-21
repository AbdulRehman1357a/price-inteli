import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import Accordion from "@mui/material/Accordion";
import AccordionDetails from "@mui/material/AccordionDetails";
import AccordionSummary from "@mui/material/AccordionSummary";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Container from "@mui/material/Container";
import Divider from "@mui/material/Divider";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Typography from "@mui/material/Typography";
import { useParams } from "react-router-dom";

import { useAgent, useRuns } from "../features/agents/hooks";
import { AGENT_RUN_STATUS_COLORS, RUN_ACTION_LABELS } from "../features/agents/options";

function RunItem({ item }) {
  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
        <Typography variant="subtitle2">
          {item.product_name} ({item.sku})
        </Typography>
        <Chip label={RUN_ACTION_LABELS[item.action] ?? item.action} size="small" />
      </Stack>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        {item.reasoning_summary}
      </Typography>
      <Grid2>
        <Field label="Current Price" value={`$${item.recommendation?.current_price}`} />
        <Field label="Recommended Price" value={`$${item.recommendation?.recommended_price}`} />
        <Field label="Confidence" value={item.recommendation?.confidence_score} />
      </Grid2>
      {item.guardrail_result && (
        <Box sx={{ mt: 1 }}>
          <Typography variant="caption" color="text.secondary" display="block">
            Guardrail Result
          </Typography>
          <Typography variant="body2">
            {item.guardrail_result.passed ? "Passed without adjustment" : "Adjusted"}
            {item.guardrail_result.notes?.length > 0 && ` — ${item.guardrail_result.notes.join("; ")}`}
          </Typography>
        </Box>
      )}
      {item.execution_result && (
        <Box sx={{ mt: 1 }}>
          <Typography variant="caption" color="text.secondary" display="block">
            Execution Result
          </Typography>
          <Typography variant="body2">
            {item.execution_result.applied
              ? `Applied — new price $${item.execution_result.selling_price}`
              : `Not executed — ${item.execution_result.reason ?? "left pending for review"}`}
          </Typography>
        </Box>
      )}
    </Paper>
  );
}

function Grid2({ children }) {
  return (
    <Stack direction="row" spacing={3} flexWrap="wrap" useFlexGap sx={{ mb: 1 }}>
      {children}
    </Stack>
  );
}

function Field({ label, value }) {
  return (
    <Box>
      <Typography variant="caption" color="text.secondary" display="block">
        {label}
      </Typography>
      <Typography variant="body2">{value ?? "—"}</Typography>
    </Box>
  );
}

export default function AgentRunHistoryPage() {
  const { agentId } = useParams();
  const { data: agent } = useAgent(agentId);
  const { data, isLoading, isError } = useRuns({ agentId, page: 1, pageSize: 20 });

  const runs = data?.items ?? [];

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Run History{agent ? ` — ${agent.name}` : ""}
      </Typography>

      {isLoading && (
        <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
          <CircularProgress />
        </Box>
      )}
      {isError && <Alert severity="error">Unable to load run history.</Alert>}
      {!isLoading && runs.length === 0 && (
        <Alert severity="info">No runs yet — use "Run now" on the Agents screen.</Alert>
      )}

      {runs.map((run) => (
        <Accordion key={run.id} variant="outlined" disableGutters sx={{ mb: 1 }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Stack
              direction="row"
              spacing={2}
              alignItems="center"
              flexWrap="wrap"
              useFlexGap
              sx={{ width: "100%" }}
            >
              <Chip
                label={run.status}
                size="small"
                color={AGENT_RUN_STATUS_COLORS[run.status] ?? "default"}
                variant="outlined"
              />
              <Typography variant="body2">{new Date(run.started_at).toLocaleString()}</Typography>
              <Typography variant="caption" color="text.secondary">
                {run.trigger_type}
              </Typography>
              {run.output && (
                <Typography variant="caption" color="text.secondary" sx={{ ml: "auto", mr: 2 }}>
                  {run.output.candidates_evaluated} evaluated · {run.output.recommendations_created} created ·{" "}
                  {run.output.auto_applied} auto-applied
                </Typography>
              )}
            </Stack>
          </AccordionSummary>
          <AccordionDetails>
            {run.status === "failed" && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {run.error_message}
              </Alert>
            )}

            <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
              Inputs (policy at run time)
            </Typography>
            <TableContainer sx={{ mb: 2 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Mode</TableCell>
                    <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Min Confidence</TableCell>
                    <TableCell>Max Price Change</TableCell>
                    <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Min Margin</TableCell>
                    <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                      Approval Required
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>{run.input_snapshot?.policy?.mode}</TableCell>
                    <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                      {run.input_snapshot?.policy?.min_confidence}
                    </TableCell>
                    <TableCell>{run.input_snapshot?.policy?.max_price_change_percent}%</TableCell>
                    <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                      {run.input_snapshot?.policy?.min_margin_percent}%
                    </TableCell>
                    <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                      {run.input_snapshot?.policy?.approval_required ? "Yes" : "No"}
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>

            {run.output?.items?.length > 0 && (
              <Stack spacing={1.5}>
                <Divider />
                {run.output.items.map((item) => (
                  <RunItem key={item.recommendation_id ?? item.product_id} item={item} />
                ))}
              </Stack>
            )}
          </AccordionDetails>
        </Accordion>
      ))}
    </Container>
  );
}
