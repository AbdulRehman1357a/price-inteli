import { zodResolver } from "@hookform/resolvers/zod";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import FormControlLabel from "@mui/material/FormControlLabel";
import Grid from "@mui/material/Grid";
import MenuItem from "@mui/material/MenuItem";
import Stack from "@mui/material/Stack";
import Switch from "@mui/material/Switch";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";

import StoreSelect from "../stores/StoreSelect";
import LabelTemplateEditor from "./LabelTemplateEditor";
import LabelTemplateSelect, { CREATE_NEW } from "./LabelTemplateSelect";
import { useDeleteLabelTemplate } from "./hooks";
import {
  BANNER_POSITION_OPTIONS,
  ERROR_CORRECTION_OPTIONS,
  ORIENTATION_OPTIONS,
  OUTPUT_CHANNEL_STATUS_OPTIONS,
  OUTPUT_TYPE_OPTIONS,
  QR_POSITION_OPTIONS,
  THEME_OPTIONS,
} from "./options";
import { outputChannelSchema } from "./validation";

const EMPTY_VALUES = {
  name: "",
  output_type: "esl_simulator",
  store_id: "",
  status: "active",
  label_template_id: "",
  label_size: "",
  orientation: "",
  theme: "",
  box_size: "",
  border: "",
  error_correction: "",
  label_width_mm: "",
  label_height_mm: "",
  show_qr: true,
  qr_position: "right",
  qr_size_mm: "",
  show_unit_price: true,
  banner_position: "bottom",
  pos_terminal_id: "",
  platform: "",
  screen_id: "",
};

// Converts the API's OutputChannelOut shape (a nested configuration blob)
// into this form's flat field values.
export function channelToFormValues(channel) {
  const configuration = channel.configuration ?? {};
  return {
    ...EMPTY_VALUES,
    name: channel.name,
    output_type: channel.output_type,
    store_id: channel.store_id ?? "",
    label_template_id: channel.label_template_id ?? "",
    status: channel.status,
    label_size: configuration.label_size ?? "",
    orientation: configuration.orientation ?? "",
    theme: configuration.theme ?? "",
    box_size: configuration.box_size != null ? String(configuration.box_size) : "",
    border: configuration.border != null ? String(configuration.border) : "",
    error_correction: configuration.error_correction ?? "",
    label_width_mm: configuration.label_width_mm != null ? String(configuration.label_width_mm) : "",
    label_height_mm: configuration.label_height_mm != null ? String(configuration.label_height_mm) : "",
    show_qr: configuration.show_qr ?? true,
    qr_position: configuration.qr_position ?? "right",
    qr_size_mm: configuration.qr_size_mm != null ? String(configuration.qr_size_mm) : "",
    show_unit_price: configuration.show_unit_price ?? true,
    banner_position: configuration.banner_position ?? "bottom",
    pos_terminal_id: configuration.pos_terminal_id ?? "",
    platform: configuration.platform ?? "",
    screen_id: configuration.screen_id ?? "",
  };
}

// output_type isn't included — it's immutable after creation, so update
// payloads never send it (see backend OutputChannelUpdate).
function toApiPayload(values, { isCreate }) {
  const configuration = {};
  if (values.output_type === "esl_simulator") {
    if (values.label_size) configuration.label_size = values.label_size;
    if (values.orientation) configuration.orientation = values.orientation;
    if (values.theme) configuration.theme = values.theme;
  } else if (values.output_type === "qr_code") {
    if (values.box_size) configuration.box_size = Number(values.box_size);
    if (values.border) configuration.border = Number(values.border);
    if (values.error_correction) configuration.error_correction = values.error_correction;
  } else if (values.output_type === "pdf_label") {
    if (values.label_width_mm) configuration.label_width_mm = Number(values.label_width_mm);
    if (values.label_height_mm) configuration.label_height_mm = Number(values.label_height_mm);
    if (values.qr_size_mm) configuration.qr_size_mm = Number(values.qr_size_mm);
    if (values.qr_position) configuration.qr_position = values.qr_position;
    if (values.banner_position) configuration.banner_position = values.banner_position;
    configuration.show_qr = values.show_qr;
    configuration.show_unit_price = values.show_unit_price;
  } else if (values.output_type === "web_display") {
    if (values.theme) configuration.theme = values.theme;
  } else if (values.output_type === "pos_integration") {
    if (values.pos_terminal_id) configuration.pos_terminal_id = values.pos_terminal_id;
  } else if (values.output_type === "ecommerce_integration") {
    if (values.platform) configuration.platform = values.platform;
  } else if (values.output_type === "digital_signage") {
    if (values.screen_id) configuration.screen_id = values.screen_id;
    if (values.theme) configuration.theme = values.theme;
  }

  const payload = {
    name: values.name,
    store_id: values.store_id || null,
    status: values.status,
    configuration,
  };
  // label_template_id is a top-level FK on the channel, not inside configuration.
  // Always include it (as the id, or null) for pdf_label so the backend's
  // exclude_unset update actually applies a cleared selection — omitting the
  // key here previously left a removed template silently still assigned when
  // editing an existing channel.
  if (values.output_type === "pdf_label") {
    payload.label_template_id = values.label_template_id || null;
  } else if (isCreate) {
    // Non-pdf_label channels never have a template; only relevant on create,
    // since output_type itself isn't editable afterwards.
    payload.label_template_id = null;
  }
  if (isCreate) payload.output_type = values.output_type;
  return payload;
}

// Most backend error messages in this app (AppError subclasses) are
// already written for a human reader. FastAPI's own request-validation
// errors aren't — they're raw Pydantic parser text (e.g. "Input should be
// a valid UUID, invalid character: ..."). Recognize the couple of shapes
// that can reach this form and rephrase them; anything else passes through.
function humanizeApiError({ message } = {}) {
  if (message && /valid uuid/i.test(message)) {
    return "This isn't a valid selection — please choose an option from the list.";
  }
  return message || "This value isn't valid.";
}

export default function ChannelForm({ defaultValues, onSubmit, submitLabel, isCreate = false }) {
  const [formError, setFormError] = useState(null);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const deleteMutation = useDeleteLabelTemplate();

  const {
    control,
    handleSubmit,
    watch,
    setValue,
    setError,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(outputChannelSchema),
    defaultValues: { ...EMPTY_VALUES, ...defaultValues },
  });

  const outputType = watch("output_type");
  const labelTemplateId = watch("label_template_id");

  const submit = async (values) => {
    setFormError(null);
    try {
      await onSubmit(toApiPayload(values, { isCreate }));
    } catch (error) {
      const apiError = error.response?.data?.error;
      // The backend names which field it choked on (e.g. "body.label_template_id")
      // for both its own validation errors and FastAPI's raw Pydantic ones. When
      // that maps to a field on this form, highlight that field instead of just
      // dumping a message at the top — and translate the handful of raw,
      // developer-facing Pydantic messages we know how to explain in plain terms.
      const fieldName = apiError?.field?.replace(/^body\./, "");
      if (fieldName && fieldName in EMPTY_VALUES) {
        setError(fieldName, { type: "server", message: humanizeApiError(apiError) });
      } else {
        setFormError(apiError?.message ?? "Unable to save this output. Please try again.");
      }
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit(submit)} noValidate>
      <Stack spacing={3}>
        {formError && <Alert severity="error">{formError}</Alert>}

        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <Controller
              name="name"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Output Name"
                  required
                  fullWidth
                  error={!!errors.name}
                  helperText={errors.name?.message}
                />
              )}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <Controller
              name="output_type"
              control={control}
              render={({ field }) => (
                <TextField {...field} select label="Output Type" required fullWidth disabled={!isCreate}>
                  {OUTPUT_TYPE_OPTIONS.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </TextField>
              )}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <Controller
              name="store_id"
              control={control}
              render={({ field }) => (
                <StoreSelect value={field.value} onChange={field.onChange} label="Store (optional)" />
              )}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <Controller
              name="status"
              control={control}
              render={({ field }) => (
                <TextField {...field} select label="Status" required fullWidth>
                  {OUTPUT_CHANNEL_STATUS_OPTIONS.map((status) => (
                    <MenuItem key={status} value={status}>
                      {status}
                    </MenuItem>
                  ))}
                </TextField>
              )}
            />
          </Grid>
        </Grid>

        <section>
          <Typography variant="subtitle1" gutterBottom>
            Configuration
          </Typography>
          <Grid container spacing={2}>
            {outputType === "esl_simulator" && (
              <>
                <Grid item xs={12} sm={4}>
                  <Controller
                    name="label_size"
                    control={control}
                    render={({ field }) => <TextField {...field} label="Label Size" fullWidth placeholder="2.9in" />}
                  />
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Controller
                    name="orientation"
                    control={control}
                    render={({ field }) => (
                      <TextField {...field} select label="Orientation" fullWidth>
                        <MenuItem value="">Default</MenuItem>
                        {ORIENTATION_OPTIONS.map((option) => (
                          <MenuItem key={option} value={option}>
                            {option}
                          </MenuItem>
                        ))}
                      </TextField>
                    )}
                  />
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Controller
                    name="theme"
                    control={control}
                    render={({ field }) => (
                      <TextField {...field} select label="Theme" fullWidth>
                        <MenuItem value="">Default</MenuItem>
                        {THEME_OPTIONS.map((option) => (
                          <MenuItem key={option} value={option}>
                            {option}
                          </MenuItem>
                        ))}
                      </TextField>
                    )}
                  />
                </Grid>
              </>
            )}

            {outputType === "qr_code" && (
              <>
                <Grid item xs={12} sm={4}>
                  <Controller
                    name="box_size"
                    control={control}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        label="Box Size"
                        fullWidth
                        error={!!errors.box_size}
                        helperText={errors.box_size?.message}
                      />
                    )}
                  />
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Controller
                    name="border"
                    control={control}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        label="Border"
                        fullWidth
                        error={!!errors.border}
                        helperText={errors.border?.message}
                      />
                    )}
                  />
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Controller
                    name="error_correction"
                    control={control}
                    render={({ field }) => (
                      <TextField {...field} select label="Error Correction" fullWidth>
                        <MenuItem value="">Default (M)</MenuItem>
                        {ERROR_CORRECTION_OPTIONS.map((option) => (
                          <MenuItem key={option} value={option}>
                            {option}
                          </MenuItem>
                        ))}
                      </TextField>
                    )}
                  />
                </Grid>
              </>
            )}

            {outputType === "pdf_label" && (
              <>
                {/* ── Label template selector + inline editor ───── */}
                <Grid item xs={12}>
                  <Controller
                    name="label_template_id"
                    control={control}
                    render={({ field }) => (
                      <LabelTemplateSelect
                        value={field.value}
                        onChange={field.onChange}
                        onEdit={(tpl) => setEditingTemplate(tpl)}
                        onDelete={(tpl) => setDeleteTarget(tpl)}
                        error={!!errors.label_template_id}
                        helperText={errors.label_template_id?.message}
                      />
                    )}
                  />
                </Grid>
                {labelTemplateId === CREATE_NEW && (
                  <Grid item xs={12}>
                    <LabelTemplateEditor
                      template={null}
                      onSaved={(saved) => {
                        setValue("label_template_id", saved.id, { shouldValidate: true });
                      }}
                      onCancel={() => setValue("label_template_id", null, { shouldValidate: true })}
                    />
                  </Grid>
                )}
                {editingTemplate && (
                  <Grid item xs={12}>
                    <LabelTemplateEditor
                      template={editingTemplate}
                      onSaved={() => {
                        setEditingTemplate(null);
                        // keep the same selection — the dropdown re-fetches via cache invalidation
                      }}
                      onCancel={() => setEditingTemplate(null)}
                    />
                  </Grid>
                )}

                <Grid item xs={12} sm={6}>
                  <Controller
                    name="show_qr"
                    control={control}
                    render={({ field }) => (
                      <FormControlLabel
                        control={<Switch {...field} checked={field.value} />}
                        label="Show QR code"
                      />
                    )}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Controller
                    name="show_unit_price"
                    control={control}
                    render={({ field }) => (
                      <FormControlLabel
                        control={<Switch {...field} checked={field.value} />}
                        label="Show unit price"
                      />
                    )}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Controller
                    name="qr_position"
                    control={control}
                    render={({ field }) => (
                      <TextField {...field} select label="QR Position" fullWidth>
                        {QR_POSITION_OPTIONS.map((option) => (
                          <MenuItem key={option.value} value={option.value}>
                            {option.label}
                          </MenuItem>
                        ))}
                      </TextField>
                    )}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Controller
                    name="banner_position"
                    control={control}
                    render={({ field }) => (
                      <TextField {...field} select label="Store Banner Position" fullWidth>
                        {BANNER_POSITION_OPTIONS.map((option) => (
                          <MenuItem key={option.value} value={option.value}>
                            {option.label}
                          </MenuItem>
                        ))}
                      </TextField>
                    )}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Controller
                    name="label_width_mm"
                    control={control}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        label="Label Width (mm)"
                        fullWidth
                        error={!!errors.label_width_mm}
                        helperText={errors.label_width_mm?.message}
                      />
                    )}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Controller
                    name="label_height_mm"
                    control={control}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        label="Label Height (mm)"
                        fullWidth
                        error={!!errors.label_height_mm}
                        helperText={errors.label_height_mm?.message}
                      />
                    )}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Controller
                    name="qr_size_mm"
                    control={control}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        label="QR Size (mm)"
                        fullWidth
                        error={!!errors.qr_size_mm}
                        helperText={errors.qr_size_mm?.message}
                      />
                    )}
                  />
                </Grid>
              </>
            )}

            {outputType === "web_display" && (
              <Grid item xs={12} sm={4}>
                <Controller
                  name="theme"
                  control={control}
                  render={({ field }) => (
                    <TextField {...field} select label="Theme" fullWidth>
                      <MenuItem value="">Default</MenuItem>
                      {THEME_OPTIONS.map((option) => (
                        <MenuItem key={option} value={option}>
                          {option}
                        </MenuItem>
                      ))}
                    </TextField>
                  )}
                />
              </Grid>
            )}

            {outputType === "pos_integration" && (
              <Grid item xs={12} sm={4}>
                <Controller
                  name="pos_terminal_id"
                  control={control}
                  render={({ field }) => <TextField {...field} label="POS Terminal ID" fullWidth />}
                />
              </Grid>
            )}

            {outputType === "ecommerce_integration" && (
              <Grid item xs={12} sm={4}>
                <Controller
                  name="platform"
                  control={control}
                  render={({ field }) => (
                    <TextField {...field} label="Platform" fullWidth placeholder="shopify" />
                  )}
                />
              </Grid>
            )}

            {outputType === "digital_signage" && (
              <>
                <Grid item xs={12} sm={4}>
                  <Controller
                    name="screen_id"
                    control={control}
                    render={({ field }) => <TextField {...field} label="Screen ID" fullWidth />}
                  />
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Controller
                    name="theme"
                    control={control}
                    render={({ field }) => (
                      <TextField {...field} select label="Theme" fullWidth>
                        <MenuItem value="">Default</MenuItem>
                        {THEME_OPTIONS.map((option) => (
                          <MenuItem key={option} value={option}>
                            {option}
                          </MenuItem>
                        ))}
                      </TextField>
                    )}
                  />
                </Grid>
              </>
            )}
          </Grid>
        </section>

        <Box>
          <Button type="submit" variant="contained" size="large" disabled={isSubmitting}>
            {submitLabel}
          </Button>
        </Box>
      </Stack>

      {/* Delete template confirmation */}
      <Dialog open={Boolean(deleteTarget)} onClose={() => setDeleteTarget(null)}>
        <DialogTitle>Delete Template</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete &ldquo;{deleteTarget?.name}&rdquo;?
            Channels using it will fall back to default colors.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteTarget(null)}>Cancel</Button>
          <Button
            color="error"
            variant="contained"
            disabled={deleteMutation.isPending}
            onClick={async () => {
              await deleteMutation.mutateAsync(deleteTarget.id);
              // If this template was selected, clear the selection
              if (labelTemplateId === deleteTarget.id) {
                setValue("label_template_id", null, { shouldValidate: true });
              }
              setDeleteTarget(null);
            }}
          >
            {deleteMutation.isPending ? "Deleting…" : "Delete"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
