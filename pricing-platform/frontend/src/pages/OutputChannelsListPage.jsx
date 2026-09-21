import EditIcon from "@mui/icons-material/Edit";
import SendIcon from "@mui/icons-material/Send";
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

import { useChannels, useLabelTemplates } from "../features/outputs/hooks";
import { OUTPUT_CHANNEL_STATUS_OPTIONS, OUTPUT_TYPE_OPTIONS } from "../features/outputs/options";
import { useAllStores } from "../features/stores/hooks";

const STATUS_COLORS = { active: "success", inactive: "default" };
const typeLabel = (value) => OUTPUT_TYPE_OPTIONS.find((o) => o.value === value)?.label ?? value;

export default function OutputChannelsListPage() {
  const navigate = useNavigate();
  const [outputType, setOutputType] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const { data, isLoading, isError } = useChannels({ page, pageSize, outputType, status });
  const { data: stores } = useAllStores();
  const { data: labelTemplates } = useLabelTemplates();
  const storeName = (storeId) => stores?.find((s) => s.id === storeId)?.name ?? "Store-specific";
  const templateName = (labelTemplateId) =>
    labelTemplates?.find((t) => t.id === labelTemplateId)?.name ?? "Default (no template)";

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
          Output Channels
        </Typography>
        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
          <Button variant="outlined" component={RouterLink} to="/outputs/routing-rules">
            Routing Rules
          </Button>
          <Button variant="outlined" component={RouterLink} to="/outputs/jobs">
            Job Monitoring
          </Button>
          <Button variant="contained" component={RouterLink} to="/outputs/channels/new">
            New Output
          </Button>
        </Stack>
      </Stack>

      <Stack direction={{ xs: "column", sm: "row" }} spacing={2} sx={{ mb: 2 }}>
        <TextField
          select
          label="Output Type"
          value={outputType}
          onChange={(event) => {
            setOutputType(event.target.value);
            setPage(1);
          }}
          sx={{ minWidth: { xs: "100%", sm: 220 } }}
        >
          <MenuItem value="">All types</MenuItem>
          {OUTPUT_TYPE_OPTIONS.map((option) => (
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
          {OUTPUT_CHANNEL_STATUS_OPTIONS.map((option) => (
            <MenuItem key={option} value={option}>
              {option}
            </MenuItem>
          ))}
        </TextField>
      </Stack>

      {isError && <Alert severity="error">Unable to load output channels.</Alert>}

      <TableContainer component={Paper} variant="outlined">
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Output Name</TableCell>
              <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>Output Type</TableCell>
              <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Template</TableCell>
              <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>Store</TableCell>
              <TableCell>Status</TableCell>
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
                  <Typography color="text.secondary">No output channels found.</Typography>
                </TableCell>
              </TableRow>
            )}

            {!isLoading &&
              data?.items.map((channel) => (
                <TableRow key={channel.id} hover>
                  <TableCell>{channel.name}</TableCell>
                  <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>
                    {typeLabel(channel.output_type)}
                  </TableCell>
                  <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                    {channel.output_type === "pdf_label" ? (
                      templateName(channel.label_template_id)
                    ) : (
                      <Typography component="span" color="text.disabled">
                        — not applicable
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>
                    {channel.store_id ? storeName(channel.store_id) : "All stores"}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={channel.status}
                      size="small"
                      color={STATUS_COLORS[channel.status] ?? "default"}
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title="Dispatch">
                      <IconButton
                        size="small"
                        onClick={() => navigate(`/outputs/jobs?channelId=${channel.id}`)}
                      >
                        <SendIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Edit">
                      <IconButton size="small" onClick={() => navigate(`/outputs/channels/${channel.id}/edit`)}>
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
