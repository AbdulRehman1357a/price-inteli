import EditIcon from "@mui/icons-material/Edit";
import Alert from "@mui/material/Alert";
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

import { useRoutingRules } from "../features/outputs/hooks";
import { OUTPUT_TYPE_OPTIONS, ROUTING_RULE_STATUS_OPTIONS } from "../features/outputs/options";

const STATUS_COLORS = { active: "success", inactive: "default" };
const typeLabel = (value) => OUTPUT_TYPE_OPTIONS.find((o) => o.value === value)?.label ?? value;

export default function OutputRoutingRulesListPage() {
  const navigate = useNavigate();
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const { data, isLoading, isError } = useRoutingRules({ page, pageSize, status });

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
          Output Routing Rules
        </Typography>
        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
          <Button variant="outlined" component={RouterLink} to="/outputs/channels">
            Output Channels
          </Button>
          <Button variant="outlined" component={RouterLink} to="/outputs/jobs">
            Job Monitoring
          </Button>
          <Button variant="contained" component={RouterLink} to="/outputs/routing-rules/new">
            New Rule
          </Button>
        </Stack>
      </Stack>

      <Typography color="text.secondary" sx={{ mb: 2 }}>
        When a price is approved, matching rules automatically create output jobs on the
        target outputs below — e.g. "If Category = Grocery, Then: ESL, QR, POS".
      </Typography>

      <Stack direction={{ xs: "column", sm: "row" }} spacing={2} sx={{ mb: 2 }}>
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
          {ROUTING_RULE_STATUS_OPTIONS.map((option) => (
            <MenuItem key={option} value={option}>
              {option}
            </MenuItem>
          ))}
        </TextField>
      </Stack>

      {isError && <Alert severity="error">Unable to load routing rules.</Alert>}

      <TableContainer component={Paper} variant="outlined">
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Rule Name</TableCell>
              <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>Priority</TableCell>
              <TableCell>Target Outputs</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading && (
              <TableRow>
                <TableCell colSpan={5} align="center" sx={{ py: 6 }}>
                  <CircularProgress size={28} />
                </TableCell>
              </TableRow>
            )}

            {!isLoading && data?.items.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} align="center" sx={{ py: 6 }}>
                  <Typography color="text.secondary">No routing rules found.</Typography>
                </TableCell>
              </TableRow>
            )}

            {!isLoading &&
              data?.items.map((rule) => (
                <TableRow key={rule.id} hover>
                  <TableCell>{rule.name}</TableCell>
                  <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>{rule.priority}</TableCell>
                  <TableCell>
                    <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                      {rule.target_outputs_json.map((type) => (
                        <Chip key={type} label={typeLabel(type)} size="small" variant="outlined" />
                      ))}
                    </Stack>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={rule.status}
                      size="small"
                      color={STATUS_COLORS[rule.status] ?? "default"}
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title="Edit">
                      <IconButton size="small" onClick={() => navigate(`/outputs/routing-rules/${rule.id}/edit`)}>
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
    </Container>
  );
}
