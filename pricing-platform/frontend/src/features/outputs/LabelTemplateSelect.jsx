import Box from "@mui/material/Box";
import IconButton from "@mui/material/IconButton";
import MenuItem from "@mui/material/MenuItem";
import TextField from "@mui/material/TextField";
import Tooltip from "@mui/material/Tooltip";
import EditIcon from "@mui/icons-material/Edit";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";

import { useLabelTemplates } from "./hooks";

// Sentinel value: when the user picks this, the LabelTemplateEditor shows
// to let them create a brand-new template inline.
export const CREATE_NEW = "__create_new__";

/**
 * Dropdown of the org's label templates + "None (defaults)" +
 * "Create new template…".  Designed to work inside a react-hook-form
 * `<Controller>` — the parent passes `value` and `onChange`.
 *
 * Props:
 *   value (string|null)   — selected template ID or sentinel
 *   onChange (fn)         — called with new value
 *   onEdit (fn)           — called with the full template object when Edit is clicked
 *   onDelete (fn)         — called with the full template object when Delete is clicked
 *   error (bool)          — shows the field in an error state
 *   helperText (string)   — validation/error message shown under the field
 */
export default function LabelTemplateSelect({ value, onChange, onEdit, onDelete, error, helperText }) {
  const { data: templates } = useLabelTemplates();

  const selectedTemplate =
    value && value !== CREATE_NEW
      ? (templates ?? []).find((t) => t.id === value)
      : null;

  return (
    <Box sx={{ display: "flex", alignItems: "flex-start", gap: 0.5 }}>
      <TextField
        select
        fullWidth
        label="Label Template"
        value={value ?? ""}
        error={error}
        helperText={helperText}
        onChange={(e) => {
          const v = e.target.value;
          onChange(v === "" ? null : v === CREATE_NEW ? CREATE_NEW : v);
        }}
      >
        <MenuItem value="">
          <em>None (default black &amp; white)</em>
        </MenuItem>
        {(templates ?? []).map((t) => (
          <MenuItem key={t.id} value={t.id}>
            {t.name}
          </MenuItem>
        ))}
        <MenuItem value={CREATE_NEW}>
          <em>+ Create new template…</em>
        </MenuItem>
      </TextField>
      {selectedTemplate && onEdit && (
        <Tooltip title="Edit template">
          <IconButton size="small" sx={{ mt: 0.5 }} onClick={() => onEdit(selectedTemplate)}>
            <EditIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      )}
      {selectedTemplate && onDelete && (
        <Tooltip title="Delete template">
          <IconButton size="small" sx={{ mt: 0.5 }} color="error" onClick={() => onDelete(selectedTemplate)}>
            <DeleteOutlineIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      )}
    </Box>
  );
}
