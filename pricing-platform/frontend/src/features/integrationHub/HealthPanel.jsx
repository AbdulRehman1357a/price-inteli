import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Grid from "@mui/material/Grid";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import { useIntegrationHealth } from "./hooks";
import { JOB_STATUS_COLORS, STATUS_COLORS } from "./options";

function Metric({ label, children }) {
  return (
    <Paper variant="outlined" sx={{ p: 2, height: "100%" }}>
      <Typography variant="caption" color="text.secondary" sx={{ display: "block" }}>
        {label}
      </Typography>
      <Typography variant="body1">{children}</Typography>
    </Paper>
  );
}

const formatDate = (value) => (value ? new Date(value).toLocaleString() : "Never");

export default function HealthPanel({ integrationId }) {
  const { data: health, isLoading } = useIntegrationHealth(integrationId);

  if (isLoading || !health) {
    return <CircularProgress size={24} />;
  }

  return (
    <Stack spacing={2}>
      <Grid container spacing={2}>
        <Grid item xs={12} sm={4}>
          <Metric label="Connection Status">
            <Chip
              label={health.status}
              size="small"
              color={STATUS_COLORS[health.status] ?? "default"}
              variant="outlined"
            />
          </Metric>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Metric label="Last Sync">{formatDate(health.last_sync_at)}</Metric>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Metric label="Last Successful Connection">{formatDate(health.last_successful_connection_at)}</Metric>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Metric label="Last Failed Connection">{formatDate(health.last_failed_connection_at)}</Metric>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Metric label="Last Job Status">
            {health.last_job_status ? (
              <Chip
                label={health.last_job_status}
                size="small"
                color={JOB_STATUS_COLORS[health.last_job_status] ?? "default"}
                variant="outlined"
              />
            ) : (
              "No jobs yet"
            )}
          </Metric>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Metric label="Webhook Configured">{health.webhook_configured ? "Yes" : "No"}</Metric>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Metric label="Open Errors">{health.open_error_count}</Metric>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Metric label="Open Reconciliation Mismatches">{health.open_reconciliation_count}</Metric>
        </Grid>
      </Grid>
    </Stack>
  );
}
