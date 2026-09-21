import Alert from "@mui/material/Alert";
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
import { useState } from "react";

import { useRotateWebhookSecret, useWebhookEvents } from "./hooks";
import { WEBHOOK_EVENT_STATUS_COLORS } from "./options";

export default function WebhookEventsTable({ integrationId }) {
  const [secret, setSecret] = useState(null);
  const [rotateError, setRotateError] = useState(null);
  const { data, isLoading } = useWebhookEvents(integrationId, { page: 1, pageSize: 20 });
  const rotateSecret = useRotateWebhookSecret(integrationId);

  const handleRotate = async () => {
    setRotateError(null);
    try {
      const result = await rotateSecret.mutateAsync();
      setSecret(result.webhook_secret);
    } catch (error) {
      setRotateError(error.response?.data?.error?.message ?? "Unable to rotate the webhook secret.");
    }
  };

  return (
    <Stack spacing={2}>
      <Stack direction="row" spacing={2} alignItems="center">
        <Button variant="outlined" onClick={handleRotate} disabled={rotateSecret.isPending}>
          {rotateSecret.isPending ? "Rotating…" : "Generate / Rotate Webhook Secret"}
        </Button>
        <Typography variant="body2" color="text.secondary">
          POST to /integration-webhooks/{"{integration_id}"}/{"{entity_type}"}, signed with this secret
          (HMAC-SHA256, header X-Webhook-Signature).
        </Typography>
      </Stack>
      {rotateError && <Alert severity="error">{rotateError}</Alert>}
      {secret && (
        <Alert severity="success">
          New secret (shown once — store it in the external system now): <code>{secret}</code>
        </Alert>
      )}

      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Event</TableCell>
              <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Entity</TableCell>
              <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Signature</TableCell>
              <TableCell>Status</TableCell>
              <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Received</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {!isLoading && (data?.items.length ?? 0) === 0 && (
              <TableRow>
                <TableCell colSpan={5} align="center" sx={{ py: 4 }}>
                  <Typography color="text.secondary">No webhook events received yet.</Typography>
                </TableCell>
              </TableRow>
            )}
            {(data?.items ?? []).map((event) => (
              <TableRow key={event.id}>
                <TableCell>{event.provider_event_id}</TableCell>
                <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                  {event.entity_type ?? "—"}
                </TableCell>
                <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                  <Chip
                    label={event.signature_valid ? "valid" : "invalid"}
                    size="small"
                    color={event.signature_valid ? "success" : "error"}
                    variant="outlined"
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    label={event.status}
                    size="small"
                    color={WEBHOOK_EVENT_STATUS_COLORS[event.status] ?? "default"}
                    variant="outlined"
                  />
                </TableCell>
                <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                  {new Date(event.received_at).toLocaleString()}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Stack>
  );
}
