import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
import HistoryIcon from "@mui/icons-material/History";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Container from "@mui/material/Container";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogContentText from "@mui/material/DialogContentText";
import DialogTitle from "@mui/material/DialogTitle";
import IconButton from "@mui/material/IconButton";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import { useState } from "react";
import { Link as RouterLink, useNavigate } from "react-router-dom";

import { useAgents, useDeleteAgent, usePolicies, useRunAgent } from "../features/agents/hooks";
import { AGENT_TYPE_OPTIONS, IMPLEMENTED_AGENT_TYPES } from "../features/agents/options";
import { useAuth } from "../features/auth/AuthContext";

function typeLabel(agentType) {
  return AGENT_TYPE_OPTIONS.find((o) => o.value === agentType)?.label ?? agentType;
}

export default function AgentsListPage() {
  const navigate = useNavigate();
  const { hasPermission } = useAuth();
  const { data: agents, isLoading, isError } = useAgents();
  const { data: policies } = usePolicies();
  const deleteAgent = useDeleteAgent();
  const runAgent = useRunAgent();
  const [agentToDelete, setAgentToDelete] = useState(null);
  const [runFeedback, setRunFeedback] = useState(null);

  const canManage = hasPermission("ai_recommendations.apply");
  const canRun = hasPermission("ai_recommendations.create");

  const policyByType = new Map((policies ?? []).map((p) => [p.agent_type, p]));

  const handleRun = async (agent) => {
    setRunFeedback(null);
    try {
      await runAgent.mutateAsync(agent.id);
      setRunFeedback({ severity: "success", message: `${agent.name} started running.` });
    } catch (error) {
      setRunFeedback({
        severity: "error",
        message: error.response?.data?.error?.message ?? "Unable to run this agent.",
      });
    }
  };

  const handleConfirmDelete = async () => {
    if (!agentToDelete) return;
    try {
      await deleteAgent.mutateAsync(agentToDelete.id);
      setAgentToDelete(null);
    } catch (error) {
      setRunFeedback({
        severity: "error",
        message: error.response?.data?.error?.message ?? "Unable to delete this agent.",
      });
      setAgentToDelete(null);
    }
  };

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
          AI Agents
        </Typography>
        {canManage && (
          <Button variant="contained" component={RouterLink} to="/ai-agents/new">
            New Agent
          </Button>
        )}
      </Stack>

      {runFeedback && (
        <Alert severity={runFeedback.severity} sx={{ mb: 2 }} onClose={() => setRunFeedback(null)}>
          {runFeedback.message}
        </Alert>
      )}
      {isError && <Alert severity="error">Unable to load agents.</Alert>}

      <TableContainer component={Paper} variant="outlined">
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Agent Name</TableCell>
              <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>Agent Type</TableCell>
              <TableCell>Status</TableCell>
              <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>Execution Mode</TableCell>
              <TableCell align="right" sx={{ display: { xs: "none", sm: "table-cell" } }}>
                Confidence
              </TableCell>
              <TableCell align="right" sx={{ display: { xs: "none", md: "table-cell" } }}>
                Max Price Change
              </TableCell>
              <TableCell align="right" sx={{ display: { xs: "none", md: "table-cell" } }}>
                Min Margin
              </TableCell>
              <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Approval Required</TableCell>
              <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Schedule</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading && (
              <TableRow>
                <TableCell colSpan={10} align="center" sx={{ py: 6 }}>
                  <CircularProgress size={28} />
                </TableCell>
              </TableRow>
            )}

            {!isLoading && (agents ?? []).length === 0 && (
              <TableRow>
                <TableCell colSpan={10} align="center" sx={{ py: 6 }}>
                  <Typography color="text.secondary">No agents configured yet.</Typography>
                </TableCell>
              </TableRow>
            )}

            {!isLoading &&
              (agents ?? []).map((agent) => {
                const policy = policyByType.get(agent.agent_type);
                const implemented = IMPLEMENTED_AGENT_TYPES.has(agent.agent_type);
                return (
                  <TableRow key={agent.id} hover>
                    <TableCell>{agent.name}</TableCell>
                    <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>
                      {typeLabel(agent.agent_type)}
                      {!implemented && (
                        <Chip label="Not implemented" size="small" sx={{ ml: 1 }} variant="outlined" />
                      )}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={agent.status}
                        size="small"
                        color={agent.status === "active" ? "success" : "default"}
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>
                      {policy?.mode ?? "—"}
                    </TableCell>
                    <TableCell align="right" sx={{ display: { xs: "none", sm: "table-cell" } }}>
                      {policy ? Number(policy.min_confidence).toFixed(2) : "—"}
                    </TableCell>
                    <TableCell align="right" sx={{ display: { xs: "none", md: "table-cell" } }}>
                      {policy ? `${Number(policy.max_price_change_percent).toFixed(1)}%` : "—"}
                    </TableCell>
                    <TableCell align="right" sx={{ display: { xs: "none", md: "table-cell" } }}>
                      {policy ? `${Number(policy.min_margin_percent).toFixed(1)}%` : "—"}
                    </TableCell>
                    <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                      {policy?.approval_required ? "Yes" : "No"}
                    </TableCell>
                    <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                      {agent.configuration?.schedule ?? "manual"}
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title={implemented ? "Run now" : "Not implemented yet"}>
                        <span>
                          <IconButton
                            size="small"
                            disabled={!canRun || !implemented || agent.status !== "active"}
                            onClick={() => handleRun(agent)}
                          >
                            <PlayArrowIcon fontSize="small" />
                          </IconButton>
                        </span>
                      </Tooltip>
                      <Tooltip title="Run history">
                        <IconButton size="small" onClick={() => navigate(`/ai-agents/${agent.id}/runs`)}>
                          <HistoryIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Edit">
                        <span>
                          <IconButton
                            size="small"
                            disabled={!canManage}
                            onClick={() => navigate(`/ai-agents/${agent.id}/edit`)}
                          >
                            <EditIcon fontSize="small" />
                          </IconButton>
                        </span>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <span>
                          <IconButton
                            size="small"
                            disabled={!canManage}
                            onClick={() => setAgentToDelete(agent)}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </span>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                );
              })}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={Boolean(agentToDelete)} onClose={() => setAgentToDelete(null)}>
        <DialogTitle>Delete agent</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Delete <strong>{agentToDelete?.name}</strong>? Agents with run history can't be deleted —
            set them to inactive instead.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAgentToDelete(null)}>Cancel</Button>
          <Button color="error" onClick={handleConfirmDelete} disabled={deleteAgent.isPending}>
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
