import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import DownloadIcon from "@mui/icons-material/Download";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Container from "@mui/material/Container";
import MenuItem from "@mui/material/MenuItem";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Step from "@mui/material/Step";
import StepLabel from "@mui/material/StepLabel";
import Stepper from "@mui/material/Stepper";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import StoreSelect from "../features/stores/StoreSelect";
import {
  useDownloadImportTemplate,
  useImportErrors,
  useImportJob,
  useStartImport,
  useUploadImport,
} from "../features/imports/hooks";
import { ENTITY_TYPE_OPTIONS, STATUS_LABELS, TERMINAL_STATUSES, fieldsForJob } from "../features/imports/options";

const STEP_LABELS = [
  "Upload File",
  "Preview Columns",
  "Map Columns",
  "Validation",
  "Preview Rows",
  "Resolve Errors",
  "Import",
  "Results",
];

// Steps 4-6 ("Validation" / "Preview valid & invalid rows" / "Resolve
// errors") happen together with Step 7 ("Import") as one background pass —
// each valid row is imported as it's validated, rather than pausing for a
// second manual "commit" step. The stepper below still shows all 8 labels
// for clarity; "processing" just advances straight to the "Import" index.
const PHASE_TO_STEP_INDEX = { select: 0, columns: 1, mapping: 2, processing: 6, results: 7 };
const DONE_DESTINATION = { products: "/products", inventory: "/inventory", users: "/users" };

export default function ImportWizardPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [phase, setPhase] = useState("select");
  const [file, setFile] = useState(null);
  const [entityType, setEntityType] = useState(location.state?.entityType ?? "products");
  const [storeId, setStoreId] = useState("");
  const [job, setJob] = useState(null);
  const [mapping, setMapping] = useState({});
  const [formError, setFormError] = useState(null);

  const upload = useUploadImport();
  const start = useStartImport();
  const downloadTemplate = useDownloadImportTemplate();
  const { data: polledJob } = useImportJob(job?.id, { poll: phase === "processing" });
  const { data: errorsData } = useImportErrors(job?.id, { page: 1, pageSize: 50 });

  useEffect(() => {
    if (phase === "processing" && polledJob && TERMINAL_STATUSES.has(polledJob.status)) {
      setJob(polledJob);
      setPhase("results");
    }
  }, [phase, polledJob]);

  const handleUpload = async () => {
    setFormError(null);
    if (!file) {
      setFormError("Choose a file first.");
      return;
    }
    try {
      const uploaded = await upload.mutateAsync({ file, entityType, storeId: storeId || undefined });
      setJob(uploaded);
      setPhase("columns");
    } catch (error) {
      setFormError(error.response?.data?.error?.message ?? "Upload failed. Please try again.");
    }
  };

  const handleStart = async () => {
    setFormError(null);
    const fields = fieldsForJob(entityType, Boolean(job.store_id));
    const missing = fields.filter((f) => f.required && !mapping[f.value]);
    if (missing.length > 0) {
      setFormError(`Map the required field(s): ${missing.map((f) => f.label).join(", ")}.`);
      return;
    }
    try {
      const started = await start.mutateAsync({ jobId: job.id, mapping });
      setJob(started);
      setPhase("processing");
    } catch (error) {
      setFormError(error.response?.data?.error?.message ?? "Could not start the import.");
    }
  };

  const resetWizard = () => {
    setPhase("select");
    setFile(null);
    setJob(null);
    setMapping({});
    setFormError(null);
  };

  const activeStep = PHASE_TO_STEP_INDEX[phase];
  const fields = job ? fieldsForJob(entityType, Boolean(job.store_id)) : [];
  const displayJob = phase === "processing" ? (polledJob ?? job) : job;

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Bulk Import
      </Typography>

      <Stepper activeStep={activeStep} sx={{ my: 4, flexWrap: "wrap", rowGap: 2 }} alternativeLabel>
        {STEP_LABELS.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      <Paper variant="outlined" sx={{ p: 3 }}>
        {formError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {formError}
          </Alert>
        )}

        {phase === "select" && (
          <Stack spacing={2}>
            <Typography variant="subtitle1">Step 1: Upload File</Typography>
            <TextField
              select
              label="What are you importing?"
              value={entityType}
              onChange={(e) => setEntityType(e.target.value)}
            >
              {ENTITY_TYPE_OPTIONS.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </TextField>

            <Box>
              <Button
                variant="text"
                size="small"
                startIcon={<DownloadIcon />}
                onClick={() => downloadTemplate.mutate(entityType)}
                disabled={downloadTemplate.isPending}
              >
                {downloadTemplate.isPending ? "Preparing template..." : "Download blank template (.xlsx)"}
              </Button>
              {downloadTemplate.isError && (
                <Typography variant="caption" color="error" display="block">
                  Could not download the template. Please try again.
                </Typography>
              )}
            </Box>

            {entityType === "inventory" && (
              <StoreSelect
                value={storeId}
                onChange={setStoreId}
                helperText="Optional — leave blank to map a Store column per row instead."
              />
            )}

            <Button variant="outlined" component="label" startIcon={<CloudUploadIcon />}>
              {file ? file.name : "Choose CSV or XLSX file"}
              <input
                type="file"
                hidden
                accept=".csv,.xlsx"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
            </Button>

            <Box>
              <Button variant="contained" onClick={handleUpload} disabled={upload.isPending}>
                {upload.isPending ? "Uploading..." : "Upload"}
              </Button>
            </Box>
          </Stack>
        )}

        {phase === "columns" && job && (
          <Stack spacing={2}>
            <Typography variant="subtitle1">Step 2: Preview Detected Columns</Typography>
            <Typography color="text.secondary">
              Found {job.detected_columns.length} column(s) in <strong>{job.file_name}</strong>:
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
              {job.detected_columns.map((column) => (
                <Chip key={column} label={column} />
              ))}
            </Stack>
            <Box>
              <Button variant="contained" onClick={() => setPhase("mapping")}>
                Next: Map Columns
              </Button>
            </Box>
          </Stack>
        )}

        {phase === "mapping" && job && (
          <Stack spacing={2}>
            <Typography variant="subtitle1">Step 3: Map Columns</Typography>
            <Typography color="text.secondary">
              Tell us which file column feeds each field. Fields marked * are required.
            </Typography>
            {entityType === "users" && (
              <Alert severity="info">
                The Role column's values must match an existing role name exactly (e.g. "Store
                Manager"), and Initial Password must be at least 8 characters — see Roles &amp;
                Permissions for the exact role names available.
              </Alert>
            )}
            {fields.map((field) => (
              <TextField
                key={field.value}
                select
                label={field.required ? `${field.label} *` : field.label}
                value={mapping[field.value] ?? ""}
                onChange={(e) => setMapping((prev) => ({ ...prev, [field.value]: e.target.value }))}
              >
                <MenuItem value="">— Not mapped —</MenuItem>
                {job.detected_columns.map((column) => (
                  <MenuItem key={column} value={column}>
                    {column}
                  </MenuItem>
                ))}
              </TextField>
            ))}
            <Box>
              <Button variant="contained" onClick={handleStart} disabled={start.isPending}>
                {start.isPending ? "Starting..." : "Start Import"}
              </Button>
            </Box>
          </Stack>
        )}

        {phase === "processing" && (
          <Stack spacing={2} alignItems="center" sx={{ py: 4 }}>
            <Typography variant="subtitle1">Steps 4–7: Validating &amp; Importing</Typography>
            <CircularProgress />
            <Typography color="text.secondary">
              Status: {STATUS_LABELS[displayJob?.status] ?? displayJob?.status}
            </Typography>
            <Typography color="text.secondary">
              {displayJob?.success_rows ?? 0} succeeded, {displayJob?.failed_rows ?? 0} failed so far
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Rows are validated and imported together — a row either succeeds and is imported
              immediately, or fails and is recorded as an error below.
            </Typography>
          </Stack>
        )}

        {phase === "results" && displayJob && (
          <Stack spacing={2}>
            <Typography variant="subtitle1">Step 8: Results</Typography>
            <Alert severity={displayJob.status === "completed" ? "success" : displayJob.status === "failed" ? "error" : "warning"}>
              {displayJob.status === "failed"
                ? displayJob.error_summary
                : `${displayJob.success_rows} of ${displayJob.total_rows} row(s) imported successfully.`}
            </Alert>

            {errorsData?.items.length > 0 && (
              <>
                <Typography variant="subtitle2">Row errors ({errorsData.meta.total})</Typography>
                <TableContainer sx={{ maxHeight: 400 }}>
                  <Table size="small" stickyHeader>
                    <TableHead>
                      <TableRow>
                        <TableCell>Row</TableCell>
                        <TableCell>Field</TableCell>
                        <TableCell>Message</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {errorsData.items.map((error) => (
                        <TableRow key={error.id}>
                          <TableCell>{error.row_number}</TableCell>
                          <TableCell>{error.field_name ?? "—"}</TableCell>
                          <TableCell>{error.error_message}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </>
            )}

            <Stack direction="row" spacing={1}>
              <Button variant="contained" onClick={resetWizard}>
                Start Another Import
              </Button>
              <Button variant="outlined" onClick={() => navigate(DONE_DESTINATION[entityType] ?? "/")}>
                Done
              </Button>
            </Stack>
          </Stack>
        )}
      </Paper>
    </Container>
  );
}
