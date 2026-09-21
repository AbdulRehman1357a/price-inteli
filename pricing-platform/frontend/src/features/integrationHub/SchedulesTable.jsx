import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Grid from "@mui/material/Grid";
import MenuItem from "@mui/material/MenuItem";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Switch from "@mui/material/Switch";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useState } from "react";

import { useCreateSchedule, useSchedules, useUpdateSchedule } from "./hooks";
import { ENTITY_TYPE_OPTIONS, SCHEDULE_INTERVAL_OPTIONS } from "./options";

const DEFAULT_FORM = { entity_type: "product", job_type: "incremental_sync", interval_minutes: 15 };

export default function SchedulesTable({ integrationId }) {
  const [form, setForm] = useState(DEFAULT_FORM);
  const [formError, setFormError] = useState(null);
  const { data: schedules, isLoading } = useSchedules(integrationId);
  const createSchedule = useCreateSchedule(integrationId);
  const updateSchedule = useUpdateSchedule(integrationId);

  const submit = async () => {
    setFormError(null);
    try {
      await createSchedule.mutateAsync(form);
      setForm(DEFAULT_FORM);
    } catch (error) {
      setFormError(error.response?.data?.error?.message ?? "Unable to add this schedule.");
    }
  };

  return (
    <Stack spacing={3}>
      <Typography variant="body2" color="text.secondary">
        Runs an incremental (or full) sync automatically at a fixed interval, in addition to any manual
        "Start Sync" you trigger from the Sync Jobs tab.
      </Typography>

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="subtitle2" gutterBottom>
          Add Schedule
        </Typography>
        {formError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {formError}
          </Alert>
        )}
        <Box>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={4}>
              <TextField
                select
                label="Entity"
                fullWidth
                value={form.entity_type}
                onChange={(e) => setForm((f) => ({ ...f, entity_type: e.target.value }))}
              >
                {ENTITY_TYPE_OPTIONS.map((option) => (
                  <MenuItem key={option} value={option}>
                    {option}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} sm={5}>
              <TextField
                select
                label="Frequency"
                fullWidth
                value={form.interval_minutes}
                onChange={(e) =>
                  setForm((f) => ({ ...f, interval_minutes: Number(e.target.value) }))
                }
              >
                {SCHEDULE_INTERVAL_OPTIONS.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} sm={3}>
              <Button variant="contained" fullWidth onClick={submit} disabled={createSchedule.isPending}>
                Add Schedule
              </Button>
            </Grid>
          </Grid>
        </Box>
      </Paper>

      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Entity</TableCell>
              <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Job Type</TableCell>
              <TableCell>Frequency</TableCell>
              <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Next Run</TableCell>
              <TableCell align="center">Enabled</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {!isLoading && (schedules ?? []).length === 0 && (
              <TableRow>
                <TableCell colSpan={5} align="center" sx={{ py: 4 }}>
                  <Typography color="text.secondary">No schedules configured.</Typography>
                </TableCell>
              </TableRow>
            )}
            {(schedules ?? []).map((schedule) => (
              <TableRow key={schedule.id}>
                <TableCell>{schedule.entity_type}</TableCell>
                <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>{schedule.job_type}</TableCell>
                <TableCell>
                  {SCHEDULE_INTERVAL_OPTIONS.find((o) => o.value === schedule.interval_minutes)?.label ??
                    `Every ${schedule.interval_minutes} min`}
                </TableCell>
                <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                  {new Date(schedule.next_run_at).toLocaleString()}
                </TableCell>
                <TableCell align="center">
                  <Switch
                    checked={schedule.is_enabled}
                    onChange={(event) =>
                      updateSchedule.mutate({
                        scheduleId: schedule.id,
                        payload: { is_enabled: event.target.checked },
                      })
                    }
                  />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Stack>
  );
}
