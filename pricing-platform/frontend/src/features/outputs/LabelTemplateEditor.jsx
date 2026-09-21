import { useEffect, useRef, useState } from "react";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import Grid from "@mui/material/Grid";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";

import {
  useCreateLabelTemplate,
  useUpdateLabelTemplate,
  useUploadTemplateBackgroundImage,
} from "./hooks";

const COLOR_KEYS = [
  { key: "background", label: "Background" },
  { key: "border", label: "Border" },
  { key: "text", label: "Text" },
  { key: "banner", label: "Banner" },
  { key: "unit_border", label: "Unit Box Border" },
  { key: "sublabel", label: "Sublabel" },
  { key: "placeholder", label: "Placeholder" },
];

const DEFAULT_COLORS = {
  background: "#FFFFFF",
  border: "#111111",
  text: "#111111",
  banner: "#111111",
  unit_border: "#111111",
  sublabel: "#666666",
  placeholder: "#AAAAAA",
};

/**
 * Inline editor for a LabelTemplate: name, 7 color pickers (native
 * `<input type="color">` + hex TextField), and a background image upload
 * with thumbnail. Used inside ChannelForm's pdf_label section to create
 * or edit the selected template.
 *
 * Props:
 *   template (object|null) — existing template data to pre-fill; null = new
 *   onSaved (template)     — called after create/update succeeds with the
 *                            saved template object (has id, name, colors, etc.)
 *   onCancel ()            — called when user clicks Cancel
 */
export default function LabelTemplateEditor({ template, onSaved, onCancel }) {
  const [name, setName] = useState(template?.name ?? "");
  const [colors, setColors] = useState(template?.colors ?? { ...DEFAULT_COLORS });
  const [backgroundFile, setBackgroundFile] = useState(null);
  const [backgroundPreview, setBackgroundPreview] = useState(
    template?.background_image_url ?? null,
  );
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const createMutation = useCreateLabelTemplate();
  const updateMutation = useUpdateLabelTemplate();
  const uploadImage = useUploadTemplateBackgroundImage();

  const saving = createMutation.isPending || updateMutation.isPending || uploadImage.isPending;

  const setHex = (key, value) => {
    setColors((prev) => ({ ...prev, [key]: value }));
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0] ?? null;
    setBackgroundFile(file);
    if (file) {
      setBackgroundPreview(URL.createObjectURL(file));
    } else {
      setBackgroundPreview(template?.background_image_url ?? null);
    }
  };

  const handleSave = async () => {
    setError(null);
    try {
      let saved;
      if (template?.id) {
        saved = await updateMutation.mutateAsync({
          id: template.id,
          name,
          colors,
        });
      } else {
        saved = await createMutation.mutateAsync({ name, colors });
      }
      if (backgroundFile) {
        saved = await uploadImage.mutateAsync({
          templateId: saved.id,
          file: backgroundFile,
        });
      }
      onSaved(saved);
    } catch (err) {
      setError(
        err.response?.data?.error?.message ?? "Failed to save template. Please try again.",
      );
    }
  };

  return (
    <Stack spacing={2} sx={{ mt: 1, p: 2, border: "1px solid #e0e0e0", borderRadius: 1 }}>
      <Typography variant="subtitle2">Label Template</Typography>
      {error && <Alert severity="error" sx={{ mb: 1 }}>{error}</Alert>}

      <TextField
        label="Template Name"
        value={name}
        onChange={(e) => setName(e.target.value)}
        fullWidth
        required
        size="small"
      />

      <Grid container spacing={1}>
        {COLOR_KEYS.map(({ key, label }) => (
          <Grid item xs={6} sm={4} md={3} key={key}>
            <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
              <input
                type="color"
                value={colors[key] ?? "#000000"}
                onChange={(e) => setHex(key, e.target.value)}
                style={{ width: 32, height: 32, padding: 0, border: "none", cursor: "pointer" }}
              />
              <TextField
                size="small"
                label={label}
                value={colors[key] ?? ""}
                onChange={(e) => setHex(key, e.target.value)}
                inputProps={{ maxLength: 7, style: { fontFamily: "monospace", fontSize: 12 } }}
                sx={{ flex: 1 }}
              />
            </Box>
          </Grid>
        ))}
      </Grid>

      {/* Background image */}
      <Box>
        <Typography variant="caption" color="text.secondary">
          Background Image (optional)
        </Typography>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/png,image/jpeg,image/gif,image/webp"
          onChange={handleFileChange}
          style={{ display: "none" }}
        />
        <Box sx={{ display: "flex", alignItems: "center", gap: 1, mt: 0.5 }}>
          <Button variant="outlined" size="small" onClick={() => fileInputRef.current?.click()}>
            {backgroundPreview ? "Change image" : "Upload image"}
          </Button>
          {backgroundPreview && (
            <Box
              component="img"
              src={backgroundPreview}
              alt="Background preview"
              sx={{ width: 48, height: 48, objectFit: "cover", borderRadius: 1, border: "1px solid #ccc" }}
            />
          )}
          {backgroundFile && (
            <Button size="small" color="warning" onClick={() => { setBackgroundFile(null); setBackgroundPreview(null); }}>
              Remove
            </Button>
          )}
        </Box>
      </Box>

      <Stack direction="row" spacing={1}>
        <Button variant="contained" size="small" onClick={handleSave} disabled={saving || !name.trim()}>
          {saving ? <CircularProgress size={16} /> : template?.id ? "Save changes" : "Create template"}
        </Button>
        <Button variant="outlined" size="small" onClick={onCancel} disabled={saving}>
          Cancel
        </Button>
      </Stack>
    </Stack>
  );
}
