import { useQueries } from "@tanstack/react-query";
import ArticleIcon from "@mui/icons-material/Article";
import CancelIcon from "@mui/icons-material/Cancel";
import ListAltIcon from "@mui/icons-material/ListAlt";
import ReplayIcon from "@mui/icons-material/Replay";
import VisibilityIcon from "@mui/icons-material/Visibility";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Container from "@mui/material/Container";
import Dialog from "@mui/material/Dialog";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import Grid from "@mui/material/Grid";
import IconButton from "@mui/material/IconButton";
import Link from "@mui/material/Link";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TablePagination from "@mui/material/TablePagination";
import TableRow from "@mui/material/TableRow";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import { useState } from "react";
import { Link as RouterLink, useSearchParams } from "react-router-dom";

import ChannelSelect from "../features/outputs/ChannelSelect";
import ESLSimulatorPreview from "../features/outputs/ESLSimulatorPreview";
import {
  useCancelJob,
  useChannels,
  useCreateJob,
  useJobs,
  useJobsSummary,
  useRetryJob,
} from "../features/outputs/hooks";
import { OUTPUT_JOB_STATUS_COLORS, OUTPUT_TYPE_OPTIONS } from "../features/outputs/options";
import ProductMultiSelect from "../features/pricing/ProductMultiSelect";
import { fetchProduct } from "../features/products/api";
import { useAllStores } from "../features/stores/hooks";

const STATUS_TABS = ["all", "pending", "processing", "completed", "failed", "cancelled"];

const SUMMARY_CARDS = [
  { key: "total", label: "Total Jobs" },
  { key: "successful", label: "Successful" },
  { key: "failed", label: "Failed" },
  { key: "pending", label: "Pending" },
];

function ExecutionSummaryCards() {
  const { data: summary } = useJobsSummary();

  return (
    <Grid container spacing={2} sx={{ mb: 3 }}>
      {SUMMARY_CARDS.map(({ key, label }) => (
        <Grid item xs={6} sm={3} key={key}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="body2" color="text.secondary">
                {label}
              </Typography>
              <Typography variant="h4">{summary ? summary[key] : "—"}</Typography>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
}

function JobResultView({ job }) {
  if (!job) return null;

  if (job.status === "pending" || job.status === "processing") {
    return (
      <Stack spacing={1.5} alignItems="center" sx={{ py: 3 }}>
        <CircularProgress size={28} />
        <Typography color="text.secondary">
          This job is still {job.status} — a label hasn't been generated yet.
        </Typography>
      </Stack>
    );
  }

  if (job.status === "failed") {
    return <Alert severity="error">{job.last_error || "This job failed with no error detail."}</Alert>;
  }

  const payload = job.payload;
  if (!payload) return <Typography color="text.secondary">No result available for this job.</Typography>;

  if (payload.qr_image_base64) {
    return (
      <Stack spacing={1.5} alignItems="flex-start">
        <Box
          component="img"
          src={`data:${payload.qr_image_mime};base64,${payload.qr_image_base64}`}
          alt="Generated QR code"
          sx={{ width: 200, height: 200, border: "1px solid", borderColor: "divider", borderRadius: 1 }}
        />
        {payload.qr_text ? (
          <Paper variant="outlined" sx={{ p: 1.5, width: "100%" }}>
            <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 0.5 }}>
              QR link:
            </Typography>
            <Box component="pre" sx={{ m: 0, fontSize: 13, whiteSpace: "pre-wrap", fontFamily: "monospace" }}>
              {payload.qr_text}
            </Box>
          </Paper>
        ) : payload.target_url ? (
          <Link href={payload.target_url} target="_blank" rel="noopener noreferrer">
            {payload.target_url}
          </Link>
        ) : null}
      </Stack>
    );
  }

  if (payload.pdf_base64) {
    console.log("PDF Payload:", payload);
    const pdfDataUrl = `data:${payload.pdf_mime};base64,${payload.pdf_base64}`;
    return (
      <Stack spacing={1} alignItems="flex-start" sx={{ width: "100%" }}>
        <Typography>
          {payload.product_name} — {payload.currency} {payload.price}
        </Typography>
        <Box
          component="iframe"
          src={pdfDataUrl}
          title="PDF Preview"
          sx={{ width: "100%", height: 320, border: "1px solid", borderColor: "divider", borderRadius: 1 }}
        />
        <Link href={pdfDataUrl} download={`${payload.sku || "label"}.pdf`}>
          Download PDF label
        </Link>
      </Stack>
    );
  }

  if (payload.published) {
    return (
      <Stack spacing={1} alignItems="flex-start">
        <Typography>
          {payload.product_name} — {payload.currency} {payload.price}
        </Typography>
        <Link href={payload.public_url} target="_blank" rel="noopener noreferrer">
          {payload.public_url}
        </Link>
      </Stack>
    );
  }

  const syncStatus =
    payload.pos_sync_status || payload.ecommerce_sync_status || payload.signage_sync_status;
  if (syncStatus) {
    return (
      <Stack spacing={1} alignItems="flex-start">
        <Typography>
          {payload.product_name} — {payload.currency} {payload.price}
        </Typography>
        <Chip label={syncStatus.replace(/_/g, " ")} size="small" color="success" variant="outlined" />
      </Stack>
    );
  }

  return <ESLSimulatorPreview payload={payload} />;
}

function JobLogsView({ job }) {
  if (!job) return null;

  const rows = [
    ["Job ID", job.id],
    ["Status", job.status],
    ["Attempts", job.attempts],
    ["Idempotency Key", job.idempotency_key || "— (manually dispatched)"],
    ["Routing Rule", job.routing_rule_id || "— (manually dispatched)"],
    ["Source Price", job.source_price_id || "—"],
    ["Created", new Date(job.created_at).toLocaleString()],
    ["Completed", job.completed_at ? new Date(job.completed_at).toLocaleString() : "—"],
    ["Last Error", job.last_error || "—"],
  ];

  return (
    <Table size="small">
      <TableBody>
        {rows.map(([label, value]) => (
          <TableRow key={label}>
            <TableCell sx={{ fontWeight: "bold", width: "35%" }}>{label}</TableCell>
            <TableCell sx={{ wordBreak: "break-all" }}>{value}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

export default function OutputJobsPage() {
  const [searchParams] = useSearchParams();
  const [channelId, setChannelId] = useState(searchParams.get("channelId") ?? "");
  const [selectedProducts, setSelectedProducts] = useState([]);
  const [dispatchError, setDispatchError] = useState(null);
  const [tab, setTab] = useState("all");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [viewingJob, setViewingJob] = useState(null);
  const [payloadJob, setPayloadJob] = useState(null);
  const [logsJob, setLogsJob] = useState(null);

  const createJob = useCreateJob();
  const retryJob = useRetryJob();
  const cancelJob = useCancelJob();
  const { data, isLoading, isError } = useJobs({
    page,
    pageSize,
    status: tab === "all" ? undefined : tab,
  });
  const { data: channelsData } = useChannels({ page: 1, pageSize: 100 });
  const { data: stores } = useAllStores();

  const items = data?.items ?? [];
  const productIds = [...new Set(items.map((job) => job.product_id))];
  const productQueries = useQueries({
    queries: productIds.map((id) => ({
      queryKey: ["products", "detail", id],
      queryFn: () => fetchProduct(id),
    })),
  });
  const productById = new Map(productQueries.map((q) => q.data).filter(Boolean).map((p) => [p.id, p]));
  const channelById = new Map((channelsData?.items ?? []).map((c) => [c.id, c]));
  const storeById = new Map((stores ?? []).map((s) => [s.id, s]));

  const handleDispatch = async () => {
    setDispatchError(null);
    if (!channelId || selectedProducts.length === 0) {
      setDispatchError("Select an output channel and at least one product.");
      return;
    }
    // The channel already carries its own store (or none, for "all
    // stores") — every job in this batch inherits it rather than asking
    // for a store again here.
    const channelStoreId = channelById.get(channelId)?.store_id;

    const results = await Promise.allSettled(
      selectedProducts.map((product) =>
        createJob.mutateAsync({
          outputChannelId: channelId,
          productId: product.id,
          storeId: channelStoreId || undefined,
        })
      )
    );
    const failed = results.filter((result) => result.status === "rejected");
    if (failed.length === 0) {
      setSelectedProducts([]);
    } else {
      const firstMessage = failed[0].reason?.response?.data?.error?.message ?? "Unable to dispatch this job.";
      setDispatchError(
        failed.length === selectedProducts.length
          ? firstMessage
          : `${selectedProducts.length - failed.length} of ${selectedProducts.length} jobs dispatched; ` +
              `${failed.length} failed (${firstMessage}).`
      );
    }
  };

  const handleRetry = (jobId) => {
    retryJob.mutate(jobId);
  };

  const handleCancel = (jobId) => {
    cancelJob.mutate(jobId);
  };

  return (
    <Container sx={{ py: 4 }}>
      <Stack
        direction={{ xs: "column", sm: "row" }}
        justifyContent="space-between"
        alignItems={{ xs: "flex-start", sm: "center" }}
        spacing={2}
        sx={{ mb: 1 }}
      >
        <Typography variant="h4" component="h1">
          Output Job Monitoring
        </Typography>
        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
          <Button variant="outlined" component={RouterLink} to="/outputs/channels">
            Output Channels
          </Button>
          <Button variant="outlined" component={RouterLink} to="/outputs/routing-rules">
            Routing Rules
          </Button>
        </Stack>
      </Stack>

      <ExecutionSummaryCards />

      <Paper variant="outlined" sx={{ p: 3, mb: 3 }}>
        <Typography variant="subtitle1" gutterBottom>
          Dispatch Output
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Pick a channel and one or more products — each product gets its own job, all sent to the
          same channel as a batch. The store is whichever one the channel itself is scoped to.
        </Typography>
        {dispatchError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {dispatchError}
          </Alert>
        )}
        <Grid container spacing={2} alignItems="flex-start">
          <Grid item xs={12} sm={4}>
            <ChannelSelect value={channelId} onChange={setChannelId} required />
          </Grid>
          <Grid item xs={12} sm={6}>
            <ProductMultiSelect
              value={selectedProducts}
              onChange={setSelectedProducts}
              label="Products"
              helperText="Search and select one or more products to dispatch."
            />
          </Grid>
          <Grid item xs={12} sm={2}>
            <Button
              variant="contained"
              onClick={handleDispatch}
              disabled={createJob.isPending}
              fullWidth
            >
              Send
            </Button>
          </Grid>
        </Grid>
      </Paper>

      <Tabs
        value={tab}
        onChange={(_, newValue) => {
          setTab(newValue);
          setPage(1);
        }}
        variant="scrollable"
        scrollButtons="auto"
        sx={{ mb: 2 }}
      >
        {STATUS_TABS.map((status) => (
          <Tab key={status} value={status} label={status === "all" ? "All" : status} />
        ))}
      </Tabs>

      {isError && <Alert severity="error">Unable to load output jobs.</Alert>}

      <TableContainer component={Paper} variant="outlined">
        <Table>
          <TableHead>
            <TableRow>
              <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>Channel</TableCell>
              <TableCell>Product</TableCell>
              <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>Store</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right" sx={{ display: { xs: "none", md: "table-cell" } }}>
                Attempts
              </TableCell>
              <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Created</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading && (
              <TableRow>
                <TableCell colSpan={7} align="center" sx={{ py: 6 }}>
                  <CircularProgress size={28} />
                </TableCell>
              </TableRow>
            )}

            {!isLoading && items.length === 0 && (
              <TableRow>
                <TableCell colSpan={7} align="center" sx={{ py: 6 }}>
                  <Typography color="text.secondary">No output jobs found.</Typography>
                </TableCell>
              </TableRow>
            )}

            {!isLoading &&
              items.map((job) => {
                const channel = channelById.get(job.output_channel_id);
                const product = productById.get(job.product_id);
                const store = job.store_id ? storeById.get(job.store_id) : null;
                const canRetry = job.status === "failed" || job.status === "completed";
                const canCancel = job.status === "pending";
                return (
                  <TableRow key={job.id} hover>
                    <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>
                      {channel
                        ? `${channel.name} (${
                            OUTPUT_TYPE_OPTIONS.find((o) => o.value === channel.output_type)?.label ??
                            channel.output_type
                          })`
                        : job.output_channel_id}
                    </TableCell>
                    <TableCell>{product ? `${product.product_name} (${product.sku})` : job.product_id}</TableCell>
                    <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>
                      {store ? store.name : "All stores"}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={job.status}
                        size="small"
                        color={OUTPUT_JOB_STATUS_COLORS[job.status] ?? "default"}
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell align="right" sx={{ display: { xs: "none", md: "table-cell" } }}>
                      {job.attempts}
                    </TableCell>
                    <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                      {new Date(job.created_at).toLocaleString()}
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title="View result">
                        <IconButton size="small" onClick={() => setViewingJob(job)}>
                          <VisibilityIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="View payload">
                        <IconButton size="small" onClick={() => setPayloadJob(job)}>
                          <ArticleIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="View logs">
                        <IconButton size="small" onClick={() => setLogsJob(job)}>
                          <ListAltIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Retry">
                        <span>
                          <IconButton size="small" onClick={() => handleRetry(job.id)} disabled={!canRetry}>
                            <ReplayIcon fontSize="small" />
                          </IconButton>
                        </span>
                      </Tooltip>
                      <Tooltip title="Cancel">
                        <span>
                          <IconButton size="small" onClick={() => handleCancel(job.id)} disabled={!canCancel}>
                            <CancelIcon fontSize="small" />
                          </IconButton>
                        </span>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                );
              })}
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

      <Dialog open={Boolean(viewingJob)} onClose={() => setViewingJob(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Output Result</DialogTitle>
        <DialogContent>
          <Box sx={{ py: 1 }}>
            <JobResultView job={viewingJob} />
          </Box>
        </DialogContent>
      </Dialog>

      <Dialog open={Boolean(payloadJob)} onClose={() => setPayloadJob(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Job Payload</DialogTitle>
        <DialogContent>
          <Box
            component="pre"
            sx={{
              py: 1,
              fontSize: 13,
              whiteSpace: "pre-wrap",
              wordBreak: "break-all",
              fontFamily: "monospace",
            }}
          >
            {payloadJob ? JSON.stringify(payloadJob.payload ?? {}, null, 2) : ""}
          </Box>
        </DialogContent>
      </Dialog>

      <Dialog open={Boolean(logsJob)} onClose={() => setLogsJob(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Job Logs</DialogTitle>
        <DialogContent>
          <JobLogsView job={logsJob} />
        </DialogContent>
      </Dialog>
    </Container>
  );
}
