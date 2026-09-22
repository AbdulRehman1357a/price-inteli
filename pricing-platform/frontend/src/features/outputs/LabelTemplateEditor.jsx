import { useEffect, useRef, useState } from "react";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import Grid from "@mui/material/Grid";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import LabelPreview from "./LabelPreview";

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
 * A simple SVG-based live preview of the PDF shelf label, driven by the
 * template's colors. It mirrors the backend's three-column layout (text /
 * unit-price box / QR zone) and the banner, so the user can see exactly how
 * their color choices affect the rendered label — no PDF generation needed
 * for this preview, so it's instant and works on mobile.
 *
 * This is a *mockup preview only* (same fidelity as ESLSimulatorPreview):
 * the real PDF is generated server-side. The goal is to show color impact
 * in real time, not pixel-perfect parity with the reportlab renderer.
 */
function LabelPreview({ colors }) {
  const labelW = 240;
  const labelH = 150;
  const pad = 4;
  const bannerH = 14;
  const unitBoxW = 48;

  const textColW = labelW - pad * 2 - unitBoxW - 14;

  const bannerColor = colors.banner ?? DEFAULT_COLORS.banner;
  const textColor = colors.text ?? DEFAULT_COLORS.text;
  const borderColor = colors.border ?? DEFAULT_COLORS.border;
  const unitBorderColor = colors.unit_border ?? DEFAULT_COLORS.unit_border;
  const sublabelColor = colors.sublabel ?? DEFAULT_COLORS.sublabel;
  const placeholderColor = colors.placeholder ?? DEFAULT_COLORS.placeholder;
  const bgColor = colors.background ?? DEFAULT_COLORS.background;

  // Simple placeholder text for price display
  const priceText = "$49.99";
  const productName = "Wireless Mouse";
  const unitPriceText = "$4.99";

  return (
    <Box
      sx={{
        width: "100%",
        maxWidth: 260,
        aspectRatio: `${labelW}/${labelH}`,
        border: "1px solid #ccc",
        borderRadius: 1,
        overflow: "hidden",
        bgcolor: bgColor,
      }}
    >
      <svg
        width={labelW}
        height={labelH}
        viewBox={`0 0 ${labelW} ${labelH}`}
        xmlns="http://www.w3.org/2000/svg"
        style={{ width: "100%", height: "100%" }}
      >
        {/* Background */}
        <rect x={0} y={0} width={labelW} height={labelH} fill={bgColor} />

        {/* Outer border */}
        <rect
          x={pad}
          y={pad}
          width={labelW - pad * 2}
          height={labelH - pad * 2}
          rx={2}
          ry={2}
          fill="none"
          stroke={borderColor}
          strokeWidth={2}
        />

        {/* Bottom banner */}
        <rect
          x={pad}
          y={labelH - pad - bannerH}
          width={labelW - pad * 2}
          height={bannerH}
          fill={bannerColor}
        />
        <text
          x={labelW / 2}
          y={labelH - pad - bannerH / 2 + 4}
          textAnchor="middle"
          fill="#FFFFFF"
          fontSize={11}
          fontWeight="bold"
          fontFamily="Helvetica, Arial, sans-serif"
        >
          Store Name
        </text>

        {/* Unit price box (center column) */}
        <g transform={`translate(${labelW - pad - unitBoxW}, ${pad + 10})`}>
          <rect
            x={0}
            y={0}
            width={unitBoxW}
            height={50}
            rx={3}
            ry={3}
            fill="none"
            stroke={unitBorderColor}
            strokeWidth={1}
          />
          <text
            x={unitBoxW / 2}
            y={13}
            textAnchor="middle"
            fill={textColor}
            fontSize={7}
            fontWeight="bold"
            fontFamily="Helvetica, Arial, sans-serif"
          >
            UNIT PRICE
          </text>
          <text
            x={unitBoxW / 2}
            y={32}
            textAnchor="middle"
            fill={textColor}
            fontSize={12}
            fontWeight="bold"
            fontFamily="Helvetica, Arial, sans-serif"
          >
            {unitPriceText}
          </text>
          <text
            x={unitBoxW / 2}
            y={44}
            textAnchor="middle"
            fill={sublabelColor}
            fontSize={6}
            fontFamily="Helvetica, Arial, sans-serif"
          >
            PER EA
          </text>
        </g>

        {/* Text zone */}
        <g transform={`translate(${pad + 6}, ${pad + 6})`}>
          {/* Product name */}
          <text
            x={0}
            y={0}
            fill={productName ? textColor : placeholderColor}
            fontSize={10}
            fontWeight="bold"
            fontFamily="Helvetica, Arial, sans-serif"
          >
            {productName || "Product Name"}
          </text>
          {/* RETAIL PRICE sublabel */}
          <text
            x={0}
            y={15}
            fill={sublabelColor}
            fontSize={6.5}
            fontFamily="Helvetica, Arial, sans-serif"
          >
            RETAIL PRICE
          </text>
          {/* Big price */}
          <text
            x={0}
            y={30}
            fill={textColor}
            fontSize={20}
            fontWeight="bold"
            fontFamily="Helvetica, Arial, sans-serif"
          >
            {priceText}
          </text>
          {/* SKU */}
          <text
            x={0}
            y={42}
            fill={placeholderColor}
            fontSize={6}
            fontFamily="Helvetica, Arial, sans-serif"
          >
            SKU-000
          </text>
        </g>

        {/* QR zone placeholder (dashed outline) */}
        <g
          transform={`translate(${labelW - pad - unitBoxW - 14}, ${pad + 10})`}
        >
          <rect
            x={0}
            y={0}
            width={40}
            height={50}
            fill="none"
            stroke={placeholderColor}
            strokeWidth={1}
            strokeDasharray="3,2"
          />
          <text
            x={20}
            y={48}
            textAnchor="middle"
            fill={placeholderColor}
            fontSize={5}
            fontFamily="Helvetica, Arial, sans-serif"
          >
            QR
          </text>
        </g>
      </svg>
    </Box>
  );
}

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

      {/* Live color preview */}
      <Box sx={{ display: "flex", justifyContent: "center" }}>
        <LabelPreview colors={colors} />
      </Box>

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
