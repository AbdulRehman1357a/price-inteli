import ReplayIcon from "@mui/icons-material/Replay";
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
import TableRow from "@mui/material/TableRow";
import Tab from "@mui/material/Tab";
import Tabs from "@mui/material/Tabs";
import TextField from "@mui/material/TextField";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import { useState } from "react";
import { useParams } from "react-router-dom";

import AuthorityTable from "../features/integrationHub/AuthorityTable";
import ErrorsTable from "../features/integrationHub/ErrorsTable";
import HealthPanel from "../features/integrationHub/HealthPanel";
import IntegrationForm, { integrationToFormValues } from "../features/integrationHub/IntegrationForm";
import LocationsTable from "../features/integrationHub/LocationsTable";
import MappingsTable from "../features/integrationHub/MappingsTable";
import ReconciliationTable from "../features/integrationHub/ReconciliationTable";
import SchedulesTable from "../features/integrationHub/SchedulesTable";
import SetupChecklist from "../features/integrationHub/SetupChecklist";
import WebhookEventsTable from "../features/integrationHub/WebhookEventsTable";
import {
  useIntegration,
  useRetrySyncJob,
  useStartSync,
  useSyncJobs,
  useTestConnection,
  useUpdateIntegration,
} from "../features/integrationHub/hooks";
import { ENTITY_TYPE_OPTIONS, JOB_STATUS_COLORS, STATUS_COLORS } from "../features/integrationHub/options";

function OverviewTab({ integration }) {
  const updateIntegration = useUpdateIntegration(integration.id);
  const testConnection = useTestConnection(integration.id);
  const [testResult, setTestResult] = useState(null);

  const handleTest = async () => {
    const result = await testConnection.mutateAsync();
    setTestResult(result);
  };

  return (
    <Stack spacing={3}>
      <Stack direction="row" spacing={2} alignItems="center">
        <Button variant="outlined" onClick={handleTest} disabled={testConnection.isPending}>
          {testConnection.isPending ? "Testing…" : "Test Connection"}
        </Button>
        <Chip
          label={integration.status}
          color={STATUS_COLORS[integration.status] ?? "default"}
          variant="outlined"
        />
      </Stack>
      {testResult && (
        <Alert severity={testResult.success ? "success" : "error"}>{testResult.message}</Alert>
      )}
      <IntegrationForm
        defaultValues={integrationToFormValues(integration)}
        onSubmit={(payload) => updateIntegration.mutateAsync(payload)}
        submitLabel="Save Changes"
      />
    </Stack>
  );
}

const CAPABILITY_FLAG_BY_ENTITY_TYPE = {
  product: "supports_product_read",
  price: "supports_price_read",
  inventory: "supports_inventory_read",
  promotion: "supports_promotion_read",
};

function SyncJobsTab({ integration }) {
  const [entityType, setEntityType] = useState("product");
  const [formError, setFormError] = useState(null);
  const { data, isLoading } = useSyncJobs(integration.id, { page: 1, pageSize: 20 });
  const startSync = useStartSync(integration.id);
  const retryJob = useRetrySyncJob(integration.id);

  const handleStartSync = async () => {
    setFormError(null);
    try {
      await startSync.mutateAsync({ entityType });
    } catch (error) {
      setFormError(error.response?.data?.error?.message ?? "Unable to start this sync.");
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
            sx={{ minWidth: { xs: "100%", sm: 180 } }}
          >
            {ENTITY_TYPE_OPTIONS.map((option) => {
              const flag = CAPABILITY_FLAG_BY_ENTITY_TYPE[option];
              const supported = !flag || integration.capabilities?.[flag] !== false;
              return (
                <MenuItem key={option} value={option} disabled={!supported}>
                  {option}
                  {!supported ? " (not supported by this adapter)" : ""}
                </MenuItem>
              );
            })}
          </TextField>
          <Button variant="contained" onClick={handleStartSync} disabled={startSync.isPending}>
            {startSync.isPending ? "Starting…" : "Start Sync"}
          </Button>
        </Stack>
        {formError && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {formError}
          </Alert>
        )}
      </Paper>

      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Entity</TableCell>
              <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Type</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right" sx={{ display: { xs: "none", sm: "table-cell" } }}>
                Processed
              </TableCell>
              <TableCell align="right" sx={{ display: { xs: "none", sm: "table-cell" } }}>
                Failed
              </TableCell>
              <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Started</TableCell>
              <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Completed</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading && (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  <CircularProgress size={24} />
                </TableCell>
              </TableRow>
            )}
            {!isLoading && (data?.items.length ?? 0) === 0 && (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  <Typography color="text.secondary">No sync jobs yet.</Typography>
                </TableCell>
              </TableRow>
            )}
            {!isLoading &&
              data?.items.map((job) => {
                const canRetry = job.status === "failed" || job.status === "completed_with_errors";
                return (
                  <TableRow key={job.id}>
                    <TableCell>{job.entity_type}</TableCell>
                    <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>{job.job_type}</TableCell>
                    <TableCell>
                      <Chip
                        label={job.status}
                        size="small"
                        color={JOB_STATUS_COLORS[job.status] ?? "default"}
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell align="right" sx={{ display: { xs: "none", sm: "table-cell" } }}>
                      {job.records_processed}
                    </TableCell>
                    <TableCell align="right" sx={{ display: { xs: "none", sm: "table-cell" } }}>
                      {job.records_failed}
                    </TableCell>
                    <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                      {new Date(job.started_at).toLocaleString()}
                    </TableCell>
                    <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                      {job.completed_at ? new Date(job.completed_at).toLocaleString() : "—"}
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title="Retry">
                        <span>
                          <IconButton
                            size="small"
                            disabled={!canRetry}
                            onClick={() => retryJob.mutate(job.id)}
                          >
                            <ReplayIcon fontSize="small" />
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
    </Stack>
  );
}

export default function IntegrationHubDetailPage() {
  const { integrationId } = useParams();
  const [tab, setTab] = useState("overview");
  const { data: integration, isLoading, isError } = useIntegration(integrationId);

  if (isLoading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (isError || !integration) {
    return (
      <Container sx={{ py: 4 }}>
        <Alert severity="error">Integration not found.</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        {integration.name}
      </Typography>

      <SetupChecklist integration={integration} onNavigate={setTab} />

      <Tabs
        value={tab}
        onChange={(_, newValue) => setTab(newValue)}
        variant="scrollable"
        scrollButtons="auto"
        sx={{ mb: 2 }}
      >
        <Tab value="overview" label="Overview" />
        <Tab value="locations" label="Locations" />
        <Tab value="mappings" label="Field Mappings" />
        <Tab value="authority" label="Authority" />
        <Tab value="jobs" label="Sync Jobs" />
        <Tab value="schedules" label="Schedules" />
        <Tab value="webhooks" label="Webhook Events" />
        <Tab value="errors" label="Errors" />
        <Tab value="reconciliation" label="Reconciliation" />
        <Tab value="health" label="Health" />
      </Tabs>

      <Paper variant="outlined" sx={{ p: 3 }}>
        {tab === "overview" && <OverviewTab integration={integration} />}
        {tab === "locations" && <LocationsTable integrationId={integration.id} />}
        {tab === "mappings" && <MappingsTable integrationId={integration.id} />}
        {tab === "authority" && <AuthorityTable integrationId={integration.id} />}
        {tab === "jobs" && <SyncJobsTab integration={integration} />}
        {tab === "schedules" && <SchedulesTable integrationId={integration.id} />}
        {tab === "webhooks" && <WebhookEventsTable integrationId={integration.id} />}
        {tab === "errors" && <ErrorsTable integrationId={integration.id} />}
        {tab === "reconciliation" && <ReconciliationTable integrationId={integration.id} />}
        {tab === "health" && <HealthPanel integrationId={integration.id} />}
      </Paper>
    </Container>
  );
}
