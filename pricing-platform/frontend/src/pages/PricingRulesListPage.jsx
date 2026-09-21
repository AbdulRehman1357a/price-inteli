import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import EditIcon from "@mui/icons-material/Edit";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Container from "@mui/material/Container";
import IconButton from "@mui/material/IconButton";
import MenuItem from "@mui/material/MenuItem";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TablePagination from "@mui/material/TablePagination";
import TableRow from "@mui/material/TableRow";
import TextField from "@mui/material/TextField";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import { useState } from "react";
import { Link as RouterLink, useNavigate } from "react-router-dom";

import { useRules } from "../features/pricing/hooks";
import { RULE_STATUS_OPTIONS, RULE_TYPE_OPTIONS } from "../features/pricing/options";

const STATUS_COLORS = { draft: "default", active: "success", inactive: "warning", expired: "error" };

const ruleTypeLabel = (value) => RULE_TYPE_OPTIONS.find((o) => o.value === value)?.label ?? value;

export default function PricingRulesListPage() {
  const navigate = useNavigate();
  const [ruleType, setRuleType] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const { data, isLoading, isError } = useRules({ page, pageSize, ruleType, status });

  return (
    <Container sx={{ py: 4 }}>
      <Stack
        direction={{ xs: "column", sm: "row" }}
        justifyContent="space-between"
        alignItems={{ xs: "flex-start", sm: "center" }}
        spacing={2}
        sx={{ mb: 3 }}
      >
        <Typography variant="h4" component="h1">
          Pricing Rules
        </Typography>
        <Button variant="contained" component={RouterLink} to="/pricing/rules/new">
          New Rule
        </Button>
      </Stack>

      <Stack direction={{ xs: "column", sm: "row" }} spacing={2} sx={{ mb: 2 }}>
        <TextField
          select
          label="Rule Type"
          value={ruleType}
          onChange={(event) => {
            setRuleType(event.target.value);
            setPage(1);
          }}
          sx={{ minWidth: { xs: "100%", sm: 200 } }}
        >
          <MenuItem value="">All types</MenuItem>
          {RULE_TYPE_OPTIONS.map((option) => (
            <MenuItem key={option.value} value={option.value}>
              {option.label}
            </MenuItem>
          ))}
        </TextField>
        <TextField
          select
          label="Status"
          value={status}
          onChange={(event) => {
            setStatus(event.target.value);
            setPage(1);
          }}
          sx={{ minWidth: { xs: "100%", sm: 160 } }}
        >
          <MenuItem value="">All statuses</MenuItem>
          {RULE_STATUS_OPTIONS.map((option) => (
            <MenuItem key={option} value={option}>
              {option}
            </MenuItem>
          ))}
        </TextField>
      </Stack>

      {isError && <Alert severity="error">Unable to load pricing rules.</Alert>}

      <TableContainer component={Paper} variant="outlined">
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Rule Name</TableCell>
              <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>Rule Type</TableCell>
              <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>Priority</TableCell>
              <TableCell>Status</TableCell>
              <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Approval Required</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading && (
              <TableRow>
                <TableCell colSpan={6} align="center" sx={{ py: 6 }}>
                  <CircularProgress size={28} />
                </TableCell>
              </TableRow>
            )}

            {!isLoading && data?.items.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} align="center" sx={{ py: 6 }}>
                  <Typography color="text.secondary">No pricing rules found.</Typography>
                </TableCell>
              </TableRow>
            )}

            {!isLoading &&
              data?.items.map((rule) => (
                <TableRow key={rule.id} hover>
                  <TableCell>{rule.name}</TableCell>
                  <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>
                    {ruleTypeLabel(rule.rule_type)}
                  </TableCell>
                  <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>{rule.priority}</TableCell>
                  <TableCell>
                    <Chip
                      label={rule.status}
                      size="small"
                      color={STATUS_COLORS[rule.status] ?? "default"}
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                    {rule.approval_required ? "Yes" : "No"}
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title="Test">
                      <IconButton size="small" onClick={() => navigate(`/pricing/rules/${rule.id}/test`)}>
                        <PlayArrowIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Edit">
                      <IconButton size="small" onClick={() => navigate(`/pricing/rules/${rule.id}/edit`)}>
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
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

      <Box sx={{ mt: 2 }} />
    </Container>
  );
}
